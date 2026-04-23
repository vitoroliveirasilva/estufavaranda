from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ClimateData:
    city_name: str
    temperature_c: float | None
    humidity_percent: int | None
    rain_mm: float | None
    feels_like_c: float | None
    uv_index: float | None
    raw_payload: dict


class OpenMeteoClimateProvider:
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def fetch_by_city(self, city_name: str) -> ClimateData:
        settings = get_settings()

        geo_resp = requests.get(
            self.GEOCODE_URL,
            params={"name": city_name, "count": 1, "language": "pt", "format": "json"},
            timeout=settings.climate_request_timeout_seconds,
        )
        geo_resp.raise_for_status()
        geo_payload = geo_resp.json()
        results = geo_payload.get("results") or []
        if not results:
            raise ValueError(f"Cidade não encontrada: {city_name}")
        place = results[0]

        weather_resp = requests.get(
            self.WEATHER_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,uv_index",
                "timezone": "auto",
            },
            timeout=settings.climate_request_timeout_seconds,
        )
        weather_resp.raise_for_status()
        payload = weather_resp.json()
        current = payload.get("current", {})

        return ClimateData(
            city_name=place["name"],
            temperature_c=current.get("temperature_2m"),
            humidity_percent=current.get("relative_humidity_2m"),
            rain_mm=current.get("precipitation"),
            feels_like_c=current.get("apparent_temperature"),
            uv_index=current.get("uv_index"),
            raw_payload=payload,
        )


def get_climate_provider():
    settings = get_settings()
    provider = settings.climate_provider.lower()
    if provider == "open_meteo":
        return OpenMeteoClimateProvider()
    raise ValueError(f"Provider de clima não suportado: {provider}")
