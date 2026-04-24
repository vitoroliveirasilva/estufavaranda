from tests.conftest import login


def test_admin_can_create_and_list_user(client, auth_headers_for):
    headers = auth_headers_for("admin@example.com", "Admin123")

    create_response = client.post(
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
    assert create_response.status_code == 201, create_response.get_json()
    payload = create_response.get_json()["data"]
    assert payload["email"] == "novo@example.com"

    list_response = client.get("/api/v1/admin/users?search=novo", headers=headers)
    assert list_response.status_code == 200
    listed_emails = [item["email"] for item in list_response.get_json()["data"]]
    assert "novo@example.com" in listed_emails


def test_non_admin_cannot_create_user(client, auth_headers_for):
    headers = auth_headers_for("user@example.com", "User12345")
    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "name": "Sem Permissão",
            "email": "sempermissao@example.com",
            "password": "Senha1234",
            "is_admin": False,
            "is_active": True,
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "authorization_error"


def test_admin_cannot_create_duplicate_user(client, auth_headers_for):
    headers = auth_headers_for("admin@example.com", "Admin123")
    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "name": "Duplicado",
            "email": "USER@example.com",
            "password": "Senha1234",
            "is_admin": False,
            "is_active": True,
        },
    )
    assert response.status_code == 409
    error = response.get_json()["error"]
    assert error["code"] == "conflict"
    assert error["details"]["email"] == "duplicated"


def test_admin_can_reset_password_and_user_can_login_with_new_password(
    client, auth_headers_for
):
    headers = auth_headers_for("admin@example.com", "Admin123")
    response = client.post(
        "/api/v1/admin/users/2/reset-password",
        headers=headers,
        json={"new_password": "NovaSenha123"},
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["user_id"] == 2

    login_response = login(
        client,
        "user@example.com",
        "NovaSenha123",
        expected_status=200,
    )
    assert login_response["data"]["user"]["email"] == "user@example.com"
