import pytest
from fastapi import status

def test_create_user(client):
    """Test crear un nuevo usuario"""
    response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data
    assert "password_hash" not in data
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

def test_create_user_duplicate_username(client):
    """Test que no se puede crear usuario con username duplicado"""
    user_data = {
        "username": "testuser",
        "email": "test1@example.com",
        "password": "password123"
    }
    client.post("/users/", json=user_data)

    # Intentar crear con mismo username pero diferente email
    response = client.post("/users/", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already exists" in response.json()["detail"]

def test_create_user_duplicate_email(client):
    """Test que no se puede crear usuario con email duplicado"""
    user_data = {
        "username": "testuser1",
        "email": "test@example.com",
        "password": "password123"
    }
    client.post("/users/", json=user_data)

    # Intentar crear con diferente username pero mismo email
    response = client.post("/users/", json={
        "username": "testuser2",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already exists" in response.json()["detail"]

def test_get_users(client):
    """Test obtener lista de usuarios"""
    # Crear algunos usuarios
    client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })

    response = client.get("/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["username"] == "user1"
    assert data[1]["username"] == "user2"

def test_get_user_by_id(client):
    """Test obtener usuario por ID"""
    create_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "testuser"

def test_get_user_not_found(client):
    """Test obtener usuario que no existe"""
    response = client.get("/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]

def test_update_user(client):
    """Test actualizar usuario"""
    create_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = create_response.json()["id"]

    response = client.put(f"/users/{user_id}", json={
        "username": "updateduser",
        "email": "updated@example.com"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "updated@example.com"

def test_update_user_not_found(client):
    """Test actualizar usuario que no existe"""
    response = client.put("/users/999", json={
        "username": "updateduser"
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_user_duplicate_username(client):
    """Test que no se puede actualizar a un username ya existente"""
    client.post("/users/", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    create_response = client.post("/users/", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123"
    })
    user_id = create_response.json()["id"]

    response = client.put(f"/users/{user_id}", json={
        "username": "user1"
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already exists" in response.json()["detail"]

def test_delete_user(client):
    """Test eliminar usuario"""
    create_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = create_response.json()["id"]

    response = client.delete(f"/users/{user_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que el usuario ya no existe
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_not_found(client):
    """Test eliminar usuario que no existe"""
    response = client.delete("/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_login_success(client):
    """Test login exitoso con JWT"""
    client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Validar estructura del token JWT
    assert "access_token" in data
    assert "token_type" in data
    assert "user" in data
    assert data["token_type"] == "bearer"

    # Validar datos del usuario
    assert data["user"]["username"] == "testuser"
    assert "last_login" in data["user"]

def test_login_with_email(client):
    """Test login usando email en lugar de username con JWT"""
    client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    response = client.post("/users/login", json={
        "username": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Validar JWT
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"

def test_login_invalid_credentials(client):
    """Test login con credenciales incorrectas"""
    client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid credentials" in response.json()["detail"]

def test_login_inactive_user(client):
    """Test login con usuario inactivo"""
    create_response = client.post("/users/", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    user_id = create_response.json()["id"]

    # Desactivar usuario
    client.put(f"/users/{user_id}", json={"is_active": False})

    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Account is inactive" in response.json()["detail"]
