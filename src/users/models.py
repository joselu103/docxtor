# src/users/models.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.chats.models import Chat
from src.shared.models import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    chats: Mapped[list[Chat]] = relationship("Chat")
