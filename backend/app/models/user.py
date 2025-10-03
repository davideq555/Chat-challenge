from datetime import datetime
from typing import Optional

class User:
    """Modelo de Usuario"""

    def __init__(
        self,
        id: Optional[int] = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
        created_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None,
        is_active: bool = True
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        self.is_active = is_active

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
