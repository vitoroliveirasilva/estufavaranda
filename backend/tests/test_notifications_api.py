from tests.conftest import login


def test_notifications_list_endpoint(client):
    auth = login(client, "user@example.com", "User12345")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    assert "data" in response.get_json()
