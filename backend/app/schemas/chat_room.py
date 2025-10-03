from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ChatRoomBase(BaseModel):
    """Schema base de sala de chat"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la sala")
    is_group: bool = Field(default=False, description="Indica si es chat grupal o 1 a 1")

class ChatRoomCreate(ChatRoomBase):
    """Schema para crear una sala de chat"""
    pass

class ChatRoomUpdate(BaseModel):
    """Schema para actualizar una sala de chat"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_group: Optional[bool] = None

class ChatRoomResponse(ChatRoomBase):
    """Schema de respuesta de sala de chat"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
