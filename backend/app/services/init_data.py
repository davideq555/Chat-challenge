"""
Servicio de inicialización de datos
Crea usuarios y salas por defecto al iniciar la aplicación
"""

import logging
import os
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat_room import ChatRoom
from app.models.room_participant import RoomParticipant
from app.database import SessionLocal
from app.auth.password import hash_password

logger = logging.getLogger(__name__)


def init_default_data():
    """
    Inicializar datos por defecto:
    - Usuario bot de bienvenida
    - Usuario de prueba (TestUser)
    - Segundo usuario de prueba (TestUser2)
    - Sala de bienvenida (con todos los usuarios como participantes)
    """
    # No inicializar datos en modo test
    if os.getenv("TESTING") == "1":
        logger.info("⏩ Modo test detectado, saltando inicialización de datos por defecto")
        return

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

        # 2b. Crear segundo usuario de prueba
        test_user2 = db.query(User).filter(User.username == "TestUser2").first()
        if not test_user2:
            test_user2 = User(
                username="TestUser2",
                email="test2@example.com",
                password_hash=hash_password("pass1234")
            )
            db.add(test_user2)
            db.commit()
            db.refresh(test_user2)
            logger.info(f"✅ Segundo usuario de prueba creado: {test_user2.username} (ID: {test_user2.id})")
        else:
            logger.info(f"ℹ️  Segundo usuario de prueba ya existe: {test_user2.username} (ID: {test_user2.id})")

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

        # 4. Agregar usuarios como participantes de la sala de bienvenida
        # Agregar bot
        bot_participant = db.query(RoomParticipant).filter(
            RoomParticipant.room_id == welcome_room.id,
            RoomParticipant.user_id == bot_user.id
        ).first()
        if not bot_participant:
            bot_participant = RoomParticipant(
                room_id=welcome_room.id,
                user_id=bot_user.id
            )
            db.add(bot_participant)
            logger.info("✅ Bot agregado como participante de la sala de bienvenida")
        else:
            logger.info("ℹ️  Bot ya es participante de la sala de bienvenida")

        # Agregar test user
        test_participant = db.query(RoomParticipant).filter(
            RoomParticipant.room_id == welcome_room.id,
            RoomParticipant.user_id == test_user.id
        ).first()
        if not test_participant:
            test_participant = RoomParticipant(
                room_id=welcome_room.id,
                user_id=test_user.id
            )
            db.add(test_participant)
            logger.info("✅ TestUser agregado como participante de la sala de bienvenida")
        else:
            logger.info("ℹ️  TestUser ya es participante de la sala de bienvenida")

        # Agregar test user 2
        test_participant2 = db.query(RoomParticipant).filter(
            RoomParticipant.room_id == welcome_room.id,
            RoomParticipant.user_id == test_user2.id
        ).first()
        if not test_participant2:
            test_participant2 = RoomParticipant(
                room_id=welcome_room.id,
                user_id=test_user2.id
            )
            db.add(test_participant2)
            logger.info("✅ TestUser2 agregado como participante de la sala de bienvenida")
        else:
            logger.info("ℹ️  TestUser2 ya es participante de la sala de bienvenida")

        db.commit()

        logger.info("✅ Datos por defecto inicializados correctamente")
        logger.info(f"   Bot ID: {bot_user.id}, TestUser ID: {test_user.id}, TestUser2 ID: {test_user2.id}, Room ID: {welcome_room.id}")

    except Exception as e:
        logger.error(f"❌ Error inicializando datos por defecto: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
