from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserUpdate, UserLogin, UserResponse, Token
from app.models.user import User
from app.database import get_db
from app.services.user_online import user_online_service
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

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
        # Usar bcrypt para hashear la nueva contraseña
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

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Autenticar un usuario y retornar un token JWT

    Args:
        credentials: Username/email y contraseña
        db: Sesión de base de datos

    Returns:
        Token JWT y datos del usuario
    """
    # Buscar por username o email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verificar contraseña con bcrypt
    if not verify_password(credentials.password, user.password_hash):
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

    # Crear token JWT
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/online", response_model=List[int])
async def get_online_users():
    """
    Obtener lista de IDs de usuarios online

    Returns:
        Lista de IDs de usuarios que están conectados actualmente
    """
    online_users = user_online_service.get_online_users()
    # Convertir set de strings a lista de ints
    return [int(user_id) for user_id in online_users]

@router.get("/{user_id}/online")
async def check_user_online(user_id: int, db: Session = Depends(get_db)):
    """
    Verificar si un usuario específico está online

    Args:
        user_id: ID del usuario a verificar

    Returns:
        Diccionario con is_online y connections_count
    """
    # Verificar que el usuario exista
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    is_online = user_online_service.is_user_online(user_id)
    connections_count = user_online_service.get_user_connections_count(user_id)

    return {
        "user_id": user_id,
        "username": user.username,
        "is_online": is_online,
        "connections_count": connections_count
    }
