from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import hashlib

from app.schemas.user import UserCreate, UserUpdate, UserLogin, UserResponse
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Almacenamiento temporal en memoria (luego se reemplazará con base de datos)
users_db = {}
user_id_counter = 1

def hash_password(password: str) -> str:
    """Hash simple de contraseña (usar bcrypt en producción)"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_username(username: str) -> User | None:
    """Buscar usuario por username"""
    for user in users_db.values():
        if user.username == username:
            return user
    return None

def get_user_by_email(email: str) -> User | None:
    """Buscar usuario por email"""
    for user in users_db.values():
        if user.email == email:
            return user
    return None

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """Crear un nuevo usuario"""
    global user_id_counter

    # Validar que username no exista
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Validar que email no exista
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Crear usuario
    user = User(
        id=user_id_counter,
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        created_at=datetime.now(),
        is_active=True
    )

    users_db[user_id_counter] = user
    user_id_counter += 1

    return user.to_dict()

@router.get("/", response_model=List[UserResponse])
async def get_users():
    """Obtener todos los usuarios"""
    return [user.to_dict() for user in users_db.values()]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Obtener un usuario por ID"""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user.to_dict()

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate):
    """Actualizar un usuario"""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Actualizar campos si se proporcionan
    if user_data.username is not None:
        # Verificar que el nuevo username no exista
        existing = get_user_by_username(user_data.username)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = user_data.username

    if user_data.email is not None:
        # Verificar que el nuevo email no exista
        existing = get_user_by_email(user_data.email)
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

    return user.to_dict()

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """Eliminar un usuario"""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    del users_db[user_id]

@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin):
    """Autenticar un usuario"""
    user = get_user_by_username(credentials.username)

    # También permitir login con email
    if not user:
        user = get_user_by_email(credentials.username)

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

    return user.to_dict()
