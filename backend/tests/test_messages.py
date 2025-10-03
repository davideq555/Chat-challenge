import pytest
from fastapi import status

def test_create_message(client):
    """Test crear un nuevo mensaje"""
    response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Hello World!"
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["room_id"] == 1
    assert data["user_id"] == 1
    assert data["content"] == "Hello World!"
    assert data["is_deleted"] is False
    assert "id" in data
    assert "created_at" in data

def test_get_all_messages(client):
    """Test obtener todos los mensajes"""
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Message 1"
    })
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 2,
        "content": "Message 2"
    })

    response = client.get("/messages/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_messages_filter_by_room(client):
    """Test filtrar mensajes por sala"""
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Room 1 message"
    })
    client.post("/messages/", json={
        "room_id": 2,
        "user_id": 1,
        "content": "Room 2 message"
    })

    response = client.get("/messages/?room_id=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["room_id"] == 1
    assert data[0]["content"] == "Room 1 message"

def test_get_messages_filter_by_user(client):
    """Test filtrar mensajes por usuario"""
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "User 1 message"
    })
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 2,
        "content": "User 2 message"
    })

    response = client.get("/messages/?user_id=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == 1

def test_get_messages_exclude_deleted(client):
    """Test que los mensajes eliminados no se muestran por defecto"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "To be deleted"
    })
    message_id = create_response.json()["id"]

    # Eliminar mensaje (soft delete)
    client.delete(f"/messages/{message_id}?soft_delete=true")

    # Por defecto no debe aparecer
    response = client.get("/messages/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

def test_get_messages_include_deleted(client):
    """Test incluir mensajes eliminados"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Deleted message"
    })
    message_id = create_response.json()["id"]

    client.delete(f"/messages/{message_id}?soft_delete=true")

    # Con include_deleted=true debe aparecer
    response = client.get("/messages/?include_deleted=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_deleted"] is True

def test_get_message_by_id(client):
    """Test obtener mensaje por ID"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Test message"
    })
    message_id = create_response.json()["id"]

    response = client.get(f"/messages/{message_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == message_id
    assert data["content"] == "Test message"

def test_get_message_not_found(client):
    """Test obtener mensaje que no existe"""
    response = client.get("/messages/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Message not found" in response.json()["detail"]

def test_update_message(client):
    """Test actualizar contenido de mensaje"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Original content"
    })
    message_id = create_response.json()["id"]

    response = client.put(f"/messages/{message_id}", json={
        "content": "Updated content"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["updated_at"] is not None

def test_update_message_not_found(client):
    """Test actualizar mensaje que no existe"""
    response = client.put("/messages/999", json={
        "content": "Updated"
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_cannot_update_deleted_message(client):
    """Test que no se puede editar un mensaje eliminado"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Original"
    })
    message_id = create_response.json()["id"]

    # Eliminar mensaje
    client.delete(f"/messages/{message_id}?soft_delete=true")

    # Intentar actualizar
    response = client.put(f"/messages/{message_id}", json={
        "content": "Updated"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot edit deleted message" in response.json()["detail"]

def test_soft_delete_message(client):
    """Test soft delete de mensaje"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "To be soft deleted"
    })
    message_id = create_response.json()["id"]

    response = client.delete(f"/messages/{message_id}?soft_delete=true")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el mensaje existe pero está marcado como eliminado
    get_response = client.get(f"/messages/{message_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["is_deleted"] is True

def test_hard_delete_message(client):
    """Test hard delete de mensaje"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "To be hard deleted"
    })
    message_id = create_response.json()["id"]

    response = client.delete(f"/messages/{message_id}?soft_delete=false")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el mensaje ya no existe
    get_response = client.get(f"/messages/{message_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_message_not_found(client):
    """Test eliminar mensaje que no existe"""
    response = client.delete("/messages/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_restore_message(client):
    """Test restaurar mensaje eliminado"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "To restore"
    })
    message_id = create_response.json()["id"]

    # Soft delete
    client.delete(f"/messages/{message_id}?soft_delete=true")

    # Restaurar
    response = client.post(f"/messages/{message_id}/restore")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_deleted"] is False
    assert data["updated_at"] is not None

def test_restore_message_not_deleted(client):
    """Test que no se puede restaurar un mensaje que no está eliminado"""
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Not deleted"
    })
    message_id = create_response.json()["id"]

    response = client.post(f"/messages/{message_id}/restore")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Message is not deleted" in response.json()["detail"]

def test_restore_message_not_found(client):
    """Test restaurar mensaje que no existe"""
    response = client.post("/messages/999/restore")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_latest_messages_from_room(client):
    """Test obtener últimos mensajes de una sala"""
    # Crear varios mensajes
    for i in range(5):
        client.post("/messages/", json={
            "room_id": 1,
            "user_id": 1,
            "content": f"Message {i}"
        })

    response = client.get("/messages/room/1/latest?limit=3")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    # Deben estar ordenados del más reciente al más antiguo
    assert data[0]["content"] == "Message 4"
    assert data[1]["content"] == "Message 3"
    assert data[2]["content"] == "Message 2"

def test_latest_messages_exclude_deleted(client):
    """Test que los mensajes recientes no incluyen eliminados"""
    client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Message 1"
    })
    create_response = client.post("/messages/", json={
        "room_id": 1,
        "user_id": 1,
        "content": "Message 2"
    })
    message_id = create_response.json()["id"]

    # Eliminar el segundo mensaje
    client.delete(f"/messages/{message_id}?soft_delete=true")

    response = client.get("/messages/room/1/latest")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Message 1"

def test_latest_messages_limit(client):
    """Test límite de mensajes recientes"""
    # Crear 10 mensajes
    for i in range(10):
        client.post("/messages/", json={
            "room_id": 1,
            "user_id": 1,
            "content": f"Message {i}"
        })

    response = client.get("/messages/room/1/latest?limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
