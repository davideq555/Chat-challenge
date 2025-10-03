from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Schema base de usuario"""
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")
    email: EmailStr = Field(..., description="Correo electrónico único")

class UserCreate(UserBase):
    """Schema para crear un usuario"""
    password: str = Field(..., min_length=8, description="Contraseña del usuario")

class UserUpdate(BaseModel):
    """Schema para actualizar un usuario"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    """Schema para login"""
    username: str = Field(..., description="Nombre de usuario o email")
    password: str = Field(..., description="Contraseña")

class UserResponse(UserBase):
    """Schema de respuesta de usuario"""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    """Schema de usuario en base de datos (incluye password_hash)"""
    password_hash: str
