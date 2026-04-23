def test_notifications_list_mark_read_and_discard(
    client,
    auth_headers_for,
    create_notification,
):
    headers = auth_headers_for("user@example.com", "User12345")
    notification_id = create_notification(user_key="user", title="Rega pendente")

    list_response = client.get(
        "/api/v1/notifications?status=pending",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.get_json()
    assert payload["meta"]["total"] >= 1
    ids = [item["id"] for item in payload["data"]]
    assert notification_id in ids

    read_response = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
        headers=headers,
    )
    assert read_response.status_code == 200
    assert read_response.get_json()["data"]["status"] == "read"

    second_notification_id = create_notification(user_key="user", title="Nova foto")
    discard_response = client.patch(
        f"/api/v1/notifications/{second_notification_id}/discard",
        headers=headers,
    )
    assert discard_response.status_code == 200
    assert discard_response.get_json()["data"]["status"] == "discarded"


def test_user_cannot_access_other_users_notification(
    client,
    auth_headers_for,
    create_notification,
):
    headers = auth_headers_for("user@example.com", "User12345")
    notification_id = create_notification(user_key="admin", title="Privado")

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
