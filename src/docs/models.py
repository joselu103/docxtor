# src/docs/models.py
import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import UUID, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.settings.settings import get_settings
from src.shared.models import BaseModel

if TYPE_CHECKING:
    from src.chats.models import Chat

    pass

settings = get_settings()


class Doc(BaseModel):
    __tablename__ = "docs"

    title: Mapped[str] = mapped_column(String, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )

    chat: Mapped["Chat"] = relationship(back_populates="docs")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="doc", cascade="all, delete-orphan", passive_deletes=True
    )


class Chunk(BaseModel):
    __tablename__ = "chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(settings.vector_dim), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    doc: Mapped["Doc"] = relationship(back_populates="chunks")
