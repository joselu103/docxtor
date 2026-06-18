# src/docs/repository.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.docs.models import Chunk, Doc
from src.shared.repository import BaseRepository


class DocRepository(BaseRepository[Doc]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Doc)


class ChunkRepository(BaseRepository[Chunk]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Chunk)
