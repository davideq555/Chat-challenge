from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    """Schema base de mensaje"""
    content: str = Field(..., min_length=1, description="Contenido del mensaje")

class MessageCreate(MessageBase):
    """Schema para crear un mensaje (usado internamente)"""
    room_id: int = Field(..., gt=0, description="ID de la sala de chat")
    user_id: int = Field(..., gt=0, description="ID del usuario autor")

class MessageCreateRequest(MessageBase):
    """Schema para crear un mensaje con JWT (no incluye user_id, se obtiene del token)"""
    room_id: int = Field(..., gt=0, description="ID de la sala de chat")

class MessageUpdate(BaseModel):
    """Schema para actualizar un mensaje (solo contenido)"""
    content: str = Field(..., min_length=1, description="Nuevo contenido del mensaje")

class MessageResponse(MessageBase):
    """Schema de respuesta de mensaje"""
    id: int
    room_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool

    class Config:
        from_attributes = True
