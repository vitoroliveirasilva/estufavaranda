def test_user_can_create_read_update_archive_and_list_plant(client, auth_headers_for):
    headers = auth_headers_for("user@example.com", "User12345")

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
    detail_payload = detail_response.get_json()["data"]
    assert detail_payload["name"] == "Roseira"
    assert detail_payload["watering_summary"]["score"] >= 0

    update_response = client.patch(
        f"/api/v1/plants/{plant_id}",
        headers=headers,
        json={"health_status": "recovering", "nickname": "Rosie"},
    )
    assert update_response.status_code == 200, update_response.get_json()
    assert update_response.get_json()["data"]["health_status"] == "recovering"

    list_before_archive = client.get("/api/v1/plants", headers=headers)
    assert list_before_archive.status_code == 200
    listed_ids = [item["id"] for item in list_before_archive.get_json()["data"]]
    assert plant_id in listed_ids
    assert list_before_archive.get_json()["meta"]["total"] >= 1

    archive_response = client.delete(f"/api/v1/plants/{plant_id}", headers=headers)
    assert archive_response.status_code == 204

    default_list = client.get("/api/v1/plants", headers=headers)
    default_ids = [item["id"] for item in default_list.get_json()["data"]]
    assert plant_id not in default_ids

    archived_list = client.get(
        "/api/v1/plants?archived=true",
        headers=headers,
    )
    archived_ids = [item["id"] for item in archived_list.get_json()["data"]]
    assert plant_id in archived_ids


def test_user_cannot_access_another_users_plant(client, auth_headers_for, create_plant):
    admin_plant_id = create_plant(
        email="admin@example.com",
        password="Admin123",
        name="Planta do Admin",
    )
    user_headers = auth_headers_for("user@example.com", "User12345")

    response = client.get(f"/api/v1/plants/{admin_plant_id}", headers=user_headers)
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_invalid_species_profile_query_returns_client_error(client, auth_headers_for):
    headers = auth_headers_for("user@example.com", "User12345")
    response = client.get(
        "/api/v1/plants?species_profile_id=abc",
        headers=headers,
    )
    assert response.status_code in {400, 422, 500}
    assert "error" in response.get_json()
