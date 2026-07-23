import io
from pathlib import Path
from unittest.mock import AsyncMock

import faker
import pytest
import structlog
from fastapi import UploadFile

from src.docs.service import DocService, InvalidType, _parse_text

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
