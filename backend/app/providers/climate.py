from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_CLIMATE_TIMEOUT_SECONDS = 15


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

        resolved_city_name = str(place.get("name") or normalized_city_name).strip() or normalized_city_name

        return ClimateData(
            city_name=resolved_city_name,
            temperature_c=self._to_float(current.get("temperature_2m")),
            humidity_percent=self._to_int(current.get("relative_humidity_2m")),
            rain_mm=self._to_float(current.get("precipitation")),
            feels_like_c=self._to_float(current.get("apparent_temperature")),
            uv_index=self._to_float(current.get("uv_index")),
            raw_payload=payload if isinstance(payload, dict) else {},
        )

    def _fetch_place(self, city_name: str, timeout: float) -> dict[str, Any]:
        try:
            response = self._session.get(
                self.GEOCODE_URL,
                params={"name": city_name, "count": 1, "language": "pt", "format": "json"},
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
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,uv_index",
                    "timezone": "auto",
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
        raw_timeout = getattr(settings, "climate_request_timeout_seconds", _DEFAULT_CLIMATE_TIMEOUT_SECONDS)
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
