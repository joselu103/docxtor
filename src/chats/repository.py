# src/chats/repository.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.chats.models import Chat, Message
from src.docs.models import Doc
from src.shared.repository import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Chat)

    async def get_with_doc_and_chunks(
        self, chat_id: uuid.UUID, doc_title: str
    ) -> Chat | None:
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(
                selectinload(Chat.docs.and_(Doc.title == doc_title)).selectinload(
                    Doc.chunks
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)
