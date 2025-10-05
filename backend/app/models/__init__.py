from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from .user import User
from .chat_room import ChatRoom
from .message import Message
from .attachment import Attachment
from .room_participant import RoomParticipant
from .contact import Contact

__all__ = ["Base", "User", "ChatRoom", "Message", "Attachment", "RoomParticipant", "Contact"]
