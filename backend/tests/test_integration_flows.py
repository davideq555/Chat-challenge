"""
Tests de Integración - Flujos Completos E2E
Prueba flujos de trabajo completos de usuarios reales
"""
import pytest
from fastapi import status
from tests.conftest import create_test_user, login_user, get_auth_headers


# ============================================================================
# FLUJO 1: Registro → Login → Crear Sala → Enviar Mensaje
# ============================================================================

def test_complete_chat_flow(client, db_session):
    """
    Flujo completo de usuario nuevo:
    1. Registrar usuario
    2. Login y obtener JWT
    3. Crear sala de chat
    4. Enviar mensaje
    5. Leer mensajes
    """
    # 1. Registrar usuario
    user_response = client.post("/users/", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "securepass123"
    })
    assert user_response.status_code == status.HTTP_201_CREATED
    assert user_response.json()["username"] == "alice"

    # 2. Login y obtener JWT
    login_response = client.post("/users/login", json={
        "username": "alice",
        "password": "securepass123"
    })
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    assert "access_token" in token_data
    headers = get_auth_headers(token_data["access_token"])

    # 3. Crear sala de chat
    room_response = client.post("/chat-rooms/", json={
        "name": "Mi Primera Sala",
        "is_group": False
    }, headers=headers)
    assert room_response.status_code == status.HTTP_201_CREATED
    room = room_response.json()
    assert room["name"] == "Mi Primera Sala"
    room_id = room["id"]

    # 4. Enviar mensaje
    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "¡Hola mundo! Este es mi primer mensaje"
    }, headers=headers)
    assert message_response.status_code == status.HTTP_201_CREATED
    message = message_response.json()
    assert message["content"] == "¡Hola mundo! Este es mi primer mensaje"
    assert message["is_deleted"] is False

    # 5. Leer mensajes de la sala
    messages_response = client.get(f"/messages/room/{room_id}/latest", headers=headers)
    assert messages_response.status_code == status.HTTP_200_OK
    messages = messages_response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "¡Hola mundo! Este es mi primer mensaje"


# ============================================================================
# FLUJO 2: Dos Usuarios Chatean en Sala Privada
# ============================================================================

def test_two_users_private_chat(client, db_session):
    """
    Flujo de chat privado entre dos usuarios:
    1. Crear alice y bob
    2. Alice crea sala privada
    3. Alice agrega a bob como participante
    4. Ambos intercambian mensajes
    5. Verificar que solo ellos ven los mensajes
    """
    # 1. Crear alice
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])
    alice_id = alice_login["user"]["id"]

    # 2. Crear bob
    create_test_user(client, "bob", "bob@example.com", "pass123")
    bob_login = login_user(client, "bob", "pass123")
    bob_headers = get_auth_headers(bob_login["access_token"])
    bob_id = bob_login["user"]["id"]

    # 3. Alice crea sala privada
    room_response = client.post("/chat-rooms/", json={
        "name": "Alice & Bob Chat",
        "is_group": False
    }, headers=alice_headers)
    assert room_response.status_code == status.HTTP_201_CREATED
    room_id = room_response.json()["id"]

    # 4. Alice agrega a bob
    add_participant_response = client.post(
        f"/chat-rooms/{room_id}/participants?user_id={bob_id}",
        headers=alice_headers
    )
    assert add_participant_response.status_code == status.HTTP_201_CREATED

    # 5. Alice envía mensaje
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "Hola Bob, ¿cómo estás?"
    }, headers=alice_headers)

    # 6. Bob responde
    client.post("/messages/", json={
        "room_id": room_id,
        "content": "¡Hola Alice! Todo bien, gracias"
    }, headers=bob_headers)

    # 7. Verificar que ambos ven los mensajes
    alice_messages = client.get(f"/messages/room/{room_id}/latest", headers=alice_headers)
    bob_messages = client.get(f"/messages/room/{room_id}/latest", headers=bob_headers)

    assert alice_messages.status_code == status.HTTP_200_OK
    assert bob_messages.status_code == status.HTTP_200_OK
    assert len(alice_messages.json()) == 2
    assert len(bob_messages.json()) == 2

    # 8. Verificar participantes
    participants_response = client.get(f"/chat-rooms/{room_id}/participants", headers=alice_headers)
    assert participants_response.status_code == status.HTTP_200_OK
    participants = participants_response.json()
    assert len(participants) == 2
    participant_ids = [p["user_id"] for p in participants]
    assert alice_id in participant_ids
    assert bob_id in participant_ids


# ============================================================================
# FLUJO 3: Sala Grupal con Múltiples Usuarios
# ============================================================================

