from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.common import InputModel, ORMModel, blank_str_to_none


class AskAIInput(InputModel):
    question: str = Field(min_length=3, max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def _validate_question(cls, value):
        value = blank_str_to_none(value)
        if value is None:
            raise ValueError("question é obrigatório.")
        return value


class AIConversationOutput(ORMModel):
    id: int
    user_id: int
    plant_id: int | None
    title: str | None
