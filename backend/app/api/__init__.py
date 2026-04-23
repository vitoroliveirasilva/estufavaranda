from __future__ import annotations

from flask import Flask

from app.api.admin import admin_bp
from app.api.ai import ai_bp
from app.api.auth import auth_bp
from app.api.climate import climate_bp
from app.api.events import events_bp
from app.api.health import health_bp
from app.api.notifications import notifications_bp
from app.api.photos import photos_bp
from app.api.plants import plants_bp
from app.api.species import species_bp
from app.api.watering import watering_bp


def register_blueprints(app: Flask) -> None:
    blueprints = (
        (health_bp, None),
        (auth_bp, "/api/v1/auth"),
        (admin_bp, "/api/v1/admin"),
        (plants_bp, "/api/v1/plants"),
        (species_bp, "/api/v1/species"),
        (events_bp, "/api/v1/plants"),
        (photos_bp, "/api/v1/plants"),
        (watering_bp, "/api/v1/plants"),
        (climate_bp, "/api/v1"),
        (notifications_bp, "/api/v1"),
        (ai_bp, "/api/v1/plants"),
    )

    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)