def test_group_chat_with_three_users(client, db_session):
    """
    Flujo de chat grupal:
    1. Alice crea sala grupal
    2. Alice agrega a bob y charlie
    3. Los 3 envían mensajes
    4. Charlie se sale de la sala
    5. Verificar que charlie ya no puede acceder
    """
    # 1. Crear usuarios
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])

    create_test_user(client, "bob", "bob@example.com", "pass123")
    bob_login = login_user(client, "bob", "pass123")
    bob_headers = get_auth_headers(bob_login["access_token"])
    bob_id = bob_login["user"]["id"]

    create_test_user(client, "charlie", "charlie@example.com", "pass123")
    charlie_login = login_user(client, "charlie", "pass123")
    charlie_headers = get_auth_headers(charlie_login["access_token"])
    charlie_id = charlie_login["user"]["id"]

    # 2. Alice crea sala grupal
    room_response = client.post("/chat-rooms/", json={
        "name": "Grupo de Amigos",
        "is_group": True
    }, headers=alice_headers)
    room_id = room_response.json()["id"]

    # 3. Alice agrega a bob y charlie
    client.post(f"/chat-rooms/{room_id}/participants?user_id={bob_id}", headers=alice_headers)
    client.post(f"/chat-rooms/{room_id}/participants?user_id={charlie_id}", headers=alice_headers)

    # 4. Los 3 envían mensajes
    client.post("/messages/", json={"room_id": room_id, "content": "Mensaje de Alice"}, headers=alice_headers)
    client.post("/messages/", json={"room_id": room_id, "content": "Mensaje de Bob"}, headers=bob_headers)
    client.post("/messages/", json={"room_id": room_id, "content": "Mensaje de Charlie"}, headers=charlie_headers)

    # 5. Verificar que hay 3 mensajes
    messages_response = client.get(f"/messages/room/{room_id}/latest", headers=alice_headers)
    assert len(messages_response.json()) == 3

    # 6. Charlie se sale de la sala
    remove_response = client.delete(
        f"/chat-rooms/{room_id}/participants/{charlie_id}",
        headers=charlie_headers
    )
    assert remove_response.status_code == status.HTTP_204_NO_CONTENT

    # 7. Verificar que charlie ya no puede acceder
    charlie_access_response = client.get(f"/chat-rooms/{room_id}", headers=charlie_headers)
    assert charlie_access_response.status_code == status.HTTP_403_FORBIDDEN

    # 8. Verificar que solo quedan 2 participantes
    participants_response = client.get(f"/chat-rooms/{room_id}/participants", headers=alice_headers)
    assert len(participants_response.json()) == 2


# ============================================================================
# FLUJO 4: Operaciones de Mensajes (Editar, Eliminar, Restaurar)
# ============================================================================

def test_message_crud_operations(client, db_session):
    """
    Flujo completo de operaciones con mensajes:
    1. Usuario crea mensaje
    2. Edita el mensaje
    3. Soft delete (marca como eliminado)
    4. Restaura el mensaje
    5. Hard delete (elimina permanentemente)
    """
    # 1. Crear usuario y sala
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])

    room_response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": False
    }, headers=alice_headers)
    room_id = room_response.json()["id"]

    # 2. Crear mensaje original
    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Mensaje original"
    }, headers=alice_headers)
    message_id = message_response.json()["id"]

    # 3. Editar mensaje
    edit_response = client.put(f"/messages/{message_id}", json={
        "content": "Mensaje editado"
    }, headers=alice_headers)
    assert edit_response.status_code == status.HTTP_200_OK
    assert edit_response.json()["content"] == "Mensaje editado"
    assert edit_response.json()["updated_at"] is not None

    # 4. Soft delete
    soft_delete_response = client.delete(
        f"/messages/{message_id}?soft_delete=true",
        headers=alice_headers
    )
    assert soft_delete_response.status_code == status.HTTP_204_NO_CONTENT

    # 5. Verificar que está marcado como eliminado
    get_message_response = client.get(f"/messages/{message_id}", headers=alice_headers)
    assert get_message_response.json()["is_deleted"] is True

    # 6. Verificar que no aparece en listado por defecto
    messages_list = client.get(f"/messages/room/{room_id}/latest", headers=alice_headers)
    assert len(messages_list.json()) == 0

    # 7. Restaurar mensaje
    restore_response = client.post(f"/messages/{message_id}/restore", headers=alice_headers)
    assert restore_response.status_code == status.HTTP_200_OK
    assert restore_response.json()["is_deleted"] is False

    # 8. Verificar que vuelve a aparecer
    messages_list = client.get(f"/messages/room/{room_id}/latest", headers=alice_headers)
    assert len(messages_list.json()) == 1

    # 9. Hard delete
    hard_delete_response = client.delete(
        f"/messages/{message_id}?soft_delete=false",
        headers=alice_headers
    )
    assert hard_delete_response.status_code == status.HTTP_204_NO_CONTENT

    # 10. Verificar que ya no existe
    get_deleted_message = client.get(f"/messages/{message_id}", headers=alice_headers)
    assert get_deleted_message.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# FLUJO 5: Mensajes con Adjuntos
