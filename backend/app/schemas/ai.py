from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from app.schemas.common import InputModel, ORMModel, blank_str_to_none


class AskAIInput(InputModel):
    question: str = Field(min_length=5, max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def _validate_question(cls, value):
        value = blank_str_to_none(value)

        if value is None:
            raise ValueError("question é obrigatório.")

        if not isinstance(value, str):
            raise ValueError("question deve ser um texto.")

        cleaned = " ".join(value.split())

        if not cleaned:
            raise ValueError("question não pode ser vazio.")

        return cleaned


class AIAnswerOutput(ORMModel):
    answer: str
    confidence: str
    considered_context: dict[str, Any]


class AIMessageOutput(ORMModel):
    id: int
    role: str
    content: str
    created_at: str
    metadata_json: dict[str, Any] | None = None


class AIConversationOutput(ORMModel):
    id: int
    title: str | None
    question: str | None
    answer: AIAnswerOutput | None
    response: AIAnswerOutput | None
    messages: list[AIMessageOutput]
    created_at: str
    updated_at: str
