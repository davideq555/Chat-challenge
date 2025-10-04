from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse
from app.models.message import Message
from app.models.room_participant import RoomParticipant
from app.models.chat_room import ChatRoom
from app.database import get_db
from app.services.message_cache import message_cache

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo mensaje (VALIDACIÓN DE ACCESO)

    El usuario debe ser participante de la sala para enviar mensajes
    """
    # Validar que la sala existe
    room = db.query(ChatRoom).filter(ChatRoom.id == message_data.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Validar que el usuario es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == message_data.room_id,
        RoomParticipant.user_id == message_data.user_id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    message = Message(
        room_id=message_data.room_id,
        user_id=message_data.user_id,
        content=message_data.content,
        is_deleted=False
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # Cachear mensaje en Redis
    try:
        message_dict = {
            "id": message.id,
            "room_id": message.room_id,
            "user_id": message.user_id,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
            "is_deleted": message.is_deleted
        }
        message_cache.cache_message(message.room_id, message_dict)
    except Exception as e:
        logger.warning(f"No se pudo cachear mensaje {message.id}: {e}")
        # No fallar la request si falla el caché

    return message

@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    room_id: int = Query(None, description="Filtrar por sala de chat"),
    user_id: int = Query(None, description="Filtrar por usuario"),
    requesting_user_id: int = Query(..., description="ID del usuario que solicita (REQUERIDO para validación)"),
    include_deleted: bool = Query(False, description="Incluir mensajes eliminados"),
    db: Session = Depends(get_db)
):
    """
    Obtener mensajes con filtros opcionales (VALIDACIÓN DE ACCESO)

    - **room_id**: Filtrar por sala específica
    - **user_id**: Filtrar por autor
    - **requesting_user_id**: Usuario que solicita (para validar acceso)
    - **include_deleted**: Incluir mensajes marcados como eliminados
    """
    # Si se filtra por room_id, validar que el usuario es participante
    if room_id is not None:
        is_participant = db.query(RoomParticipant).filter(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == requesting_user_id
        ).first()

        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant of this chat room"
            )

    query = db.query(Message)

    # Aplicar filtros
    if room_id is not None:
        query = query.filter(Message.room_id == room_id)

    if user_id is not None:
        query = query.filter(Message.user_id == user_id)

    if not include_deleted:
        query = query.filter(Message.is_deleted == False)

    # Ordenar por fecha de creación (más recientes primero)
    query = query.order_by(Message.created_at.desc())

    return query.all()

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int, requesting_user_id: int, db: Session = Depends(get_db)):
    """
    Obtener un mensaje por ID (VALIDACIÓN DE ACCESO)

    - **message_id**: ID del mensaje
    - **requesting_user_id**: ID del usuario que solicita (query parameter)
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es participante de la sala del mensaje
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == message.room_id,
        RoomParticipant.user_id == requesting_user_id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    return message

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: int, message_data: MessageUpdate, requesting_user_id: int, db: Session = Depends(get_db)):
    """
    Actualizar el contenido de un mensaje (VALIDACIÓN DE ACCESO)

    - **message_id**: ID del mensaje
    - **message_data**: Nuevo contenido
    - **requesting_user_id**: ID del usuario que solicita (query parameter)
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )

    # No permitir editar mensajes eliminados
    if message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit deleted message"
        )

    # Actualizar contenido y timestamp
    message.content = message_data.content
    message.updated_at = datetime.now()

    db.commit()
    db.refresh(message)

    return message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    requesting_user_id: int,
    soft_delete: bool = Query(True, description="Soft delete (marcar como eliminado) o hard delete"),
    db: Session = Depends(get_db)
):
    """
    Eliminar un mensaje (VALIDACIÓN DE ACCESO)

    - **message_id**: ID del mensaje
    - **requesting_user_id**: ID del usuario que solicita (query parameter)
    - **soft_delete=True**: Marca el mensaje como eliminado (por defecto)
    - **soft_delete=False**: Elimina permanentemente el mensaje
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )

    if soft_delete:
        # Soft delete: marcar como eliminado
        message.is_deleted = True
        message.updated_at = datetime.now()
        db.commit()
    else:
        # Hard delete: eliminar completamente
        db.delete(message)
        db.commit()

@router.post("/{message_id}/restore", response_model=MessageResponse)
async def restore_message(message_id: int, requesting_user_id: int, db: Session = Depends(get_db)):
    """
    Restaurar un mensaje eliminado (VALIDACIÓN DE ACCESO)

    - **message_id**: ID del mensaje
    - **requesting_user_id**: ID del usuario que solicita (query parameter)
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only restore your own messages"
        )

    if not message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is not deleted"
        )

    message.is_deleted = False
    message.updated_at = datetime.now()

    db.commit()
    db.refresh(message)

    return message

@router.get("/room/{room_id}/latest", response_model=List[MessageResponse])
async def get_latest_messages(
    room_id: int,
    requesting_user_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número de mensajes recientes"),
    db: Session = Depends(get_db)
):
    """
    Obtener los últimos N mensajes de una sala (VALIDACIÓN DE ACCESO)

    - **room_id**: ID de la sala
    - **requesting_user_id**: ID del usuario que solicita (query parameter)
    - **limit**: Número de mensajes a obtener

    Usa caché Redis para mejor rendimiento. Si no hay caché,
    consulta la DB y actualiza el caché.
    """
    # Validar que el usuario es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == requesting_user_id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    # Intentar obtener del caché
    try:
        cached_messages = message_cache.get_cached_messages(room_id, limit)
        if cached_messages is not None:
            logger.info(f"✅ Mensajes obtenidos del caché para sala {room_id}")
            return cached_messages
    except Exception as e:
        logger.warning(f"Error leyendo caché: {e}, consultando DB...")

    # Si no hay caché, consultar DB
    messages = db.query(Message).filter(
        Message.room_id == room_id,
        Message.is_deleted == False
    ).order_by(Message.created_at.desc()).limit(limit).all()

    # Actualizar caché con resultados de la DB
    try:
        messages_dict = [
            {
                "id": msg.id,
                "room_id": msg.room_id,
                "user_id": msg.user_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "updated_at": msg.updated_at.isoformat() if msg.updated_at else None,
                "is_deleted": msg.is_deleted
            }
            for msg in messages
        ]
        message_cache.update_cache_with_db_messages(room_id, messages_dict)
    except Exception as e:
        logger.warning(f"No se pudo actualizar caché: {e}")

    return messages