# ============================================================================

def test_messages_with_attachments(client, db_session):
    """
    Flujo de mensajes con archivos adjuntos:
    1. Crear mensaje
    2. Agregar 3 adjuntos (imagen, PDF, video)
    3. Listar adjuntos del mensaje
    4. Obtener estadísticas por tipo
    5. Eliminar un adjunto
    """
    # 1. Crear usuario y sala
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])

    room_response = client.post("/chat-rooms/", json={
        "name": "Compartir Archivos",
        "is_group": False
    }, headers=alice_headers)
    room_id = room_response.json()["id"]

    # 2. Crear mensaje
    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Aquí están los archivos del proyecto"
    }, headers=alice_headers)
    message_id = message_response.json()["id"]

    # 3. Agregar adjuntos
    attachments_data = [
        {"file_url": "https://example.com/diagram.png", "file_type": "image/png"},
        {"file_url": "https://example.com/report.pdf", "file_type": "application/pdf"},
        {"file_url": "https://example.com/demo.mp4", "file_type": "video/mp4"}
    ]

    attachment_ids = []
    for att_data in attachments_data:
        att_response = client.post("/attachments/", json={
            "message_id": message_id,
            **att_data
        }, headers=alice_headers)
        assert att_response.status_code == status.HTTP_201_CREATED
        attachment_ids.append(att_response.json()["id"])

    # 4. Listar adjuntos del mensaje
    attachments_list = client.get(f"/attachments/message/{message_id}/all", headers=alice_headers)
    assert attachments_list.status_code == status.HTTP_200_OK
    assert len(attachments_list.json()) == 3

    # 5. Contar adjuntos
    count_response = client.get(f"/attachments/message/{message_id}/count", headers=alice_headers)
    assert count_response.json()["attachment_count"] == 3

    # 6. Estadísticas por tipo
    stats_response = client.get("/attachments/stats/by-type", headers=alice_headers)
    stats = stats_response.json()
    assert stats["total_attachments"] == 3
    assert stats["by_type"]["image/png"] == 1
    assert stats["by_type"]["application/pdf"] == 1
    assert stats["by_type"]["video/mp4"] == 1

    # 7. Eliminar un adjunto
    delete_response = client.delete(f"/attachments/{attachment_ids[0]}", headers=alice_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # 8. Verificar que quedan 2
    count_response = client.get(f"/attachments/message/{message_id}/count", headers=alice_headers)
    assert count_response.json()["attachment_count"] == 2


# ============================================================================
# FLUJO 6: Seguridad y Control de Acceso
# ============================================================================

def test_security_access_control(client, db_session):
    """
    Flujo de seguridad y control de acceso:
    1. Alice crea sala privada
    2. Bob intenta acceder → 403 Forbidden
    3. Bob intenta enviar mensaje → 403 Forbidden
    4. Alice agrega a bob como participante
    5. Bob ahora puede acceder y enviar mensajes
    6. Charlie (no participante) no puede ver mensajes
    """
    # 1. Crear usuarios
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])

    create_test_user(client, "bob", "bob@example.com", "pass123")
    bob_login = login_user(client, "bob", "pass123")
    bob_headers = get_auth_headers(bob_login["access_token"])
    bob_id = bob_login["user"]["id"]

    create_test_user(client, "charlie", "charlie@example.com", "pass123")
    charlie_login = login_user(client, "charlie", "pass123")
    charlie_headers = get_auth_headers(charlie_login["access_token"])

    # 2. Alice crea sala privada
    room_response = client.post("/chat-rooms/", json={
        "name": "Sala Privada de Alice",
        "is_group": False
    }, headers=alice_headers)
    room_id = room_response.json()["id"]

    # 3. Alice envía mensaje
    message_response = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Mensaje privado"
    }, headers=alice_headers)
    message_id = message_response.json()["id"]

    # 4. Bob intenta acceder a la sala → FORBIDDEN
    bob_access_room = client.get(f"/chat-rooms/{room_id}", headers=bob_headers)
    assert bob_access_room.status_code == status.HTTP_403_FORBIDDEN

    # 5. Bob intenta ver mensajes → FORBIDDEN
    bob_access_messages = client.get(f"/messages/room/{room_id}/latest", headers=bob_headers)
    assert bob_access_messages.status_code == status.HTTP_403_FORBIDDEN

    # 6. Bob intenta enviar mensaje → FORBIDDEN
    bob_send_message = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Intento de mensaje"
    }, headers=bob_headers)
    assert bob_send_message.status_code == status.HTTP_403_FORBIDDEN

    # 7. Alice agrega a bob como participante
    add_bob_response = client.post(
        f"/chat-rooms/{room_id}/participants?user_id={bob_id}",
        headers=alice_headers
    )
    assert add_bob_response.status_code == status.HTTP_201_CREATED

    # 8. Ahora bob SÍ puede acceder
    bob_access_room_now = client.get(f"/chat-rooms/{room_id}", headers=bob_headers)
    assert bob_access_room_now.status_code == status.HTTP_200_OK

    # 9. Bob puede ver mensajes
    bob_see_messages = client.get(f"/messages/room/{room_id}/latest", headers=bob_headers)
    assert bob_see_messages.status_code == status.HTTP_200_OK
    assert len(bob_see_messages.json()) == 1

    # 10. Bob puede enviar mensaje
    bob_send_message_now = client.post("/messages/", json={
        "room_id": room_id,
        "content": "Ahora sí puedo escribir!"
    }, headers=bob_headers)
    assert bob_send_message_now.status_code == status.HTTP_201_CREATED

    # 11. Charlie (no participante) NO puede acceder
    charlie_access = client.get(f"/chat-rooms/{room_id}", headers=charlie_headers)
    assert charlie_access.status_code == status.HTTP_403_FORBIDDEN

    charlie_messages = client.get(f"/messages/room/{room_id}/latest", headers=charlie_headers)
    assert charlie_messages.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# FLUJO 7: Gestión de Salas del Usuario
