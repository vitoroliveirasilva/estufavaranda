from __future__ import annotations

import pytest

from app import create_app
from app.core.config import get_settings
from app.core.security import hash_password
from app.extensions import db
from app.models import User


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_SECRET", "access-secret")
    monkeypatch.setenv("REFRESH_TOKEN_SECRET", "refresh-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("UPLOAD_BASE_PATH", str(tmp_path / "uploads"))
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost")
    monkeypatch.setenv("ENABLE_ADMIN_READ_ALL_PLANTS", "true")
    get_settings.cache_clear()

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        admin = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hash_password("Admin123"),
            is_admin=True,
            is_active=True,
        )
        user = User(
            name="User",
            email="user@example.com",
            password_hash=hash_password("User12345"),
            is_admin=False,
            is_active=True,
        )
        db.session.add_all([admin, user])
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]
