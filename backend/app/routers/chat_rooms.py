from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from app.schemas.chat_room import ChatRoomCreate, ChatRoomUpdate, ChatRoomResponse
from app.models.chat_room import ChatRoom

router = APIRouter(
    prefix="/chat-rooms",
    tags=["chat-rooms"]
)

# Almacenamiento temporal en memoria (luego se reemplazará con base de datos)
chat_rooms_db = {}
chat_room_id_counter = 1

@router.post("/", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(room_data: ChatRoomCreate):
    """Crear una nueva sala de chat"""
    global chat_room_id_counter

    # Crear sala de chat
    chat_room = ChatRoom(
        id=chat_room_id_counter,
        name=room_data.name,
        is_group=room_data.is_group,
        created_at=datetime.now()
    )

    chat_rooms_db[chat_room_id_counter] = chat_room
    chat_room_id_counter += 1

    return chat_room.to_dict()

@router.get("/", response_model=List[ChatRoomResponse])
async def get_chat_rooms(is_group: bool = None):
    """
    Obtener todas las salas de chat

    - **is_group**: Filtrar por tipo de sala (True=grupal, False=1 a 1, None=todas)
    """
    rooms = list(chat_rooms_db.values())

    # Filtrar por tipo si se especifica
    if is_group is not None:
        rooms = [room for room in rooms if room.is_group == is_group]

    return [room.to_dict() for room in rooms]

@router.get("/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(room_id: int):
    """Obtener una sala de chat por ID"""
    chat_room = chat_rooms_db.get(room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )
    return chat_room.to_dict()

@router.put("/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(room_id: int, room_data: ChatRoomUpdate):
    """Actualizar una sala de chat"""
    chat_room = chat_rooms_db.get(room_id)
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Actualizar campos si se proporcionan
    if room_data.name is not None:
        chat_room.name = room_data.name

    if room_data.is_group is not None:
        chat_room.is_group = room_data.is_group

    return chat_room.to_dict()

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_room(room_id: int):
    """Eliminar una sala de chat"""
    if room_id not in chat_rooms_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )
    del chat_rooms_db[room_id]