# ============================================================================

def test_user_rooms_management(client, db_session):
    """
    Flujo de gestión de salas de un usuario:
    1. Alice crea 2 salas
    2. Bob crea 1 sala y agrega a alice
    3. Alice obtiene "mis salas" → debe tener 3
    4. Alice se sale de la sala de bob
    5. Alice obtiene "mis salas" → debe tener 2
    """
    # 1. Crear usuarios
    create_test_user(client, "alice", "alice@example.com", "pass123")
    alice_login = login_user(client, "alice", "pass123")
    alice_headers = get_auth_headers(alice_login["access_token"])
    alice_id = alice_login["user"]["id"]

    create_test_user(client, "bob", "bob@example.com", "pass123")
    bob_login = login_user(client, "bob", "pass123")
    bob_headers = get_auth_headers(bob_login["access_token"])

    # 2. Alice crea 2 salas
    client.post("/chat-rooms/", json={"name": "Sala 1 de Alice", "is_group": False}, headers=alice_headers)
    client.post("/chat-rooms/", json={"name": "Sala 2 de Alice", "is_group": True}, headers=alice_headers)

    # 3. Bob crea 1 sala
    bob_room_response = client.post("/chat-rooms/", json={
        "name": "Sala de Bob",
        "is_group": True
    }, headers=bob_headers)
    bob_room_id = bob_room_response.json()["id"]

    # 4. Bob agrega a alice
    client.post(f"/chat-rooms/{bob_room_id}/participants?user_id={alice_id}", headers=bob_headers)

    # 5. Alice obtiene sus salas → debe tener 3
    alice_rooms_response = client.get("/chat-rooms/my-rooms", headers=alice_headers)
    assert alice_rooms_response.status_code == status.HTTP_200_OK
    alice_rooms = alice_rooms_response.json()
    assert len(alice_rooms) == 3
    room_names = [room["name"] for room in alice_rooms]
    assert "Sala 1 de Alice" in room_names
    assert "Sala 2 de Alice" in room_names
    assert "Sala de Bob" in room_names

    # 6. Alice se sale de la sala de bob
    remove_response = client.delete(
        f"/chat-rooms/{bob_room_id}/participants/{alice_id}",
        headers=alice_headers
    )
    assert remove_response.status_code == status.HTTP_204_NO_CONTENT

    # 7. Alice obtiene sus salas → debe tener 2
    alice_rooms_response = client.get("/chat-rooms/my-rooms", headers=alice_headers)
    assert len(alice_rooms_response.json()) == 2
