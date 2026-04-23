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
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(plants_bp, url_prefix="/api/v1/plants")
    app.register_blueprint(species_bp, url_prefix="/api/v1/species")
    app.register_blueprint(events_bp, url_prefix="/api/v1/plants")
    app.register_blueprint(photos_bp, url_prefix="/api/v1/plants")
    app.register_blueprint(watering_bp, url_prefix="/api/v1/plants")
    app.register_blueprint(climate_bp, url_prefix="/api/v1")
    app.register_blueprint(notifications_bp, url_prefix="/api/v1")
    app.register_blueprint(ai_bp, url_prefix="/api/v1/plants")
