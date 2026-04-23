from tests.conftest import login


def test_login_and_me(client):
    auth = login(client, "admin@example.com", "Admin123")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    payload = me_response.get_json()["data"]
    assert payload["email"] == "admin@example.com"
    assert payload["is_admin"] is True


def test_forgot_password_is_generic(client):
    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 200
    assert "Se o e-mail estiver cadastrado" in response.get_json()["data"]["message"]
