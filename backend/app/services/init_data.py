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
from app.models.contact import Contact
from app.models.message import Message
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
                password_hash=hash_password("bot_password_secret_2025"),
                is_public=True
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
                password_hash=hash_password("pass1234"),
                is_public=True
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
                password_hash=hash_password("pass1234"),
                is_public=True
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

        # 4b. Agregar mensaje de bienvenida enviado por el bot hacia la sala de bienvenida
        try:
            welcome_text = (
                "¡Bienvenido/a! Soy el asistente de la aplicación. "
                "Aquí puedes: crear conversaciones, gestionar tus contactos, enviar archivos y ajustar tu visibilidad. "
                "Escribe un mensaje para comenzar. ¡Disfruta!"
            )
            # Evitar duplicados: si el bot ya envió un mensaje que contiene 'Bienvenido', no volver a agregar
            existing_welcome = db.query(Message).filter(
                Message.room_id == welcome_room.id,
                Message.user_id == bot_user.id
            ).first()

            if not existing_welcome:
                welcome_msg = Message(
                    room_id=welcome_room.id,
                    user_id=bot_user.id,
                    content=welcome_text
                )
                db.add(welcome_msg)
                logger.info("✅ Mensaje de bienvenida agregado a la sala de bienvenida")
            else:
                logger.info("ℹ️  Mensaje de bienvenida ya existe en la sala de bienvenida")
        except Exception as e:
            logger.error(f"❌ Error creando mensaje de bienvenida: {e}", exc_info=True)

        # 5. Crear contacto pendiente entre TestUser y TestUser2
        contact_1_to_2 = db.query(Contact).filter(
            Contact.user_id == test_user.id,
            Contact.contact_id == test_user2.id
        ).first()
        if not contact_1_to_2:
            contact_1_to_2 = Contact(
                user_id=test_user.id,
                contact_id=test_user2.id,
                status="pending"
            )
            db.add(contact_1_to_2)
            logger.info("✅ Solicitud de contacto creada: TestUser → TestUser2 (pending)")
        else:
            logger.info("ℹ️  Solicitud de contacto ya existe: TestUser → TestUser2")

        # 5b. Crear (si no existe) sala 1-a-1 entre TestUser y TestUser2 y añadir mensaje de bienvenida
        try:
            # Buscar rooms donde TestUser es participante
            rooms_user1 = db.query(RoomParticipant.room_id).filter(RoomParticipant.user_id == test_user.id).subquery()

            # Buscar una room 1-a-1 compartida con TestUser2
            existing_1to1 = db.query(ChatRoom).join(RoomParticipant, RoomParticipant.room_id == ChatRoom.id).filter(
                ChatRoom.id.in_(rooms_user1),
                ChatRoom.is_group.is_(False),
                RoomParticipant.user_id == test_user2.id
            ).first()

            if existing_1to1:
                room_1to1 = existing_1to1
                logger.info(f"ℹ️  Sala 1-a-1 ya existe entre TestUser y TestUser2 (ID: {room_1to1.id})")
            else:
                room_1to1 = ChatRoom(name=f"Chat {test_user.username} & {test_user2.username}", is_group=False)
                db.add(room_1to1)
                db.commit()
                db.refresh(room_1to1)
                logger.info(f"✅ Sala 1-a-1 creada entre TestUser y TestUser2 (ID: {room_1to1.id})")

                # Agregar participantes si no existen
                rp1 = db.query(RoomParticipant).filter(RoomParticipant.room_id == room_1to1.id, RoomParticipant.user_id == test_user.id).first()
                if not rp1:
                    db.add(RoomParticipant(room_id=room_1to1.id, user_id=test_user.id))
                rp2 = db.query(RoomParticipant).filter(RoomParticipant.room_id == room_1to1.id, RoomParticipant.user_id == test_user2.id).first()
                if not rp2:
                    db.add(RoomParticipant(room_id=room_1to1.id, user_id=test_user2.id))
                logger.info("✅ Participantes agregados a la sala 1-a-1 entre TestUser y TestUser2")

        except Exception as e:
            logger.error(f"❌ Error creando sala 1-a-1 o mensaje entre TestUser y TestUser2: {e}", exc_info=True)

        db.commit()

        logger.info("✅ Datos por defecto inicializados correctamente")
        logger.info(f"   Bot ID: {bot_user.id}, TestUser ID: {test_user.id}, TestUser2 ID: {test_user2.id}, Room ID: {welcome_room.id}")

    except Exception as e:
        logger.error(f"❌ Error inicializando datos por defecto: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
