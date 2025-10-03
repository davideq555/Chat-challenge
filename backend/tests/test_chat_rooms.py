import pytest
from fastapi import status

def test_create_chat_room(client):
    """Test crear una nueva sala de chat"""
    response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Room"
    assert data["is_group"] is True
    assert "id" in data
    assert "created_at" in data

def test_create_1to1_chat_room(client):
    """Test crear una sala de chat 1 a 1"""
    response = client.post("/chat-rooms/", json={
        "name": "Private Chat",
        "is_group": False
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Private Chat"
    assert data["is_group"] is False

def test_get_all_chat_rooms(client):
    """Test obtener todas las salas de chat"""
    client.post("/chat-rooms/", json={
        "name": "Room 1",
        "is_group": True
    })
    client.post("/chat-rooms/", json={
        "name": "Room 2",
        "is_group": False
    })

    response = client.get("/chat-rooms/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Room 1"
    assert data[1]["name"] == "Room 2"

def test_get_chat_rooms_filter_by_group(client):
    """Test filtrar salas de chat por tipo"""
    client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    })
    client.post("/chat-rooms/", json={
        "name": "Private Room",
        "is_group": False
    })
    client.post("/chat-rooms/", json={
        "name": "Another Group",
        "is_group": True
    })

    # Filtrar solo salas grupales
    response = client.get("/chat-rooms/?is_group=true")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(room["is_group"] is True for room in data)

    # Filtrar solo salas 1 a 1
    response = client.get("/chat-rooms/?is_group=false")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_group"] is False

def test_get_chat_room_by_id(client):
    """Test obtener sala de chat por ID"""
    create_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    })
    room_id = create_response.json()["id"]

    response = client.get(f"/chat-rooms/{room_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Test Room"

def test_get_chat_room_not_found(client):
    """Test obtener sala de chat que no existe"""
    response = client.get("/chat-rooms/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]

def test_update_chat_room(client):
    """Test actualizar sala de chat"""
    create_response = client.post("/chat-rooms/", json={
        "name": "Original Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    response = client.put(f"/chat-rooms/{room_id}", json={
        "name": "Updated Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Room"
    assert data["is_group"] is True

def test_update_chat_room_partial(client):
    """Test actualización parcial de sala de chat"""
    create_response = client.post("/chat-rooms/", json={
        "name": "Original Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    # Solo actualizar nombre
    response = client.put(f"/chat-rooms/{room_id}", json={
        "name": "New Name"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["is_group"] is False  # No cambió

def test_update_chat_room_not_found(client):
    """Test actualizar sala de chat que no existe"""
    response = client.put("/chat-rooms/999", json={
        "name": "Updated Room"
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_chat_room(client):
    """Test eliminar sala de chat"""
    create_response = client.post("/chat-rooms/", json={
        "name": "Room to Delete",
        "is_group": True
    })
    room_id = create_response.json()["id"]

    response = client.delete(f"/chat-rooms/{room_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que la sala ya no existe
    get_response = client.get(f"/chat-rooms/{room_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_chat_room_not_found(client):
    """Test eliminar sala de chat que no existe"""
    response = client.delete("/chat-rooms/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
