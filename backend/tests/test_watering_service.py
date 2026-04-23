from tests.conftest import login


def test_watering_log_affects_summary(client):
    auth = login(client, "user@example.com", "User12345")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    plant_response = client.post(
        "/api/v1/plants",
        headers=headers,
        json={
            "name": "Costela de Adão",
            "environment": "indoor",
            "light_exposure": "bright_indirect",
            "city_name": "Jundiaí",
        },
    )
    plant_id = plant_response.get_json()["data"]["id"]

    before = client.get(
        f"/api/v1/plants/{plant_id}/watering-summary", headers=headers
    ).get_json()["data"]
    create_log = client.post(
        f"/api/v1/plants/{plant_id}/watering-logs",
        headers=headers,
        json={
            "watered_at": "2026-04-23T10:00:00-03:00",
            "quantity_ml": 300,
            "notes": "Solo seco",
        },
    )
    assert create_log.status_code == 201, create_log.get_json()

    after = client.get(
        f"/api/v1/plants/{plant_id}/watering-summary", headers=headers
    ).get_json()["data"]
    assert before["score"] >= after["score"]
    assert after["last_watering"]["quantity_ml"] == 300
