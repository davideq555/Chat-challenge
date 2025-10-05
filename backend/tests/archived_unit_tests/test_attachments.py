import pytest
from fastapi import status
from tests.conftest import create_test_user, login_user, get_auth_headers

def test_create_attachment(client, db_session):
    """Test crear un nuevo adjunto con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message with attachment"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    response = client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message_id"] == message_id
    assert data["file_url"] == "https://example.com/file.jpg"
    assert data["file_type"] == "image/jpeg"
    assert "id" in data
    assert "uploaded_at" in data

def test_get_all_attachments(client, db_session):
    """Test obtener todos los adjuntos con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensajes
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message1_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 1"
    }, headers=headers)
    message1_id = message1_response.json()["id"]

    message2_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 2"
    }, headers=headers)
    message2_id = message2_response.json()["id"]

    # Crear adjuntos
    client.post("/attachments/", json={
        "message_id": message1_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message2_id,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    }, headers=headers)

    response = client.get("/attachments/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_attachments_filter_by_message(client, db_session):
    """Test filtrar adjuntos por mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensajes
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message1_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 1"
    }, headers=headers)
    message1_id = message1_response.json()["id"]

    message2_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 2"
    }, headers=headers)
    message2_id = message2_response.json()["id"]

    # Crear adjuntos
    client.post("/attachments/", json={
        "message_id": message1_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message2_id,
        "file_url": "https://example.com/file2.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message1_id,
        "file_url": "https://example.com/file3.pdf",
        "file_type": "application/pdf"
    }, headers=headers)

    response = client.get(f"/attachments/?message_id={message1_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["message_id"] == message1_id for att in data)

def test_get_attachments_filter_by_type(client, db_session):
    """Test filtrar adjuntos por tipo con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message with attachments"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjuntos
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file3.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)

    response = client.get("/attachments/?file_type=image/jpeg", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["file_type"].lower() == "image/jpeg" for att in data)

def test_get_attachments_filter_type_case_insensitive(client, db_session):
    """Test que el filtro por tipo es case insensitive con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "IMAGE/JPEG"
    }, headers=headers)

    response = client.get("/attachments/?file_type=image/jpeg", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

def test_get_attachment_by_id(client, db_session):
    """Test obtener adjunto por ID con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    create_response = client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    attachment_id = create_response.json()["id"]

    response = client.get(f"/attachments/{attachment_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == attachment_id
    assert data["file_url"] == "https://example.com/file.jpg"

def test_get_attachment_not_found(client, db_session):
    """Test obtener adjunto que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.get("/attachments/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Attachment not found" in response.json()["detail"]

def test_update_attachment(client, db_session):
    """Test actualizar adjunto con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    create_response = client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/old.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    attachment_id = create_response.json()["id"]

    response = client.put(f"/attachments/{attachment_id}", json={
        "file_url": "https://example.com/new.jpg",
        "file_type": "image/png"
    }, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["file_url"] == "https://example.com/new.jpg"
    assert data["file_type"] == "image/png"

def test_update_attachment_partial(client, db_session):
    """Test actualización parcial de adjunto con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    create_response = client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    attachment_id = create_response.json()["id"]

    # Solo actualizar URL
    response = client.put(f"/attachments/{attachment_id}", json={
        "file_url": "https://example.com/new.jpg"
    }, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["file_url"] == "https://example.com/new.jpg"
    assert data["file_type"] == "image/jpeg"  # No cambió

def test_update_attachment_not_found(client, db_session):
    """Test actualizar adjunto que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.put("/attachments/999", json={
        "file_url": "https://example.com/new.jpg"
    }, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_attachment(client, db_session):
    """Test eliminar adjunto con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjunto
    create_response = client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    attachment_id = create_response.json()["id"]

    response = client.delete(f"/attachments/{attachment_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el adjunto ya no existe
    get_response = client.get(f"/attachments/{attachment_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_attachment_not_found(client, db_session):
    """Test eliminar adjunto que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.delete("/attachments/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_message_attachments(client, db_session):
    """Test obtener todos los adjuntos de un mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensajes
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message1_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 1"
    }, headers=headers)
    message1_id = message1_response.json()["id"]

    message2_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 2"
    }, headers=headers)
    message2_id = message2_response.json()["id"]

    # Crear adjuntos
    client.post("/attachments/", json={
        "message_id": message1_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message1_id,
        "file_url": "https://example.com/file2.pdf",
        "file_type": "application/pdf"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message2_id,
        "file_url": "https://example.com/file3.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)

    response = client.get(f"/attachments/message/{message1_id}/all", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(att["message_id"] == message1_id for att in data)

def test_get_message_attachments_empty(client, db_session):
    """Test obtener adjuntos de mensaje sin adjuntos con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message without attachments"
    }, headers=headers)
    message_id = message_response.json()["id"]

    response = client.get(f"/attachments/message/{message_id}/all", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

def test_count_message_attachments(client, db_session):
    """Test contar adjuntos de un mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear adjuntos
    for i in range(3):
        client.post("/attachments/", json={
            "message_id": message_id,
            "file_url": f"https://example.com/file{i}.jpg",
            "file_type": "image/jpeg"
        }, headers=headers)

    response = client.get(f"/attachments/message/{message_id}/count", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message_id"] == message_id
    assert data["attachment_count"] == 3

def test_count_message_attachments_zero(client, db_session):
    """Test contar adjuntos de mensaje sin adjuntos con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    response = client.get(f"/attachments/message/{message_id}/count", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message_id"] == message_id
    assert data["attachment_count"] == 0

def test_get_attachments_stats_by_type(client, db_session):
    """Test obtener estadísticas de adjuntos por tipo con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala y mensaje
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message"
    }, headers=headers)
    message_id = message_response.json()["id"]

    # Crear varios adjuntos de diferentes tipos
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file1.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file2.jpg",
        "file_type": "image/jpeg"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file3.pdf",
        "file_type": "application/pdf"
    }, headers=headers)
    client.post("/attachments/", json={
        "message_id": message_id,
        "file_url": "https://example.com/file4.png",
        "file_type": "image/png"
    }, headers=headers)

    response = client.get("/attachments/stats/by-type", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_attachments"] == 4
    assert data["by_type"]["image/jpeg"] == 2
    assert data["by_type"]["application/pdf"] == 1
    assert data["by_type"]["image/png"] == 1

def test_get_attachments_stats_empty(client, db_session):
    """Test estadísticas cuando no hay adjuntos con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.get("/attachments/stats/by-type", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_attachments"] == 0
    assert data["by_type"] == {}
