from datetime import datetime
from typing import Optional

class ChatRoom:
    """Modelo de Sala de Chat"""

    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        is_group: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.is_group = is_group
        self.created_at = created_at or datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_group": self.is_group,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
