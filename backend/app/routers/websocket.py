from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from app.websockets.manager import manager
from app.websockets.events import EventType, create_event
from app.models.message import Message
from app.models.user import User
from app.database import get_db
from app.services.message_cache import message_cache
from app.auth.jwt import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(..., description="JWT token de autenticación")
):
    """
    WebSocket endpoint para chat en tiempo real (requiere JWT)

    Args:
        room_id: ID de la sala de chat
        token: JWT token de autenticación

    Uso:
        ws://localhost:8000/ws/{room_id}?token=YOUR_JWT_TOKEN

    Eventos que se pueden enviar:
        - message: Enviar mensaje
        - typing: Indicar que está escribiendo
        - ping: Verificar conexión

    Eventos que se reciben:
        - message_sent: Confirmación de mensaje enviado
        - message: Nuevo mensaje de otro usuario
        - user_joined: Usuario se unió a la sala
        - user_left: Usuario salió de la sala
        - typing: Alguien está escribiendo
        - connected: Confirmación de conexión
        - error: Error en el servidor
    """
    connection_id = None
    db = None

    # Obtener sesión de BD
    from app.database import SessionLocal
    db = SessionLocal()

    # Verificar token JWT
    token_data = verify_token(token)
    if token_data is None or token_data.user_id is None:
        logger.warning(f"❌ Token JWT inválido para room={room_id}")
        await websocket.close(code=1008, reason="Invalid token")
        db.close()
        return

    try:
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            logger.warning(f"❌ Usuario no encontrado: user_id={token_data.user_id}")
            await websocket.close(code=1008, reason="User not found")
            db.close()
            return

        user_id = user.id
        username = user.username

        # Conectar al manager
        connection_id = await manager.connect(websocket, room_id, user_id, username)
        logger.info(f"🔌 WebSocket conectado: user={username}, room={room_id}")

        # Escuchar mensajes del cliente
        while True:
            # Recibir mensaje del cliente
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    create_event(
                        EventType.ERROR,
                        message="Formato de mensaje inválido (debe ser JSON)"
                    ),
                    websocket
                )
                continue

            # Procesar según tipo de evento
            event_type = message_data.get("type")

            if event_type == "message":
                # Guardar mensaje en DB
                await handle_new_message(
                    room_id=room_id,
                    user_id=user_id,
                    username=username,
                    content=message_data.get("content", ""),
                    websocket=websocket
                )

            elif event_type == "typing":
                # Broadcast typing indicator
                await manager.broadcast(
                    room_id,
                    create_event(
                        EventType.TYPING,
                        user_id=user_id,
                        username=username,
                        is_typing=message_data.get("is_typing", True)
                    ),
                    exclude_connection_id=connection_id
                )

            elif event_type == "ping":
                # Responder con pong
                await manager.send_personal_message(
                    create_event(EventType.PONG),
                    websocket
                )

            else:
                # Tipo de evento desconocido
                await manager.send_personal_message(
                    create_event(
                        EventType.ERROR,
                        message=f"Tipo de evento desconocido: {event_type}"
                    ),
                    websocket
                )

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado: user={username}, room={room_id}")

    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}", exc_info=True)

    finally:
        # Desconectar del manager
        if connection_id:
            await manager.disconnect(room_id, connection_id)

        # Cerrar sesión de BD
        if db:
            db.close()

async def handle_new_message(
    room_id: int,
    user_id: int,
    username: str,
    content: str,
    websocket: WebSocket
):
    """
    Manejar nuevo mensaje: guardar en DB y hacer broadcast

    Args:
        room_id: ID de la sala
        user_id: ID del usuario
        username: Nombre del usuario
        content: Contenido del mensaje
        websocket: WebSocket del usuario
    """
    try:
        # TODO: Obtener sesión de DB de forma correcta
        # Por ahora creamos una conexión directa
        from app.database import SessionLocal
        db = SessionLocal()

        try:
            # Crear mensaje en DB
            message = Message(
                room_id=room_id,
                user_id=user_id,
                content=content,
                is_deleted=False
            )

            db.add(message)
            db.commit()
            db.refresh(message)

            # Preparar datos del mensaje
            message_dict = {
                "id": message.id,
                "room_id": message.room_id,
                "user_id": message.user_id,
                "username": username,  # Agregamos username para el frontend
                "content": message.content,
                "created_at": message.created_at.isoformat(),
                "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                "is_deleted": message.is_deleted
            }

            # Cachear mensaje en Redis
            try:
                message_cache.cache_message(room_id, message_dict)
            except Exception as cache_error:
                logger.warning(f"No se pudo cachear mensaje: {cache_error}")

            # Enviar confirmación al emisor
            await manager.send_personal_message(
                create_event(
                    EventType.MESSAGE_SENT,
                    message_id=message.id,
                    timestamp=message.created_at.isoformat()
                ),
                websocket
            )

            # Broadcast a toda la sala (incluyendo al emisor)
            await manager.broadcast(
                room_id,
                create_event(
                    EventType.MESSAGE,
                    **message_dict
                )
            )

            logger.info(f"💬 Mensaje guardado y enviado: room={room_id}, user={username}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error guardando mensaje: {e}", exc_info=True)
        await manager.send_personal_message(
            create_event(
                EventType.ERROR,
                message="Error guardando mensaje",
                details=str(e)
            ),
            websocket
        )

@router.get("/stats")
async def get_websocket_stats():
    """
    Obtener estadísticas de conexiones WebSocket

    Returns:
        Estadísticas de conexiones activas
    """
    return manager.get_stats()
