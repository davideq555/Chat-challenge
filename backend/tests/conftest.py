# Configurar variable de entorno para indicar que estamos en modo test
# IMPORTANTE: Esto debe estar ANTES de cualquier import de app
import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base

# Crear base de datos persistente para tests (SQLite)
# Usamos archivo persistente para que los datos existan entre peticiones HTTP
import tempfile
SQLALCHEMY_DATABASE_URL = f"sqlite:///{tempfile.gettempdir()}/test_chat.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None  # Sin pool para SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de base de datos para cada test"""
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Eliminar todas las tablas después del test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Fixture que proporciona un cliente de prueba para cada test"""

    # Limpiar caché de Redis antes de cada test
    try:
        from app.redis_client import redis_client
        redis_client.flushdb()
    except Exception:
        # Si Redis no está disponible, continuar sin error
        pass

    # Sobrescribir la dependency get_db para usar la DB de prueba
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override de get_current_user para tests
    async def override_get_current_user(credentials, db = None):
        from fastapi import HTTPException, status as http_status
        from app.models.user import User
        from app.auth.jwt import verify_token

        token = credentials.credentials
        token_data = verify_token(token)

        if token_data is None or token_data.user_id is None:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        # Usar la sesión de prueba
        user = db_session.query(User).filter(User.id == token_data.user_id).first()

        if user is None:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )

        return user

    from app.auth.dependencies import get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    # Limpiar overrides después del test
    app.dependency_overrides.clear()


# ============= Helper functions para JWT =============

def create_test_user(client, username="testuser", email="test@example.com", password="testpass123"):
    """
    Helper para crear un usuario de prueba con bcrypt

    Returns:
        dict: Respuesta del servidor con datos del usuario
    """
    response = client.post(
        "/users/",
        json={"username": username, "email": email, "password": password}
    )
    assert response.status_code == 201
    return response.json()


def login_user(client, username="testuser", password="testpass123"):
    """
    Helper para hacer login y obtener token JWT

    Returns:
        dict: {"access_token": str, "token_type": str, "user": dict}
    """
    response = client.post(
        "/users/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()


def get_auth_headers(token: str):
    """
    Helper para crear headers de autorización

    Args:
        token: Token JWT

    Returns:
        dict: Headers con Authorization Bearer
    """
    return {"Authorization": f"Bearer {token}"}
