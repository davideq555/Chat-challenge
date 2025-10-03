from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse
from app.models.message import Message
from app.database import get_db

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    """Crear un nuevo mensaje"""
    # TODO: Validar que room_id y user_id existan

    message = Message(
        room_id=message_data.room_id,
        user_id=message_data.user_id,
        content=message_data.content,
        is_deleted=False
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    room_id: int = Query(None, description="Filtrar por sala de chat"),
    user_id: int = Query(None, description="Filtrar por usuario"),
    include_deleted: bool = Query(False, description="Incluir mensajes eliminados"),
    db: Session = Depends(get_db)
):
    """
    Obtener mensajes con filtros opcionales

    - **room_id**: Filtrar por sala específica
    - **user_id**: Filtrar por autor
    - **include_deleted**: Incluir mensajes marcados como eliminados
    """
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
async def get_message(message_id: int, db: Session = Depends(get_db)):
    """Obtener un mensaje por ID"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: int, message_data: MessageUpdate, db: Session = Depends(get_db)):
    """Actualizar el contenido de un mensaje"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
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
    soft_delete: bool = Query(True, description="Soft delete (marcar como eliminado) o hard delete"),
    db: Session = Depends(get_db)
):
    """
    Eliminar un mensaje

    - **soft_delete=True**: Marca el mensaje como eliminado (por defecto)
    - **soft_delete=False**: Elimina permanentemente el mensaje
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
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
async def restore_message(message_id: int, db: Session = Depends(get_db)):
    """Restaurar un mensaje eliminado (soft delete)"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
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
    limit: int = Query(50, ge=1, le=100, description="Número de mensajes recientes"),
    db: Session = Depends(get_db)
):
    """Obtener los últimos N mensajes de una sala"""
    messages = db.query(Message).filter(
        Message.room_id == room_id,
        Message.is_deleted == False
    ).order_by(Message.created_at.desc()).limit(limit).all()

    return messages
