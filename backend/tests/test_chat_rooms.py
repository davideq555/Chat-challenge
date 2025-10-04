import pytest
from fastapi import status

# ============================================================================
# TESTS PARA CREAR SALAS
# ============================================================================

def test_create_chat_room(client, db_session):
    """Test crear una nueva sala de chat con creator_id"""
    # Primero crear un usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    # Crear sala con creator_id
    response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Test Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Room"
    assert data["is_group"] is True
    assert "id" in data
    assert "created_at" in data

def test_create_chat_room_without_creator(client):
    """Test crear sala sin creator_id debe fallar"""
    response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_create_chat_room_with_invalid_creator(client):
    """Test crear sala con creator_id inexistente"""
    response = client.post("/chat-rooms/?creator_id=999", json={
        "name": "Test Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Creator user not found" in response.json()["detail"]

def test_create_1to1_chat_room(client, db_session):
    """Test crear una sala de chat 1 a 1"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Private Chat",
        "is_group": False
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Private Chat"
    assert data["is_group"] is False

# ============================================================================
# TESTS PARA OBTENER SALAS
# ============================================================================

def test_get_all_chat_rooms(client, db_session):
    """Test obtener todas las salas de chat"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Room 1",
        "is_group": True
    })
    client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Room 2",
        "is_group": False
    })

    response = client.get("/chat-rooms/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_chat_rooms_filter_by_group(client, db_session):
    """Test filtrar salas de chat por tipo"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Group Room",
        "is_group": True
    })
    client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Private Room",
        "is_group": False
    })
    client.post("/chat-rooms/?creator_id={}".format(user_id), json={
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

def test_get_chat_room_by_id(client, db_session):
    """Test obtener sala de chat por ID (requiere ser participante)"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    # Crear sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Test Room",
        "is_group": True
    })
    room_id = create_response.json()["id"]

    # Obtener sala (el creador es automáticamente participante)
    response = client.get("/chat-rooms/{}?user_id={}".format(room_id, user_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Test Room"

def test_get_chat_room_not_found(client, db_session):
    """Test obtener sala de chat que no existe"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    response = client.get("/chat-rooms/999?user_id={}".format(user_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]

def test_get_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede acceder a una sala"""
    # Crear dos usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Private Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    # User2 intenta acceder (no es participante)
    response = client.get("/chat-rooms/{}?user_id={}".format(room_id, user2_id))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA ACTUALIZAR SALAS
# ============================================================================

def test_update_chat_room(client, db_session):
    """Test actualizar sala de chat (requiere ser participante)"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    # Crear sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Original Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    # Actualizar sala
    response = client.put("/chat-rooms/{}?user_id={}".format(room_id, user_id), json={
        "name": "Updated Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Room"
    assert data["is_group"] is True

def test_update_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede actualizar una sala"""
    # Crear dos usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Original Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    # User2 intenta actualizar (no es participante)
    response = client.put("/chat-rooms/{}?user_id={}".format(room_id, user2_id), json={
        "name": "Hacked Room"
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA ELIMINAR SALAS
# ============================================================================

def test_delete_chat_room(client, db_session):
    """Test eliminar sala de chat (requiere ser participante)"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    # Crear sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Room to Delete",
        "is_group": True
    })
    room_id = create_response.json()["id"]

    # Eliminar sala
    response = client.delete("/chat-rooms/{}?user_id={}".format(room_id, user_id))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que la sala ya no existe
    get_response = client.get("/chat-rooms/{}?user_id={}".format(room_id, user_id))
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede eliminar una sala"""
    # Crear dos usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    create_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Protected Room",
        "is_group": False
    })
    room_id = create_response.json()["id"]

    # User2 intenta eliminar (no es participante)
    response = client.delete("/chat-rooms/{}?user_id={}".format(room_id, user2_id))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA OBTENER SALAS DE UN USUARIO (MY ROOMS)
# ============================================================================

def test_get_my_rooms(client, db_session):
    """Test obtener salas donde el usuario es participante"""
    # Crear usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea dos salas
    room1_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Room 1",
        "is_group": True
    })
    room1_id = room1_response.json()["id"]

    room2_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Room 2",
        "is_group": False
    })
    room2_id = room2_response.json()["id"]

    # User2 crea una sala
    room3_response = client.post("/chat-rooms/?creator_id={}".format(user2_id), json={
        "name": "Room 3",
        "is_group": True
    })
    room3_id = room3_response.json()["id"]

    # Agregar user1 a room3
    client.post("/chat-rooms/{}/participants?user_id={}".format(room3_id, user1_id))

    # Obtener salas de user1 (debe tener room1, room2, y room3)
    response = client.get("/chat-rooms/my-rooms/{}".format(user1_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    room_ids = [room["id"] for room in data]
    assert room1_id in room_ids
    assert room2_id in room_ids
    assert room3_id in room_ids

def test_get_my_rooms_user_not_found(client):
    """Test obtener salas de usuario inexistente"""
    response = client.get("/chat-rooms/my-rooms/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]

def test_get_my_rooms_empty(client, db_session):
    """Test obtener salas cuando el usuario no tiene ninguna"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    # Obtener salas (debe estar vacío)
    response = client.get("/chat-rooms/my-rooms/{}".format(user_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

# ============================================================================
# TESTS PARA GESTIÓN DE PARTICIPANTES
# ============================================================================

def test_add_participant_to_room(client, db_session):
    """Test agregar un participante a una sala"""
    # Crear usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Group Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    # Agregar user2 a la sala
    response = client.post("/chat-rooms/{}/participants?user_id={}".format(room_id, user2_id))
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["room_id"] == room_id
    assert data["user_id"] == user2_id
    assert "joined_at" in data

def test_add_participant_room_not_found(client, db_session):
    """Test agregar participante a sala inexistente"""
    # Crear usuario
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    response = client.post("/chat-rooms/999/participants?user_id={}".format(user_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]

def test_add_participant_user_not_found(client, db_session):
    """Test agregar usuario inexistente a una sala"""
    # Crear usuario y sala
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    room_response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Test Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    response = client.post("/chat-rooms/{}/participants?user_id=999".format(room_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]

def test_add_participant_already_member(client, db_session):
    """Test agregar participante que ya es miembro"""
    # Crear usuario y sala
    user_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = user_response.json()["id"]

    room_response = client.post("/chat-rooms/?creator_id={}".format(user_id), json={
        "name": "Test Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    # Intentar agregar nuevamente al creador (ya es participante automáticamente)
    response = client.post("/chat-rooms/{}/participants?user_id={}".format(room_id, user_id))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already a participant" in response.json()["detail"]

def test_remove_participant_from_room(client, db_session):
    """Test remover un participante de una sala"""
    # Crear usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Group Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    # Agregar user2
    client.post("/chat-rooms/{}/participants?user_id={}".format(room_id, user2_id))

    # Remover user2
    response = client.delete("/chat-rooms/{}/participants/{}".format(room_id, user2_id))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que user2 ya no puede acceder a la sala
    get_response = client.get("/chat-rooms/{}?user_id={}".format(room_id, user2_id))
    assert get_response.status_code == status.HTTP_403_FORBIDDEN

def test_remove_participant_not_found(client, db_session):
    """Test remover participante que no existe en la sala"""
    # Crear usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Group Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    # Intentar remover user2 (no es participante)
    response = client.delete("/chat-rooms/{}/participants/{}".format(room_id, user2_id))
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Participant not found" in response.json()["detail"]

def test_get_room_participants(client, db_session):
    """Test obtener lista de participantes de una sala"""
    # Crear usuarios
    user1_response = client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    user1_id = user1_response.json()["id"]

    user2_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user2_id = user2_response.json()["id"]

    user3_response = client.post("/users/", json={
        "username": "user3",
        "email": "user3@example.com",
        "password": "password123"
    })
    user3_id = user3_response.json()["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/?creator_id={}".format(user1_id), json={
        "name": "Group Room",
        "is_group": True
    })
    room_id = room_response.json()["id"]

    # Agregar user2 y user3
    client.post("/chat-rooms/{}/participants?user_id={}".format(room_id, user2_id))
    client.post("/chat-rooms/{}/participants?user_id={}".format(room_id, user3_id))

    # Obtener participantes
    response = client.get("/chat-rooms/{}/participants".format(room_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    participant_user_ids = [p["user_id"] for p in data]
    assert user1_id in participant_user_ids
    assert user2_id in participant_user_ids
    assert user3_id in participant_user_ids

def test_get_room_participants_room_not_found(client):
    """Test obtener participantes de sala inexistente"""
    response = client.get("/chat-rooms/999/participants")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]
