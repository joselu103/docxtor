# tests/integration/test_chats.py


from pathlib import Path

import pytest
import structlog
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats.repository import ChatRepository
from src.chats.schemas import ChatResponse

logger = structlog.get_logger()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# /chats
@pytest.mark.integration
@pytest.mark.paid_api
async def test_create_chat_with_doc(
    db_session: AsyncSession, client: AsyncClient, access_token: str
):
    # Given
    header = {"Authorization": f"Bearer {access_token}"}
    fpath = FIXTURES_DIR / "pdf-file.pdf"
    chat_repo = ChatRepository(db_session)

    # When
    with open(fpath, "rb") as f:
        response = await client.post(
            url="http://test/api/v1/chats",
            headers=header,
            files={"doc": ("pdf-file.pdf", f, "application/pdf")},
        )

    # Then
    assert response.status_code == 201
    ChatResponse.model_validate(response.json())

    chat = await chat_repo.get_with_doc_and_chunks(
        chat_id=response.json()["id"], doc_title="pdf-file.pdf"
    )
    assert chat
    assert chat.docs

    chunks = chat.docs[0].chunks
    assert chunks

    await logger.ainfo(
        "Results", chat_id=chat.id, doc_id=chat.docs[0].id, n_chunks=len(chunks)
    )
