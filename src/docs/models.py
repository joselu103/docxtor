# src/docs/models.py
import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import UUID, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.settings.settings import get_settings
from src.shared.models import BaseModel

if TYPE_CHECKING:
    pass

settings = get_settings()


class Doc(BaseModel):
    __tablename__ = "docs"

    title: Mapped[str] = mapped_column(String, nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("chats.id"), nullable=False
    )

    chunks: Mapped[list[Chunk]] = relationship("Chunk")


class Chunk(BaseModel):
    __tablename__ = "chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("docs.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(settings.vector_dim), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
