from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AskAIInput(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AIConversationOutput(ORMModel):
    id: int
    user_id: int
    plant_id: int | None
    title: str | None
