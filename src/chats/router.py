# src/chats/router.py

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.docs.service import DocService

logger = structlog.get_logger()

router = APIRouter(prefix="/chats", tags=["chats"])

"text/plain"
"application/octet-stream"
"application/pdf"


def get_doc_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DocService:
    return DocService(session)


@router.post("")
async def create_chat_with_doc(
    doc_service: Annotated[DocService, Depends(get_doc_service)],
    doc: UploadFile,
):
    doc = await doc_service.upload_document(file=doc)
    return
