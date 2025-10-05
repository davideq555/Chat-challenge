import pytest
from fastapi import status
from tests.conftest import create_test_user, login_user, get_auth_headers

def test_create_message(client, db_session):
    """Test crear un nuevo mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Hello World!"
    }, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["room_id"] == room_id
    assert data["content"] == "Hello World!"
    assert data["is_deleted"] is False
    assert "id" in data
    assert "created_at" in data

def test_get_all_messages(client, db_session):
    """Test obtener todos los mensajes con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensajes
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 1"
    }, headers=headers)
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 2"
    }, headers=headers)

    response = client.get("/messages/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_messages_filter_by_room(client, db_session):
    """Test filtrar mensajes por sala con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear dos salas
    room1_response = client.post("/chat-rooms/", json={
        "name": "Room 1",
        "is_group": True
    }, headers=headers)
    room1_id = room1_response.json()["id"]

    room2_response = client.post("/chat-rooms/", json={
        "name": "Room 2",
        "is_group": True
    }, headers=headers)
    room2_id = room2_response.json()["id"]

    # Crear mensajes
    client.post("/messages/", json={
        "room_id": room1_id,
        "content": "Room 1 message"
    }, headers=headers)
    client.post("/messages/", json={
        "room_id": room2_id,
        "content": "Room 2 message"
    }, headers=headers)

    response = client.get(f"/messages/?room_id={room1_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["room_id"] == room1_id
    assert data[0]["content"] == "Room 1 message"

def test_get_messages_filter_by_user(client, db_session):
    """Test filtrar mensajes por usuario con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])
    user_id = login_data["user"]["id"]

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensajes
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "User message"
    }, headers=headers)

    response = client.get(f"/messages/?user_id={user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id

def test_get_messages_exclude_deleted(client, db_session):
    """Test que los mensajes eliminados no se muestran por defecto con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "To be deleted"
    }, headers=headers)
    message_id = create_response.json()["id"]

    # Eliminar mensaje (soft delete)
    client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)

    # Por defecto no debe aparecer
    response = client.get("/messages/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

def test_get_messages_include_deleted(client, db_session):
    """Test incluir mensajes eliminados con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Deleted message"
    }, headers=headers)
    message_id = create_response.json()["id"]

    # Eliminar
    client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)

    # Con include_deleted=true debe aparecer
    response = client.get("/messages/?include_deleted=true", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_deleted"] is True

def test_get_message_by_id(client, db_session):
    """Test obtener mensaje por ID con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Test message"
    }, headers=headers)
    message_id = create_response.json()["id"]

    response = client.get(f"/messages/{message_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == message_id
    assert data["content"] == "Test message"

def test_get_message_not_found(client, db_session):
    """Test obtener mensaje que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.get("/messages/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Message not found" in response.json()["detail"]

def test_update_message(client, db_session):
    """Test actualizar contenido de mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Original content"
    }, headers=headers)
    message_id = create_response.json()["id"]

    response = client.put(f"/messages/{message_id}", json={
        "content": "Updated content"
    }, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["updated_at"] is not None

def test_update_message_not_found(client, db_session):
    """Test actualizar mensaje que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.put("/messages/999", json={
        "content": "Updated"
    }, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_cannot_update_deleted_message(client, db_session):
    """Test que no se puede editar un mensaje eliminado con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Original"
    }, headers=headers)
    message_id = create_response.json()["id"]

    # Eliminar mensaje
    client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)

    # Intentar actualizar
    response = client.put(f"/messages/{message_id}", json={
        "content": "Updated"
    }, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot edit deleted message" in response.json()["detail"]

def test_soft_delete_message(client, db_session):
    """Test soft delete de mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "To be soft deleted"
    }, headers=headers)
    message_id = create_response.json()["id"]

    response = client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el mensaje existe pero está marcado como eliminado
    get_response = client.get(f"/messages/{message_id}", headers=headers)
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["is_deleted"] is True

def test_hard_delete_message(client, db_session):
    """Test hard delete de mensaje con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "To be hard deleted"
    }, headers=headers)
    message_id = create_response.json()["id"]

    response = client.delete(f"/messages/{message_id}?soft_delete=false", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el mensaje ya no existe
    get_response = client.get(f"/messages/{message_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_message_not_found(client, db_session):
    """Test eliminar mensaje que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.delete("/messages/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_restore_message(client, db_session):
    """Test restaurar mensaje eliminado con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "To restore"
    }, headers=headers)
    message_id = create_response.json()["id"]

    # Soft delete
    client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)

    # Restaurar
    response = client.post(f"/messages/{message_id}/restore", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_deleted"] is False
    assert data["updated_at"] is not None

def test_restore_message_not_deleted(client, db_session):
    """Test que no se puede restaurar un mensaje que no está eliminado con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensaje
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Not deleted"
    }, headers=headers)
    message_id = create_response.json()["id"]

    response = client.post(f"/messages/{message_id}/restore", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Message is not deleted" in response.json()["detail"]

def test_restore_message_not_found(client, db_session):
    """Test restaurar mensaje que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.post("/messages/999/restore", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_latest_messages_from_room(client, db_session):
    """Test obtener últimos mensajes de una sala con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear varios mensajes
    for i in range(5):
        client.post("/messages/", json={
            "room_id": room_id,
            "content": f"Message {i}"
        }, headers=headers)

    response = client.get(f"/messages/room/{room_id}/latest?limit=3", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    # Deben estar ordenados del más reciente al más antiguo
    assert data[0]["content"] == "Message 4"
    assert data[1]["content"] == "Message 3"
    assert data[2]["content"] == "Message 2"

def test_latest_messages_exclude_deleted(client, db_session):
    """Test que los mensajes recientes no incluyen eliminados con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear mensajes
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 1"
    }, headers=headers)
    create_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Message 2"
    }, headers=headers)
    message_id = create_response.json()["id"]

    # Eliminar el segundo mensaje
    client.delete(f"/messages/{message_id}?soft_delete=true", headers=headers)

    response = client.get(f"/messages/room/{room_id}/latest", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Message 1"

def test_latest_messages_limit(client, db_session):
    """Test límite de mensajes recientes con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Crear 10 mensajes
    for i in range(10):
        client.post("/messages/", json={
            "room_id": room_id,
            "content": f"Message {i}"
        }, headers=headers)

    response = client.get(f"/messages/room/{room_id}/latest?limit=5", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
