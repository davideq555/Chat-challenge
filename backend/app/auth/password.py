"""
Utilidades para manejo de contraseñas con bcrypt
"""
from passlib.context import CryptContext

# Configurar bcrypt para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash una contraseña usando bcrypt

    Args:
        password: Contraseña en texto plano

    Returns:
        Contraseña hasheada
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar si una contraseña coincide con el hash

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Contraseña hasheada

    Returns:
        True si coinciden, False si no
    """
    return pwd_context.verify(plain_password, hashed_password)
