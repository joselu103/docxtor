# src/chats/router.py

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats.schemas import ChatResponse
from src.chats.service import ChatService, CreateChatError
from src.database.engine import get_db, transaction
from src.docs.service import DocException, DocService
from src.shared.dependencies import get_current_user
from src.users.models import User

logger = structlog.get_logger()

router = APIRouter(prefix="/chats", tags=["chats"])


def get_chat_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ChatService:
    return ChatService(session)


def get_doc_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DocService:
    return DocService(session)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_with_doc(
    user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    doc_service: Annotated[DocService, Depends(get_doc_service)],
    doc: UploadFile,
) -> ChatResponse:
    """Create a new chat with the provided document.

    Raises:
        HTTPException(400): Unable to create new chat.
    """
    try:
        async with transaction(chat_service.session):
            chat = await chat_service.create_new_chat(user_id=user.id)
            doc = await doc_service.upload_document(file=doc, chat_id=chat.id)

        return ChatResponse.model_validate(chat)
    except DocException, CreateChatError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to create new chat.")
