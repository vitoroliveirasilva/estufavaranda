from conftest import login


def test_login_refresh_logout_and_me_flow(client):
    auth_payload = login(client, "admin@example.com", "Admin123")["data"]
    headers = {"Authorization": f"Bearer {auth_payload['access_token']}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.get_json()["data"]
    assert me_data["email"] == "admin@example.com"
    assert me_data["is_admin"] is True

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.get_json()["data"]["token_type"] == "bearer"

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": auth_payload["refresh_token"]},
    )
    assert logout_response.status_code == 204

    revoked_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth_payload["refresh_token"]},
    )
    assert revoked_refresh_response.status_code == 401
    assert (
        revoked_refresh_response.get_json()["error"]["code"] == "authentication_error"
    )


def test_login_requires_valid_credentials(client):
    response = login(
        client,
        "admin@example.com",
        "senha-errada",
        expected_status=401,
    )
    assert response["error"]["code"] == "authentication_error"


def test_forgot_password_is_generic_for_unknown_and_known_email(client):
    unknown_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "ghost@example.com"},
    )
    assert unknown_response.status_code == 200

    known_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    assert known_response.status_code == 200

    expected_message = "Se o e-mail estiver cadastrado, você receberá instruções para redefinir sua senha."
    assert unknown_response.get_json()["data"]["message"] == expected_message
    assert known_response.get_json()["data"]["message"] == expected_message


def test_register_device_requires_authentication(client, auth_headers_for):
    unauthorized = client.post(
        "/api/v1/auth/devices/register",
        json={"platform": "android", "push_token": "abc123"},
    )
    assert unauthorized.status_code == 401

    headers = auth_headers_for("user@example.com", "User12345")
    authorized = client.post(
        "/api/v1/auth/devices/register",
        headers=headers,
        json={
            "device_name": "Pixel 9",
            "platform": "ANDROID",
            "push_token": "push-token-123",
        },
    )
    assert authorized.status_code == 200, authorized.get_json()
    payload = authorized.get_json()["data"]
    assert payload["platform"] == "android"
    assert payload["notifications_enabled"] is True
