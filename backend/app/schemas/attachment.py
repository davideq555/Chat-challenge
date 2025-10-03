from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
from enum import Enum

class FileType(str, Enum):
    """Tipos de archivo permitidos"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    PDF = "pdf"
    OTHER = "other"

class AttachmentBase(BaseModel):
    """Schema base de adjunto"""
    file_url: str = Field(..., min_length=1, max_length=255, description="URL o path del archivo")
    file_type: str = Field(..., min_length=1, max_length=50, description="Tipo de archivo")

class AttachmentCreate(AttachmentBase):
    """Schema para crear un adjunto"""
    message_id: int = Field(..., gt=0, description="ID del mensaje al que pertenece")

class AttachmentUpdate(BaseModel):
    """Schema para actualizar un adjunto"""
    file_url: Optional[str] = Field(None, min_length=1, max_length=255)
    file_type: Optional[str] = Field(None, min_length=1, max_length=50)

class AttachmentResponse(AttachmentBase):
    """Schema de respuesta de adjunto"""
    id: int
    message_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
