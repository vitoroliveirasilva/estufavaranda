from tests.conftest import login


def test_user_can_create_and_read_plant(client):
    auth = login(client, "user@example.com", "User12345")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    create_response = client.post(
        "/api/v1/plants",
        headers=headers,
        json={
            "name": "Roseira",
            "environment": "outdoor",
            "light_exposure": "afternoon_sun",
            "location_label": "Varanda",
            "city_name": "Campo Limpo Paulista",
        },
    )
    assert create_response.status_code == 201, create_response.get_json()
    plant_id = create_response.get_json()["data"]["id"]

    detail_response = client.get(f"/api/v1/plants/{plant_id}", headers=headers)
    assert detail_response.status_code == 200
    payload = detail_response.get_json()["data"]
    assert payload["name"] == "Roseira"
    assert payload["watering_summary"]["score"] >= 0
