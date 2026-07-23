# src/chats/schemas.py
import uuid

from pydantic import BaseModel, ConfigDict


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
