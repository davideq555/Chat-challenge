from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RoomParticipantBase(BaseModel):
    """Schema base de participante de sala"""
    room_id: int = Field(..., description="ID de la sala")
    user_id: int = Field(..., description="ID del usuario")

class RoomParticipantCreate(RoomParticipantBase):
    """Schema para agregar participante a una sala"""
    pass

class RoomParticipantResponse(RoomParticipantBase):
    """Schema de respuesta de participante"""
    id: int
    joined_at: datetime

    class Config:
        from_attributes = True
