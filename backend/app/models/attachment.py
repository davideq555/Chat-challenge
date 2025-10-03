from datetime import datetime
from typing import Optional

class Attachment:
    """Modelo de Adjunto"""

    def __init__(
        self,
        id: Optional[int] = None,
        message_id: int = 0,
        file_url: str = "",
        file_type: str = "",
        uploaded_at: Optional[datetime] = None
    ):
        self.id = id
        self.message_id = message_id
        self.file_url = file_url
        self.file_type = file_type
        self.uploaded_at = uploaded_at or datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "file_url": self.file_url,
            "file_type": self.file_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
