from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.chat_room import ChatRoomCreate, ChatRoomUpdate, ChatRoomResponse
from app.models.chat_room import ChatRoom
from app.database import get_db

router = APIRouter(
    prefix="/chat-rooms",
    tags=["chat-rooms"]
)

@router.post("/", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(room_data: ChatRoomCreate, db: Session = Depends(get_db)):
    """Crear una nueva sala de chat"""
    chat_room = ChatRoom(
        name=room_data.name,
        is_group=room_data.is_group
    )

    db.add(chat_room)
    db.commit()
    db.refresh(chat_room)

    return chat_room

@router.get("/", response_model=List[ChatRoomResponse])
async def get_chat_rooms(is_group: bool = None, db: Session = Depends(get_db)):
    """
    Obtener todas las salas de chat

    - **is_group**: Filtrar por tipo de sala (True=grupal, False=1 a 1, None=todas)
    """
    query = db.query(ChatRoom)

    # Filtrar por tipo si se especifica
    if is_group is not None:
        query = query.filter(ChatRoom.is_group == is_group)

    return query.all()

@router.get("/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(room_id: int, db: Session = Depends(get_db)):
    """Obtener una sala de chat por ID"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )
    return chat_room

@router.put("/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(room_id: int, room_data: ChatRoomUpdate, db: Session = Depends(get_db)):
    """Actualizar una sala de chat"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
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

    db.commit()
    db.refresh(chat_room)

    return chat_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_room(room_id: int, db: Session = Depends(get_db)):
    """Eliminar una sala de chat"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )
    db.delete(chat_room)
    db.commit()
