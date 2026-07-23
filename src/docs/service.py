# src.docs/service.py

import tempfile
import uuid
from enum import Enum

import magic
import pymupdf
import pypandoc
import structlog
from fastapi import UploadFile
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.voyageai import VoyageEmbedding
from sqlalchemy.ext.asyncio import AsyncSession

from src.docs.models import Chunk, Doc
from src.docs.repository import ChunkRepository, DocRepository
from src.settings.settings import get_settings

logger = structlog.get_logger()


# Exceptions
class DocException(Exception): ...


class InvalidType(DocException): ...


class ParsingError(DocException): ...


class ChunkingError(DocException): ...


class EmbeddingError(DocException): ...


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


def _parse_text(file: UploadFile) -> str:
    file_format = _detect_format(file)

    try:
        if file_format == AcceptedFormats.PLAIN_TEXT:
            return file.file.read().decode("utf-8")
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


def _parse_pdf(file: UploadFile) -> str:
    doc = pymupdf.Document(
        filename=file.filename,
        stream=file.file.read(),
        filetype=file.content_type,
    )
    return "\n".join(page.get_text() for page in doc)


def _parse_doc(file: UploadFile, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix) as temp:
        temp.write(file.file.read())
        temp.flush()
        result = pypandoc.convert_file(temp.name, format=suffix, to="gfm")
    return result


async def _chunk_text(
    splitter: SentenceSplitter, text: str, chunk_size: int
) -> list[str]:
    try:
        nodes = await splitter.aget_nodes_from_documents([Document(text=text)])
        return [node.get_content() for node in nodes]

    except Exception:
        logger.exception("Exception while chunking")
        raise ChunkingError("Unable to chunk text")


async def _create_embeddings(
    embed_model: VoyageEmbedding, chunks_text: list[str]
) -> list[list[float]]:
    settings = get_settings()
    try:
        return await embed_model.aget_text_embedding_batch(
            texts=chunks_text,
            model=settings.voyage_model,
            input_type="document",
        )
    except Exception:
        logger.exception("Exception while embedding")
        raise EmbeddingError("Unable to embed text chunks")


# Services
class DocService:
    def __init__(self, session: AsyncSession):
        settings = get_settings()
        self.session = session
        self.doc_repo = DocRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.embed_model = VoyageEmbedding(
            model_name="voyage-4-lite",
            voyage_api_key=settings.voyage_api_key.get_secret_value(),
            input_type="document",
        )
        self.splitter = SentenceSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_size // 5
        )

    async def upload_document(self, file: UploadFile, chat_id: uuid.UUID) -> Doc:
        """Parse the file, chunk it and store it in the database.

        Args:
            file: uploaded file.
            chat_id: uuid of the chat associated with this document.

        Raises:
            InvalidType: if the format is not expected.
            ParsingError: if the document could not be parsed.
            ChunkingError: if the document text could not be chunked.text
            EmbeddingError: if the text-chunks could not be embedded.
        """
        settings = get_settings()

        doc_text = _parse_text(file)

        chunks_text = await _chunk_text(self.splitter, doc_text, settings.chunk_size)

        doc = Doc(
            title=file.filename,
            chat_id=chat_id,
        )
        await self.doc_repo.create(doc)

        embeddings = await _create_embeddings(self.embed_model, chunks_text=chunks_text)

        for index, (content, embedding) in enumerate(zip(chunks_text, embeddings)):
            chunk = Chunk(
                doc_id=doc.id, content=content, embedding=embedding, chunk_index=index
            )
            await self.chunk_repo.create(chunk)

        return doc
