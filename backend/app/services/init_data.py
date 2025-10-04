"""
Servicio de inicialización de datos
Crea usuarios y salas por defecto al iniciar la aplicación
"""

import hashlib
import logging
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat_room import ChatRoom
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash simple de password (mismo método que en users.py)"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_default_data():
    """
    Inicializar datos por defecto:
    - Usuario bot de bienvenida
    - Usuario de prueba
    - Sala de bienvenida
    """
    db: Session = SessionLocal()

    try:
        logger.info("🚀 Inicializando datos por defecto...")

        # 1. Crear usuario bot de bienvenida
        bot_user = db.query(User).filter(User.username == "WelcomeBot").first()
        if not bot_user:
            bot_user = User(
                username="WelcomeBot",
                email="bot@chatapp.com",
                password_hash=hash_password("bot_password_secret_2025")
            )
            db.add(bot_user)
            db.commit()
            db.refresh(bot_user)
            logger.info(f"✅ Usuario bot creado: {bot_user.username} (ID: {bot_user.id})")
        else:
            logger.info(f"ℹ️  Usuario bot ya existe: {bot_user.username} (ID: {bot_user.id})")

        # 2. Crear usuario de prueba
        test_user = db.query(User).filter(User.username == "TestUser").first()
        if not test_user:
            test_user = User(
                username="TestUser",
                email="test@example.com",
                password_hash=hash_password("pass1234")
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info(f"✅ Usuario de prueba creado: {test_user.username} (ID: {test_user.id})")
        else:
            logger.info(f"ℹ️  Usuario de prueba ya existe: {test_user.username} (ID: {test_user.id})")

        # 3. Crear sala de bienvenida
        welcome_room = db.query(ChatRoom).filter(ChatRoom.name == "Bienvenida").first()
        if not welcome_room:
            welcome_room = ChatRoom(
                name="Bienvenida",
                is_group=True  # Sala pública de bienvenida
            )
            db.add(welcome_room)
            db.commit()
            db.refresh(welcome_room)
            logger.info(f"✅ Sala de bienvenida creada: {welcome_room.name} (ID: {welcome_room.id})")
        else:
            logger.info(f"ℹ️  Sala de bienvenida ya existe: {welcome_room.name} (ID: {welcome_room.id})")

        logger.info("✅ Datos por defecto inicializados correctamente")
        logger.info(f"   Bot ID: {bot_user.id}, User ID: {test_user.id}, Room ID: {welcome_room.id}")

    except Exception as e:
        logger.error(f"❌ Error inicializando datos por defecto: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
