from tests.conftest import login


def test_admin_can_create_user(client):
    auth = login(client, "admin@example.com", "Admin123")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "name": "Novo Usuário",
            "email": "novo@example.com",
            "password": "Senha1234",
            "is_admin": False,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.get_json()
    payload = response.get_json()["data"]
    assert payload["email"] == "novo@example.com"
