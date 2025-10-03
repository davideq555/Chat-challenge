from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime

class EventType(str, Enum):
    """Tipos de eventos WebSocket"""
    # Mensajes
    MESSAGE = "message"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_UPDATED = "message_updated"

    # Usuario
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"

    # Sistema
    ERROR = "error"
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"

class WebSocketEvent(BaseModel):
    """Estructura base de un evento WebSocket"""
    type: EventType
    data: Optional[dict] = None
    timestamp: datetime = datetime.now()
    user_id: Optional[int] = None
    room_id: Optional[int] = None

    class Config:
        use_enum_values = True

class MessageEvent(BaseModel):
    """Evento de mensaje nuevo"""
    type: EventType = EventType.MESSAGE
    message_id: int
    room_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime

    class Config:
        use_enum_values = True

class TypingEvent(BaseModel):
    """Evento de usuario escribiendo"""
    type: EventType = EventType.TYPING
    room_id: int
    user_id: int
    username: str
    is_typing: bool

    class Config:
        use_enum_values = True

class UserEvent(BaseModel):
    """Evento de usuario (join/leave)"""
    type: EventType
    room_id: int
    user_id: int
    username: str
    timestamp: datetime = datetime.now()

    class Config:
        use_enum_values = True

class ErrorEvent(BaseModel):
    """Evento de error"""
    type: EventType = EventType.ERROR
    message: str
    code: Optional[str] = None
    timestamp: datetime = datetime.now()

    class Config:
        use_enum_values = True

def create_event(event_type: EventType, **kwargs) -> dict:
    """
    Helper para crear eventos rápidamente

    Args:
        event_type: Tipo de evento
        **kwargs: Datos del evento

    Returns:
        Diccionario con el evento
    """
    return {
        "type": event_type.value,
        "data": kwargs,
        "timestamp": datetime.now().isoformat()
    }
