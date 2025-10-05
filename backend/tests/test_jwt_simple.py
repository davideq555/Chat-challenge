"""Test simple para verificar que JWT funcione"""
from tests.conftest import create_test_user, login_user, get_auth_headers


def test_jwt_authentication_works(client, db_session):
    """
    Test simple para verificar que:
    1. Se puede crear un usuario
    2. Se puede hacer login y obtener token
    3. Se puede usar el token para acceder a un endpoint protegido
    """
    # 1. Crear usuario
    print("\n1. Creando usuario...")
    user_data = create_test_user(client, "testuser", "test@example.com", "password123")
    print(f"   Usuario creado: {user_data['username']} (ID: {user_data['id']})")

    # 2. Login
    print("\n2. Haciendo login...")
    login_data = login_user(client, "testuser", "password123")
    token = login_data["access_token"]
    print(f"   Token obtenido: {token[:50]}...")
    print(f"   User ID en respuesta: {login_data['user']['id']}")

    # 3. Usar token para crear sala
    print("\n3. Creando sala con JWT...")
    headers = get_auth_headers(token)
    print(f"   Headers: {headers}")

    response = client.post("/chat-rooms/", json={
        "name": "Test Room",
        "is_group": False
    }, headers=headers)

    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    room_data = response.json()
    print(f"   Sala creada: {room_data['name']} (ID: {room_data['id']})")
