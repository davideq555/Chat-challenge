from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class Contact(Base):
    """Modelo de Contacto - Relación entre usuarios"""
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, accepted, blocked
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)

    # Constraint para evitar duplicados
    __table_args__ = (
        UniqueConstraint('user_id', 'contact_id', name='unique_contact_relationship'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_id": self.contact_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
