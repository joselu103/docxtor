# src/chats/service.py

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats.models import Chat
from src.chats.repository import ChatRepository

logger = structlog.get_logger()


# Exceptions
class CreateChatError(Exception): ...


# Services
class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatRepository(session)

    async def create_new_chat(
        self, user_id: uuid.UUID, title: str = "New chat"
    ) -> Chat:
        """Create a new chat

        Args:
            title: Name of the new chat.
            user_id: UUID of the logged user.

        Returns:
            New Chat object
        """
        chat = Chat(title=title, user_id=user_id)
        await self.chat_repo.create(chat)
        return chat
