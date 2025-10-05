"""
Utilidades para manejo de JWT (JSON Web Tokens)
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuración JWT
SECRET_KEY = "your-secret-key-change-this-in-production-use-env-variable"  # TODO: Mover a .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 días


class TokenData(BaseModel):
    """Schema de datos del token"""
    user_id: Optional[int] = None
    username: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear un token JWT de acceso

    Args:
        data: Datos a codificar en el token (debe incluir 'sub' con user_id)
        expires_delta: Tiempo de expiración personalizado (opcional)

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verificar y decodificar un token JWT

    Args:
        token: Token JWT a verificar

    Returns:
        TokenData si el token es válido, None si no
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")

        if user_id is None:
            return None

        return TokenData(user_id=user_id, username=username)
    except JWTError:
        return None
