"""
Dependencies para autenticación JWT
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.jwt import verify_token

# Configurar esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtener el usuario actual desde el token JWT

    Args:
        credentials: Credenciales HTTP Bearer (token)
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extraer token
    token = credentials.credentials

    # Verificar token
    token_data = verify_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    # Buscar usuario en BD
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Obtener el usuario actual desde el token JWT (opcional)
    No lanza excepción si no hay token

    Args:
        credentials: Credenciales HTTP Bearer (token) - opcional
        db: Sesión de base de datos

    Returns:
        Usuario autenticado o None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    token_data = verify_token(token)

    if token_data is None or token_data.user_id is None:
        return None

    user = db.query(User).filter(User.id == token_data.user_id).first()
    return user
