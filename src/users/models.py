# src/users/models.py
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models import BaseModel

if TYPE_CHECKING:
    from src.chats.models import Chat


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    chats: Mapped[list["Chat"]] = relationship("Chat")
