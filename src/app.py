# src/app.py

from typing import AsyncIterator

import structlog
from fastapi import FastAPI

from src.settings.settings import get_settings
from src.shared.logging_config import configure_logging

logger = structlog.get_logger()


async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # STARTUP
    await logger.ainfo("Application starting up")

    yield

    # SHUTDOWN
    await logger.ainfo("Application shutting down")


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A REST API + RAG that allows to upload a file and ask questions about it"
            "to an LLM."
        ),
        lifespan=lifespan,
    )

    return app


app = create_app()
