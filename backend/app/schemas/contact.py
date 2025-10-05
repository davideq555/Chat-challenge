from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from .user import UserResponse

class ContactBase(BaseModel):
    """Schema base de contacto"""
    contact_id: int = Field(..., description="ID del usuario contacto")

class ContactCreate(ContactBase):
    """Schema para crear un contacto (enviar solicitud)"""
    pass

class ContactUpdate(BaseModel):
    """Schema para actualizar un contacto"""
    status: Literal["pending", "accepted", "blocked"] = Field(..., description="Estado del contacto")

class ContactResponse(ContactBase):
    """Schema de respuesta de contacto"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContactWithUser(ContactResponse):
    """Schema de contacto con información del usuario"""
    contact: UserResponse  # Información completa del contacto
