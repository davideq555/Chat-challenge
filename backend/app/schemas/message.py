from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MessageBase(BaseModel):
    """Schema base de mensaje"""
    content: str = Field(..., description="Contenido del mensaje")

class MessageCreate(MessageBase):
    """Schema para crear un mensaje (usado internamente)"""
    room_id: int = Field(..., gt=0, description="ID de la sala de chat")
    user_id: int = Field(..., gt=0, description="ID del usuario autor")

class AttachmentData(BaseModel):
    """Schema para datos de adjunto en el request de mensaje"""
    file_url: str = Field(..., min_length=1, max_length=500, description="URL del archivo")
    file_type: str = Field(..., min_length=1, max_length=50, description="Tipo de archivo")

class MessageCreateRequest(MessageBase):
    """Schema para crear un mensaje con JWT (no incluye user_id, se obtiene del token)"""
    room_id: int = Field(..., gt=0, description="ID de la sala de chat")
    attachments: Optional[List[AttachmentData]] = Field(default=None, description="Adjuntos opcionales")

class MessageUpdate(BaseModel):
    """Schema para actualizar un mensaje (solo contenido)"""
    content: str = Field(..., description="Nuevo contenido del mensaje")

class AttachmentInMessage(BaseModel):
    """Schema de adjunto en respuesta de mensaje"""
    id: int
    file_url: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(MessageBase):
    """Schema de respuesta de mensaje"""
    id: int
    room_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    attachments: List[AttachmentInMessage] = Field(default_factory=list, description="Adjuntos del mensaje")

    class Config:
        from_attributes = True
