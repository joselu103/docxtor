# src.docs/service.py

import tempfile
from enum import Enum

import magic
import pymupdf
import pypandoc
import structlog
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.docs.models import Doc
from src.docs.repository import ChunkRepository, DocRepository

logger = structlog.get_logger()


# Exceptions
class DocException(Exception): ...


class InvalidType(DocException): ...


class ParsingError(DocException): ...


class AcceptedFormats(str, Enum):
    PLAIN_TEXT = "plain_text"
    PDF = "pdf"
    DOCX = "docx"
    ODT = "odt"


_BINARY_FORMATS = {
    "application/pdf": AcceptedFormats.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": AcceptedFormats.DOCX,  # noqa: E501
    "application/vnd.oasis.opendocument.text": AcceptedFormats.ODT,
}


def _detect_format(file: UploadFile) -> AcceptedFormats:
    header = file.file.read(2048)
    file.file.seek(0)
    mime = magic.from_buffer(header, mime=True)

    if mime in _BINARY_FORMATS:
        return _BINARY_FORMATS[mime]

    try:
        header.decode("utf-8")
    except UnicodeDecodeError:
        logger.info("Invalid type", mime=mime)
        raise InvalidType(mime)

    return AcceptedFormats.PLAIN_TEXT


def _parse_text(file: UploadFile) -> list[str]:
    file_format = _detect_format(file)

    try:
        if file_format == AcceptedFormats.PLAIN_TEXT:
            return [file.file.read().decode("utf-8")]
        if file_format in (
            AcceptedFormats.DOCX,
            AcceptedFormats.ODT,
        ):
            return _parse_doc(file, suffix=file_format.value)
        if file_format == (AcceptedFormats.PDF):
            return _parse_pdf(file)

    except Exception as e:
        logger.info("Unable to parse the file", exception=str(e))
        raise ParsingError("Unable to parse the file")


def _parse_pdf(file: UploadFile) -> list[str]:
    doc = pymupdf.Document(
        filename=file.filename,
        stream=file.file.read(),
        filetype=file.content_type,
    )
    return [page.get_text() for page in doc]


def _parse_doc(file: UploadFile, suffix: str) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=suffix) as temp:
        temp.write(file.file.read())
        temp.flush()
        result = pypandoc.convert_file(temp.name, format=suffix, to="gfm")
    return [result]


# Services
class DocService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.docs_repo = DocRepository(session)
        self.chunk_repo = ChunkRepository(session)

    async def upload_document(self, file: UploadFile) -> Doc:
        """Parse the file, chunk it and store it in the database.

        Args:
            file: uploaded file.

        Raises:
            InvalidType: if the format is not expected.
            ParsingError: if the document could not be parsed.
        """
        await logger.adebug(f"{file=}")
        await logger.adebug(f"{_detect_format(file)=}")

        doc_text = _parse_text(file)

        # IF THERE IS NO TEXT, RAISE NOTEXTFOUND
        # CREATE AN ENTRY IN DOCS TABLE FOR THE FILE
        # CREATE THE CHUNKS FROM THE DOC_TEXT AND THE ENTRIES IN THE CHUNKS TABLE
        # RETURN DE DOC MODEL CREATED

        await logger.adebug(f"{doc_text=}")
