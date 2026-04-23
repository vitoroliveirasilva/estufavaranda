def test_watering_log_affects_summary_and_creates_event(
    client,
    auth_headers_for,
    create_plant,
):
    headers = auth_headers_for("user@example.com", "User12345")
    plant_id = create_plant(
        name="Costela de Adão",
        environment="indoor",
        light_exposure="bright_indirect",
        city_name="Jundiaí",
    )

    before = client.get(
        f"/api/v1/plants/{plant_id}/watering-summary",
        headers=headers,
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
        f"/api/v1/plants/{plant_id}/watering-summary",
        headers=headers,
    ).get_json()["data"]
    assert before["score"] >= after["score"]
    assert after["last_watering"]["quantity_ml"] == 300

    detail = client.get(f"/api/v1/plants/{plant_id}", headers=headers).get_json()[
        "data"
    ]
    assert any(event["event_type"] == "watering" for event in detail["recent_events"])


def test_invalid_watering_payload_is_rejected(client, auth_headers_for, create_plant):
    headers = auth_headers_for("user@example.com", "User12345")
    plant_id = create_plant(name="Jiboia")

    response = client.post(
        f"/api/v1/plants/{plant_id}/watering-logs",
        headers=headers,
        json={
            "watered_at": "not-a-datetime",
            "quantity_ml": -10,
        },
    )
    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "validation_error"
    assert "quantity_ml" in error["details"] or "watered_at" in error["details"]
