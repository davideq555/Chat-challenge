from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
import hashlib
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserUpdate, UserLogin, UserResponse
from app.models.user import User
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def hash_password(password: str) -> str:
    """Hash simple de contraseña (usar bcrypt en producción)"""
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario"""
    # Validar que username no exista
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Validar que email no exista
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Crear usuario
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """Obtener todos los usuarios"""
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario por ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Actualizar un usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Actualizar campos si se proporcionan
    if user_data.username is not None:
        # Verificar que el nuevo username no exista
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = user_data.username

    if user_data.email is not None:
        # Verificar que el nuevo email no exista
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = user_data.email

    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Eliminar un usuario"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(user)
    db.commit()

@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Autenticar un usuario"""
    # Buscar por username o email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verificar contraseña
    if user.password_hash != hash_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verificar que la cuenta esté activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Actualizar last_login
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)

    return user
