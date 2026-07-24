# src/chats/models.py
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.docs.models import Doc
from src.shared.models import BaseModel

if TYPE_CHECKING:
    pass


class ChatStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Chat(BaseModel):
    __tablename__ = "chats"

    title: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[ChatStatus] = mapped_column(
        SAEnum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", passive_deletes=True
    )
    docs: Mapped[list["Doc"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", passive_deletes=True
    )


class Message(BaseModel):
    __tablename__ = "messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    from_user: Mapped[bool] = mapped_column(Boolean, nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="messages")
