from datetime import datetime
from typing import Optional

class Message:
    """Modelo de Mensaje"""

    def __init__(
        self,
        id: Optional[int] = None,
        room_id: int = 0,
        user_id: int = 0,
        content: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_deleted: bool = False
    ):
        self.id = id
        self.room_id = room_id
        self.user_id = user_id
        self.content = content
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at
        self.is_deleted = is_deleted

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted
        }
