import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="function")
def client():
    """Fixture que proporciona un cliente de prueba para cada test"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function", autouse=True)
def reset_databases():
    """Limpia las bases de datos en memoria antes de cada test"""
    from app.routers import users, chat_rooms, messages, attachments

    # Resetear todas las bases de datos en memoria
    users.users_db.clear()
    users.user_id_counter = {"value": 0}

    chat_rooms.chat_rooms_db.clear()
    chat_rooms.room_id_counter = {"value": 0}

    messages.messages_db.clear()
    messages.message_id_counter = {"value": 0}

    attachments.attachments_db.clear()
    attachments.attachment_id_counter = {"value": 0}

    yield
