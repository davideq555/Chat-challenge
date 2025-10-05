import pytest
from fastapi import status
from tests.conftest import create_test_user, login_user, get_auth_headers

# ============================================================================
# TESTS PARA CREAR SALAS
# ============================================================================

def test_create_chat_room(client, db_session):
    """Test crear una nueva sala de chat con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala con JWT
    response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Room"
    assert data["is_group"] is True
    assert "id" in data
    assert "created_at" in data

def test_create_chat_room_without_jwt(client):
    """Test crear sala sin JWT debe fallar con 401"""
    response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_create_1to1_chat_room(client, db_session):
    """Test crear una sala de chat 1 a 1 con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.post("/chat-rooms/", json={
        "name": "Private Chat",
        "is_group": False
    }, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Private Chat"
    assert data["is_group"] is False

# ============================================================================
# TESTS PARA OBTENER SALAS
# ============================================================================

def test_get_all_chat_rooms(client, db_session):
    """Test obtener todas las salas de chat"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    client.post("/chat-rooms/", json={
        "name": "Room 1",
        "is_group": True
    }, headers=headers)
    client.post("/chat-rooms/", json={
        "name": "Room 2",
        "is_group": False
    }, headers=headers)

    response = client.get("/chat-rooms/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

def test_get_chat_rooms_filter_by_group(client, db_session):
    """Test filtrar salas de chat por tipo"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    }, headers=headers)
    client.post("/chat-rooms/", json={
        "name": "Private Room",
        "is_group": False
    }, headers=headers)
    client.post("/chat-rooms/", json={
        "name": "Another Group",
        "is_group": True
    }, headers=headers)

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
    """Test obtener sala de chat por ID con JWT (requiere ser participante)"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = create_response.json()["id"]

    # Obtener sala (el creador es automáticamente participante)
    response = client.get(f"/chat-rooms/{room_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Test Room"

def test_get_chat_room_not_found(client, db_session):
    """Test obtener sala de chat que no existe con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.get("/chat-rooms/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]

def test_get_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede acceder a una sala con JWT"""
    # Crear dos usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    headers2 = get_auth_headers(login_data2["access_token"])

    # User1 crea una sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Private Room",
        "is_group": False
    }, headers=headers1)
    room_id = create_response.json()["id"]

    # User2 intenta acceder (no es participante)
    response = client.get(f"/chat-rooms/{room_id}", headers=headers2)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA ACTUALIZAR SALAS
# ============================================================================

def test_update_chat_room(client, db_session):
    """Test actualizar sala de chat con JWT (requiere ser participante)"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Original Room",
        "is_group": False
    }, headers=headers)
    room_id = create_response.json()["id"]

    # Actualizar sala
    response = client.put(f"/chat-rooms/{room_id}", json={
        "name": "Updated Room",
        "is_group": True
    }, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Room"
    assert data["is_group"] is True

def test_update_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede actualizar una sala con JWT"""
    # Crear dos usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    headers2 = get_auth_headers(login_data2["access_token"])

    # User1 crea una sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Original Room",
        "is_group": False
    }, headers=headers1)
    room_id = create_response.json()["id"]

    # User2 intenta actualizar (no es participante)
    response = client.put(f"/chat-rooms/{room_id}", json={
        "name": "Hacked Room"
    }, headers=headers2)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA ELIMINAR SALAS
# ============================================================================

def test_delete_chat_room(client, db_session):
    """Test eliminar sala de chat con JWT (requiere ser participante)"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Crear sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Room to Delete",
        "is_group": True
    }, headers=headers)
    room_id = create_response.json()["id"]

    # Eliminar sala
    response = client.delete(f"/chat-rooms/{room_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que la sala ya no existe
    get_response = client.get(f"/chat-rooms/{room_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_chat_room_forbidden_not_participant(client, db_session):
    """Test que un no participante no puede eliminar una sala con JWT"""
    # Crear dos usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    headers2 = get_auth_headers(login_data2["access_token"])

    # User1 crea una sala
    create_response = client.post("/chat-rooms/", json={
        "name": "Protected Room",
        "is_group": False
    }, headers=headers1)
    room_id = create_response.json()["id"]

    # User2 intenta eliminar (no es participante)
    response = client.delete(f"/chat-rooms/{room_id}", headers=headers2)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a participant" in response.json()["detail"]

# ============================================================================
# TESTS PARA OBTENER SALAS DE UN USUARIO (MY ROOMS)
# ============================================================================

def test_get_my_rooms(client, db_session):
    """Test obtener salas donde el usuario autenticado es participante con JWT"""
    # Crear usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    headers2 = get_auth_headers(login_data2["access_token"])

    # User1 crea dos salas
    room1_response = client.post("/chat-rooms/", json={
        "name": "Room 1",
        "is_group": True
    }, headers=headers1)
    room1_id = room1_response.json()["id"]

    room2_response = client.post("/chat-rooms/", json={
        "name": "Room 2",
        "is_group": False
    }, headers=headers1)
    room2_id = room2_response.json()["id"]

    # User2 crea una sala
    room3_response = client.post("/chat-rooms/", json={
        "name": "Room 3",
        "is_group": True
    }, headers=headers2)
    room3_id = room3_response.json()["id"]

    # User2 agrega a user1 a room3
    user1_id = login_data1["user"]["id"]
    client.post(f"/chat-rooms/{room3_id}/participants?user_id={user1_id}", headers=headers2)

    # Obtener salas de user1 (debe tener room1, room2, y room3)
    response = client.get("/chat-rooms/my-rooms", headers=headers1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    room_ids = [room["id"] for room in data]
    assert room1_id in room_ids
    assert room2_id in room_ids
    assert room3_id in room_ids

def test_get_my_rooms_without_jwt(client):
    """Test obtener mis salas sin JWT debe fallar con 403"""
    response = client.get("/chat-rooms/my-rooms")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_my_rooms_empty(client, db_session):
    """Test obtener salas cuando el usuario autenticado no tiene ninguna con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "newuser", "new@example.com", "password123")
    login_data = login_user(client, "newuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    # Obtener salas (debe estar vacío)
    response = client.get("/chat-rooms/my-rooms", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

# ============================================================================
# TESTS PARA GESTIÓN DE PARTICIPANTES
# ============================================================================

def test_add_participant_to_room(client, db_session):
    """Test agregar un participante a una sala con JWT"""
    # Crear usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    user2_id = login_data2["user"]["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    }, headers=headers1)
    room_id = room_response.json()["id"]

    # User1 agrega a user2 a la sala
    response = client.post(f"/chat-rooms/{room_id}/participants?user_id={user2_id}", headers=headers1)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["room_id"] == room_id
    assert data["user_id"] == user2_id
    assert "joined_at" in data

def test_add_participant_room_not_found(client, db_session):
    """Test agregar participante a sala inexistente con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])
    user_id = login_data["user"]["id"]

    response = client.post(f"/chat-rooms/999/participants?user_id={user_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]

def test_add_participant_user_not_found(client, db_session):
    """Test agregar usuario inexistente a una sala con JWT"""
    # Crear usuario y sala
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    response = client.post(f"/chat-rooms/{room_id}/participants?user_id=999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]

def test_add_participant_already_member(client, db_session):
    """Test agregar participante que ya es miembro con JWT"""
    # Crear usuario y sala
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])
    user_id = login_data["user"]["id"]

    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": True
    }, headers=headers)
    room_id = room_response.json()["id"]

    # Intentar agregar nuevamente al creador (ya es participante automáticamente)
    response = client.post(f"/chat-rooms/{room_id}/participants?user_id={user_id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already a participant" in response.json()["detail"]

def test_remove_participant_from_room(client, db_session):
    """Test remover un participante de una sala con JWT"""
    # Crear usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    headers2 = get_auth_headers(login_data2["access_token"])
    user2_id = login_data2["user"]["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    }, headers=headers1)
    room_id = room_response.json()["id"]

    # User1 agrega a user2
    client.post(f"/chat-rooms/{room_id}/participants?user_id={user2_id}", headers=headers1)

    # User1 remueve a user2
    response = client.delete(f"/chat-rooms/{room_id}/participants/{user2_id}", headers=headers1)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que user2 ya no puede acceder a la sala
    get_response = client.get(f"/chat-rooms/{room_id}", headers=headers2)
    assert get_response.status_code == status.HTTP_403_FORBIDDEN

def test_remove_participant_not_found(client, db_session):
    """Test remover participante que no existe en la sala con JWT"""
    # Crear usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    user2_id = login_data2["user"]["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    }, headers=headers1)
    room_id = room_response.json()["id"]

    # Intentar remover user2 (no es participante)
    response = client.delete(f"/chat-rooms/{room_id}/participants/{user2_id}", headers=headers1)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Participant not found" in response.json()["detail"]

def test_get_room_participants(client, db_session):
    """Test obtener lista de participantes de una sala con JWT"""
    # Crear usuarios
    create_test_user(client, "user1", "user1@example.com", "password123")
    login_data1 = login_user(client, "user1", "password123")
    headers1 = get_auth_headers(login_data1["access_token"])
    user1_id = login_data1["user"]["id"]

    create_test_user(client, "user2", "user2@example.com", "password123")
    login_data2 = login_user(client, "user2", "password123")
    user2_id = login_data2["user"]["id"]

    create_test_user(client, "user3", "user3@example.com", "password123")
    login_data3 = login_user(client, "user3", "password123")
    user3_id = login_data3["user"]["id"]

    # User1 crea una sala
    room_response = client.post("/chat-rooms/", json={
        "name": "Group Room",
        "is_group": True
    }, headers=headers1)
    room_id = room_response.json()["id"]

    # User1 agrega a user2 y user3
    client.post(f"/chat-rooms/{room_id}/participants?user_id={user2_id}", headers=headers1)
    client.post(f"/chat-rooms/{room_id}/participants?user_id={user3_id}", headers=headers1)

    # Obtener participantes
    response = client.get(f"/chat-rooms/{room_id}/participants", headers=headers1)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    participant_user_ids = [p["user_id"] for p in data]
    assert user1_id in participant_user_ids
    assert user2_id in participant_user_ids
    assert user3_id in participant_user_ids

def test_get_room_participants_room_not_found(client):
    """Test obtener participantes de sala inexistente con JWT"""
    # Crear usuario y hacer login
    create_test_user(client, "testuser", "test@example.com", "password123")
    login_data = login_user(client, "testuser", "password123")
    headers = get_auth_headers(login_data["access_token"])

    response = client.get("/chat-rooms/999/participants", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Chat room not found" in response.json()["detail"]
