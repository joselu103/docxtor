import io
from pathlib import Path
from unittest.mock import AsyncMock

import faker
import pytest
import structlog
from fastapi import UploadFile
from llama_index.core.node_parser import SentenceSplitter

from src.docs.service import DocService, InvalidType, _chunk_text, _parse_text
from src.settings.settings import get_settings

logger = structlog.get_logger()
fake = faker.Faker()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

FILE_START_AND_END = ("Lorem ipsum dolor sit amet", "inceptos himenaeos.")


@pytest.fixture
def random_text():
    return fake.text(200)


@pytest.fixture
def doc_service():
    service = DocService(session=AsyncMock())
    service.user_repo = AsyncMock()
    return service


@pytest.mark.parametrize(
    "file_name",
    ["text-file.txt", "text-file-no-extension"],
    ids=["text file", "text file wo extension"],
)
async def test_parse_text_from_plain_text_file(file_name):
    # Given
    file_data = (FIXTURES_DIR / file_name).read_bytes()
    upload_file = UploadFile(io.BytesIO(file_data))

    # When
    result = _parse_text(upload_file)

    # Then
    for fragment in FILE_START_AND_END:
        assert fragment in result


async def test_parse_text_from_plain_text_file_csv_like():
    # Given
    file_data = (FIXTURES_DIR / "text-file-with-commas.txt").read_bytes()
    upload_file = UploadFile(io.BytesIO(file_data))

    # When
    result = _parse_text(upload_file)

    # Then
    assert result == "cell 1, cell 2, cell 3, cell 4\ncell 5, cell 6, cell 7, cell 8\n"


async def test_parse_text_from_pdf():
    # Given
    file_data = (FIXTURES_DIR / "pdf-file.pdf").read_bytes()
    upload_file = UploadFile(io.BytesIO(file_data))

    # When
    result = _parse_text(upload_file)

    # Then
    for fragment in FILE_START_AND_END:
        assert fragment in result


@pytest.mark.parametrize(
    "filename",
    ["docx-file.docx", "odt-file.odt"],
    ids=[".docx", ".odt"],
)
async def test_parse_text_from_document(filename):
    # Given
    file_data = (FIXTURES_DIR / filename).read_bytes()
    upload_file = UploadFile(io.BytesIO(file_data))

    # When
    result = _parse_text(upload_file)

    # Then
    for fragment in FILE_START_AND_END:
        assert fragment in result


async def test_parse_text_invalid_utf8():
    # Given
    file_data = (FIXTURES_DIR / "no-utf8.bin").read_bytes()
    upload_file = UploadFile(io.BytesIO(file_data))

    # Then
    with pytest.raises(InvalidType):
        # When
        _parse_text(upload_file)


async def test_chunk_text():
    # Given
    settings = get_settings()
    max_chunk_size = 300
    file_data = (FIXTURES_DIR / "paul_graham_essay.txt").read_bytes().decode("utf-8")
    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_size // 5
    )

    # When
    chunks = await _chunk_text(splitter, file_data, max_chunk_size)
    await logger.adebug("Chunk 1", chunk=chunks[0])
    await logger.adebug("Chunk 2", chunk=chunks[1])

    # Then
    assert chunks
    for chunk in chunks:
        assert chunk
