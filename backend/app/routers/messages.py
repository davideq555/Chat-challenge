from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from datetime import datetime

from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse
from app.models.message import Message

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

# Almacenamiento temporal en memoria (luego se reemplazará con base de datos)
messages_db = {}
message_id_counter = {"value": 1}

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(message_data: MessageCreate):
    """Crear un nuevo mensaje"""
    # TODO: Validar que room_id y user_id existan (cuando tengamos BD)

    # Crear mensaje
    message = {
        "id": message_id_counter["value"],
        "room_id": message_data.room_id,
        "user_id": message_data.user_id,
        "content": message_data.content,
        "created_at": datetime.now(),
        "updated_at": None,
        "is_deleted": False
    }

    messages_db[message_id_counter["value"]] = message
    message_id_counter["value"] += 1

    return message

@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    room_id: int = Query(None, description="Filtrar por sala de chat"),
    user_id: int = Query(None, description="Filtrar por usuario"),
    include_deleted: bool = Query(False, description="Incluir mensajes eliminados")
):
    """
    Obtener mensajes con filtros opcionales

    - **room_id**: Filtrar por sala específica
    - **user_id**: Filtrar por autor
    - **include_deleted**: Incluir mensajes marcados como eliminados
    """
    messages = list(messages_db.values())

    # Aplicar filtros
    if room_id is not None:
        messages = [msg for msg in messages if msg["room_id"] == room_id]

    if user_id is not None:
        messages = [msg for msg in messages if msg["user_id"] == user_id]

    if not include_deleted:
        messages = [msg for msg in messages if not msg["is_deleted"]]

    # Ordenar por fecha de creación (más recientes primero)
    messages.sort(key=lambda x: x["created_at"], reverse=True)

    return messages

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int):
    """Obtener un mensaje por ID"""
    message = messages_db.get(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: int, message_data: MessageUpdate):
    """Actualizar el contenido de un mensaje"""
    message = messages_db.get(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # No permitir editar mensajes eliminados
    if message["is_deleted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit deleted message"
        )

    # Actualizar contenido y timestamp
    message["content"] = message_data.content
    message["updated_at"] = datetime.now()

    return message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: int, soft_delete: bool = Query(True, description="Soft delete (marcar como eliminado) o hard delete")):
    """
    Eliminar un mensaje

    - **soft_delete=True**: Marca el mensaje como eliminado (por defecto)
    - **soft_delete=False**: Elimina permanentemente el mensaje
    """
    message = messages_db.get(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    if soft_delete:
        # Soft delete: marcar como eliminado
        message["is_deleted"] = True
        message["updated_at"] = datetime.now()
    else:
        # Hard delete: eliminar completamente
        del messages_db[message_id]

@router.post("/{message_id}/restore", response_model=MessageResponse)
async def restore_message(message_id: int):
    """Restaurar un mensaje eliminado (soft delete)"""
    message = messages_db.get(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    if not message["is_deleted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is not deleted"
        )

    message["is_deleted"] = False
    message["updated_at"] = datetime.now()

    return message

@router.get("/room/{room_id}/latest", response_model=List[MessageResponse])
async def get_latest_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número de mensajes recientes")
):
    """Obtener los últimos N mensajes de una sala"""
    messages = [
        msg for msg in messages_db.values()
        if msg["room_id"] == room_id and not msg["is_deleted"]
    ]

    # Ordenar por fecha descendente y limitar
    messages.sort(key=lambda x: x["created_at"], reverse=True)
    messages = messages[:limit]

    return messages
