from __future__ import annotations

from collections.abc import Callable

import pytest

from app import create_app
from app.core.config import get_settings
from app.core.security import hash_password, utcnow
from app.extensions import db
from app.models import NotificationEvent, NotificationStatus, User


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_SECRET", "access-secret")
    monkeypatch.setenv("REFRESH_TOKEN_SECRET", "refresh-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("UPLOAD_BASE_PATH", str(tmp_path / "uploads"))
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("ENABLE_ADMIN_READ_ALL_PLANTS", "true")
    monkeypatch.setenv("AI_PROVIDER_MODE", "rules")
    monkeypatch.setenv("LOG_JSON", "false")
    get_settings.cache_clear()

    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.create_all()
        db.session.add_all(
            [
                User(
                    name="Admin",
                    email="admin@example.com",
                    password_hash=hash_password("Admin123"),
                    is_admin=True,
                    is_active=True,
                ),
                User(
                    name="User",
                    email="user@example.com",
                    password_hash=hash_password("User12345"),
                    is_admin=False,
                    is_active=True,
                ),
            ]
        )
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.session.remove()

    get_settings.cache_clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user_ids(app) -> dict[str, int]:
    with app.app_context():
        admin_id = db.session.execute(
            db.select(User.id).where(User.email == "admin@example.com")
        ).scalar_one()
        user_id = db.session.execute(
            db.select(User.id).where(User.email == "user@example.com")
        ).scalar_one()
    return {"admin": admin_id, "user": user_id}


def login(
    client,
    email: str,
    password: str,
    *,
    expected_status: int = 200,
) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == expected_status, response.get_json()
    return response.get_json()


@pytest.fixture()
def auth_headers_for(client) -> Callable[[str, str], dict[str, str]]:
    def _build(email: str, password: str) -> dict[str, str]:
        payload = login(client, email, password)["data"]
        return {"Authorization": f"Bearer {payload['access_token']}"}

    return _build


@pytest.fixture()
def create_plant(client, auth_headers_for) -> Callable[..., int]:
    def _create(
        *,
        email: str = "user@example.com",
        password: str = "User12345",
        **overrides,
    ) -> int:
        headers = auth_headers_for(email, password)
        payload = {
            "name": "Roseira",
            "environment": "outdoor",
            "light_exposure": "afternoon_sun",
            "location_label": "Varanda",
            "city_name": "Campo Limpo Paulista",
        }
        payload.update(overrides)
        response = client.post("/api/v1/plants", headers=headers, json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()["data"]["id"]

    return _create


@pytest.fixture()
def create_notification(app, user_ids) -> Callable[..., int]:
    def _create(
        *,
        user_key: str = "user",
        title: str = "Alerta",
        body: str = "Corpo do alerta",
        alert_type: str = "watering_risk",
        status: str = NotificationStatus.PENDING.value,
        dedupe_key: str | None = None,
        plant_id: int | None = None,
    ) -> int:
        with app.app_context():
            item = NotificationEvent(
                user_id=user_ids[user_key],
                plant_id=plant_id,
                type=alert_type,
                title=title,
                body=body,
                status=status,
                dedupe_key=dedupe_key,
                created_at=utcnow(),
            )
            db.session.add(item)
            db.session.commit()
            return item.id

    return _create
