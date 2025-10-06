from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.chat_room import ChatRoomCreate, ChatRoomUpdate, ChatRoomResponse
from app.schemas.room_participant import RoomParticipantCreate, RoomParticipantResponse
from app.models.chat_room import ChatRoom
from app.models.room_participant import RoomParticipant
from app.models.message import Message
from app.models.attachment import Attachment
from app.models.user import User
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/chat-rooms",
    tags=["chat-rooms"]
)

@router.post("/", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva sala de chat (requiere autenticación JWT)

    - **room_data**: Datos de la sala

    El usuario autenticado será agregado automáticamente como participante
    """
    # Crear la sala
    chat_room = ChatRoom(
        name=room_data.name,
        is_group=room_data.is_group
    )

    db.add(chat_room)
    db.commit()
    db.refresh(chat_room)

    # Agregar al creador como participante automáticamente
    participant = RoomParticipant(
        room_id=chat_room.id,
        user_id=current_user.id
    )

    db.add(participant)
    db.commit()

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

@router.get("/my-rooms", response_model=List[ChatRoomResponse])
async def get_user_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todas las salas donde el usuario autenticado es participante (requiere JWT)
    """
    # Obtener todas las salas donde el usuario es participante
    room_ids = db.query(RoomParticipant.room_id).filter(
        RoomParticipant.user_id == current_user.id
    ).all()

    # Extraer los IDs
    room_ids = [room_id[0] for room_id in room_ids]

    # Obtener las salas
    rooms = db.query(ChatRoom).filter(ChatRoom.id.in_(room_ids)).all()

    return rooms

@router.get("/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener una sala de chat por ID (requiere JWT y validación de acceso)

    - **room_id**: ID de la sala
    """
    # Verificar que la sala existe
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Verificar que el usuario es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    return chat_room

@router.put("/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(
    room_id: int,
    room_data: ChatRoomUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar una sala de chat (requiere JWT y validación de acceso)

    - **room_id**: ID de la sala
    - **room_data**: Datos a actualizar
    """
    # Verificar que la sala existe
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Verificar que el usuario es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
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
async def delete_chat_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar una sala de chat (requiere JWT y validación de acceso)

    - **room_id**: ID de la sala

    Elimina en cascada: attachments → messages → participants → chat_room
    """
    # Verificar que la sala existe
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Verificar que el usuario es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    # Eliminar todo en el orden correcto para evitar violaciones de foreign key

    # 1. Obtener todos los mensajes de este room
    messages = db.query(Message).filter(Message.room_id == room_id).all()

    # 2. Para cada mensaje, eliminar sus attachments
    for message in messages:
        db.query(Attachment).filter(Attachment.message_id == message.id).delete()

    # 3. Eliminar todos los mensajes
    db.query(Message).filter(Message.room_id == room_id).delete()

    # 4. Eliminar todos los participantes
    db.query(RoomParticipant).filter(RoomParticipant.room_id == room_id).delete()

    # 5. Finalmente eliminar el chat room
    db.delete(chat_room)
    db.commit()

# --- ENDPOINTS DE GESTIÓN DE PARTICIPANTES ---

@router.post("/{room_id}/participants", response_model=RoomParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    room_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Agregar un participante a una sala (requiere JWT)

    - **room_id**: ID de la sala
    - **user_id**: ID del usuario a agregar (query parameter)

    Solo los participantes actuales de una sala pueden agregar nuevos participantes
    """
    # Verificar que la sala existe
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Verificar que el usuario autenticado es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    # Verificar que el usuario a agregar existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verificar que no sea ya participante
    existing = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant of this room"
        )

    # Agregar participante
    participant = RoomParticipant(
        room_id=room_id,
        user_id=user_id
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return participant

@router.delete("/{room_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    room_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remover un participante de una sala (requiere JWT)

    - **room_id**: ID de la sala
    - **user_id**: ID del usuario a remover

    Solo los participantes de una sala pueden remover participantes (incluido a sí mismos)
    """
    # Verificar que el usuario autenticado es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    # Buscar al participante a remover
    participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == user_id
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in this room"
        )

    db.delete(participant)
    db.commit()

@router.get("/{room_id}/participants", response_model=List[RoomParticipantResponse])
async def get_room_participants(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los participantes de una sala (requiere JWT)

    - **room_id**: ID de la sala

    Solo los participantes de una sala pueden ver la lista de participantes
    """
    # Verificar que la sala existe
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # Verificar que el usuario autenticado es participante de la sala
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    participants = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room_id
    ).all()

    return participants
