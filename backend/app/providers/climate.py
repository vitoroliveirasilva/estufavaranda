from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_CLIMATE_TIMEOUT_SECONDS = 15

_CURRENT_WEATHER_FIELDS = ",".join(
    (
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "showers",
        "uv_index",
    )
)

_MINUTELY_15_WEATHER_FIELDS = ",".join(
    (
        "precipitation",
        "rain",
    )
)

_HOURLY_WEATHER_FIELDS = ",".join(
    (
        "precipitation",
        "rain",
        "showers",
    )
)

_DAILY_WEATHER_FIELDS = ",".join(
    (
        "precipitation_sum",
        "rain_sum",
        "showers_sum",
    )
)


@dataclass(slots=True)
class ClimateData:
    city_name: str
    temperature_c: float | None
    humidity_percent: int | None
    rain_mm: float | None
    feels_like_c: float | None
    uv_index: float | None
    raw_payload: dict[str, Any]


class OpenMeteoClimateProvider:
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, session: Session | None = None) -> None:
        self._session = session or self._build_session()

    def fetch_by_city(self, city_name: str) -> ClimateData:
        normalized_city_name = self._normalize_city_name(city_name)
        settings = get_settings()
        timeout = self._get_timeout_seconds(settings)

        place = self._fetch_place(normalized_city_name, timeout)
        payload = self._fetch_weather(place, timeout)

        current = payload.get("current") if isinstance(payload, dict) else {}
        if not isinstance(current, dict):
            current = {}

        resolved_city_name = (
            str(place.get("name") or normalized_city_name).strip()
            or normalized_city_name
        )

        return ClimateData(
            city_name=resolved_city_name,
            temperature_c=self._to_float(current.get("temperature_2m")),
            humidity_percent=self._to_int(current.get("relative_humidity_2m")),
            rain_mm=self._resolve_rain_mm(payload, current),
            feels_like_c=self._to_float(current.get("apparent_temperature")),
            uv_index=self._to_float(current.get("uv_index")),
            raw_payload=payload if isinstance(payload, dict) else {},
        )

    def _fetch_place(self, city_name: str, timeout: float) -> dict[str, Any]:
        try:
            response = self._session.get(
                self.GEOCODE_URL,
                params={
                    "name": city_name,
                    "count": 1,
                    "language": "pt",
                    "format": "json",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            self._raise_for_status("geocode", response)
            payload = response.json()
        except requests.Timeout as exc:
            logger.warning(
                "provider.climate.geocode_timeout",
                extra={"city_name": city_name, "timeout_seconds": timeout},
                exc_info=exc,
            )
            raise RuntimeError("Tempo esgotado ao consultar o provider de clima.") from exc
        except requests.RequestException as exc:
            logger.exception(
                "provider.climate.geocode_request_failed",
                extra={"city_name": city_name},
            )
            raise RuntimeError("Falha ao consultar o provider de clima.") from exc
        except ValueError as exc:
            logger.exception(
                "provider.climate.geocode_invalid_json",
                extra={"city_name": city_name},
            )
            raise RuntimeError("Provider de clima retornou JSON inválido.") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Provider de clima retornou payload inválido.")

        results = payload.get("results") or []
        if not isinstance(results, list) or not results:
            raise ValueError(f"Cidade não encontrada: {city_name}")

        place = results[0]
        if not isinstance(place, dict):
            raise RuntimeError("Provider de clima retornou localidade inválida.")

        latitude = self._to_float(place.get("latitude"))
        longitude = self._to_float(place.get("longitude"))
        if latitude is None or longitude is None:
            raise RuntimeError("Provider de clima retornou coordenadas inválidas.")

        place["latitude"] = latitude
        place["longitude"] = longitude
        return place

    def _fetch_weather(self, place: dict[str, Any], timeout: float) -> dict[str, Any]:
        try:
            response = self._session.get(
                self.WEATHER_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": _CURRENT_WEATHER_FIELDS,
                    "minutely_15": _MINUTELY_15_WEATHER_FIELDS,
                    "hourly": _HOURLY_WEATHER_FIELDS,
                    "daily": _DAILY_WEATHER_FIELDS,
                    "timezone": "auto",
                    "precipitation_unit": "mm",
                    "past_hours": 24,
                    "forecast_hours": 6,
                    "past_minutely_15": 8,
                    "forecast_minutely_15": 8,
                },
                timeout=timeout,
                allow_redirects=False,
            )
            self._raise_for_status("weather", response)
            payload = response.json()
        except requests.Timeout as exc:
            logger.warning(
                "provider.climate.weather_timeout",
                extra={
                    "city_name": place.get("name"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "timeout_seconds": timeout,
                },
                exc_info=exc,
            )
            raise RuntimeError("Tempo esgotado ao consultar o provider de clima.") from exc
        except requests.RequestException as exc:
            logger.exception(
                "provider.climate.weather_request_failed",
                extra={
                    "city_name": place.get("name"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                },
            )
            raise RuntimeError("Falha ao consultar o provider de clima.") from exc
        except ValueError as exc:
            logger.exception(
                "provider.climate.weather_invalid_json",
                extra={
                    "city_name": place.get("name"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                },
            )
            raise RuntimeError("Provider de clima retornou JSON inválido.") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Provider de clima retornou payload inválido.")

        return payload

    @classmethod
    def _resolve_rain_mm(
        cls,
        payload: dict[str, Any],
        current: dict[str, Any],
    ) -> float | None:
        current_time = cls._parse_datetime(current.get("time"))

        current_value = cls._precipitation_from_mapping(current)
        if cls._is_positive(current_value):
            return current_value

        if current_time is not None:
            minutely_value = cls._nearest_precipitation_value(
                payload=payload,
                block_name="minutely_15",
                target_time=current_time,
                max_delta_minutes=45,
            )
            if cls._is_positive(minutely_value):
                return minutely_value

            hourly_value = cls._nearest_precipitation_value(
                payload=payload,
                block_name="hourly",
                target_time=current_time,
                max_delta_minutes=90,
            )
            if cls._is_positive(hourly_value):
                return hourly_value

            today_value = cls._today_accumulated_precipitation(
                payload=payload,
                target_time=current_time,
            )
            if cls._is_positive(today_value):
                return today_value

            daily_value = cls._daily_precipitation_value(
                payload=payload,
                target_time=current_time,
            )
            if cls._is_positive(daily_value):
                return daily_value

        return current_value if current_value is not None else 0.0

    @classmethod
    def _precipitation_from_mapping(cls, data: dict[str, Any]) -> float | None:
        rain = cls._to_float(data.get("rain"))
        showers = cls._to_float(data.get("showers"))
        precipitation = cls._to_float(data.get("precipitation"))

        if rain is not None or showers is not None:
            return cls._round_mm((rain or 0.0) + (showers or 0.0))

        return cls._round_mm(precipitation)

    @classmethod
    def _nearest_precipitation_value(
        cls,
        *,
        payload: dict[str, Any],
        block_name: str,
        target_time: datetime,
        max_delta_minutes: int,
    ) -> float | None:
        block = payload.get(block_name)
        if not isinstance(block, dict):
            return None

        times = block.get("time")
        if not isinstance(times, list) or not times:
            return None

        nearest_index: int | None = None
        nearest_delta_seconds: float | None = None

        for index, raw_time in enumerate(times):
            parsed_time = cls._parse_datetime(raw_time)
            if parsed_time is None:
                continue

            delta_seconds = abs((parsed_time - target_time).total_seconds())
            if nearest_delta_seconds is None or delta_seconds < nearest_delta_seconds:
                nearest_delta_seconds = delta_seconds
                nearest_index = index

        if nearest_index is None or nearest_delta_seconds is None:
            return None

        if nearest_delta_seconds > max_delta_minutes * 60:
            return None

        return cls._precipitation_from_series(block, nearest_index)

    @classmethod
    def _today_accumulated_precipitation(
        cls,
        *,
        payload: dict[str, Any],
        target_time: datetime,
    ) -> float | None:
        hourly = payload.get("hourly")
        if not isinstance(hourly, dict):
            return None

        times = hourly.get("time")
        if not isinstance(times, list) or not times:
            return None

        total = 0.0
        found_value = False

        for index, raw_time in enumerate(times):
            parsed_time = cls._parse_datetime(raw_time)
            if parsed_time is None:
                continue

            if parsed_time.date() != target_time.date():
                continue

            if parsed_time > target_time:
                continue

            value = cls._precipitation_from_series(hourly, index)
            if value is None:
                continue

            total += value
            found_value = True

        if not found_value:
            return None

        return cls._round_mm(total)

    @classmethod
    def _daily_precipitation_value(
        cls,
        *,
        payload: dict[str, Any],
        target_time: datetime,
    ) -> float | None:
        daily = payload.get("daily")
        if not isinstance(daily, dict):
            return None

        times = daily.get("time")
        if not isinstance(times, list):
            return None

        target_date = target_time.date().isoformat()

        try:
            index = times.index(target_date)
        except ValueError:
            return None

        rain = cls._series_float(daily, "rain_sum", index)
        showers = cls._series_float(daily, "showers_sum", index)
        precipitation = cls._series_float(daily, "precipitation_sum", index)

        if rain is not None or showers is not None:
            return cls._round_mm((rain or 0.0) + (showers or 0.0))

        return cls._round_mm(precipitation)

    @classmethod
    def _precipitation_from_series(
        cls,
        block: dict[str, Any],
        index: int,
    ) -> float | None:
        rain = cls._series_float(block, "rain", index)
        showers = cls._series_float(block, "showers", index)
        precipitation = cls._series_float(block, "precipitation", index)

        if rain is not None or showers is not None:
            return cls._round_mm((rain or 0.0) + (showers or 0.0))

        return cls._round_mm(precipitation)

    @classmethod
    def _series_float(
        cls,
        block: dict[str, Any],
        key: str,
        index: int,
    ) -> float | None:
        values = block.get(key)
        if not isinstance(values, list):
            return None

        if index < 0 or index >= len(values):
            return None

        return cls._to_float(values[index])

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        normalized = str(value).strip()
        if not normalized:
            return None

        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except ValueError:
            return None

    @staticmethod
    def _round_mm(value: float | None) -> float | None:
        if value is None:
            return None
        return round(value, 3)

    @staticmethod
    def _is_positive(value: float | None) -> bool:
        return value is not None and value > 0

    @staticmethod
    def _build_session() -> Session:
        session = requests.Session()
        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _normalize_city_name(city_name: str) -> str:
        normalized = str(city_name or "").strip()
        if not normalized:
            raise ValueError("Cidade inválida para consulta climática.")
        return normalized

    @staticmethod
    def _get_timeout_seconds(settings: Any) -> float:
        raw_timeout = getattr(
            settings,
            "climate_request_timeout_seconds",
            _DEFAULT_CLIMATE_TIMEOUT_SECONDS,
        )
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError):
            return float(_DEFAULT_CLIMATE_TIMEOUT_SECONDS)
        return timeout if timeout > 0 else float(_DEFAULT_CLIMATE_TIMEOUT_SECONDS)

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _raise_for_status(stage: str, response: Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.warning(
                f"provider.climate.{stage}_http_error",
                extra={
                    "status_code": response.status_code,
                    "response_preview": response.text[:500],
                },
            )
            raise exc


_OPEN_METEO_PROVIDER: OpenMeteoClimateProvider | None = None


def get_climate_provider() -> OpenMeteoClimateProvider:
    global _OPEN_METEO_PROVIDER

    settings = get_settings()
    provider = str(getattr(settings, "climate_provider", "") or "").strip().lower()
    if provider != "open_meteo":
        raise ValueError(f"Provider de clima não suportado: {provider}")

    if _OPEN_METEO_PROVIDER is None:
        _OPEN_METEO_PROVIDER = OpenMeteoClimateProvider()

    return _OPEN_METEO_PROVIDER
