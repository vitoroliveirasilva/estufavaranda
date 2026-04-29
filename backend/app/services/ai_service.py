from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import ValidationError
from app.core.security import utcnow
from app.models import AIConversation, AIMessage, PlantDiagnosis
from app.repositories import AIRepository
from app.services.local_plant_ai_engine import LocalPlantAiEngine, LocalPlantAiResult
from app.services.plant_ai_context import PlantAiContextBuilder

logger = logging.getLogger(__name__)


class AIService:
    MIN_QUESTION_LENGTH = 5
    MAX_QUESTION_LENGTH = 2000
    TITLE_MAX_LENGTH = 120

    def __init__(
        self,
        *,
        repo: AIRepository | None = None,
        context_builder: PlantAiContextBuilder | None = None,
        engine: LocalPlantAiEngine | None = None,
    ) -> None:
        self.repo = repo or AIRepository()
        self.context_builder = context_builder or PlantAiContextBuilder()
        self.engine = engine or LocalPlantAiEngine()

    def ask(self, *, current_user, plant, question: str) -> dict[str, Any]:
        cleaned_question = self._clean_question(question)
        context = self.context_builder.build(plant)
        result = self.engine.answer(question=cleaned_question, context=context)

        now = utcnow()
        assistant_created_at = utcnow()

        conversation = AIConversation(
            user_id=current_user.id,
            plant_id=plant.id,
            title=cleaned_question[: self.TITLE_MAX_LENGTH],
            created_at=now,
            updated_at=assistant_created_at,
        )

        try:
            self.repo.add(conversation)
            self.repo.flush()

            user_message = AIMessage(
                conversation_id=conversation.id,
                role="user",
                content=cleaned_question,
                metadata_json=None,
                created_at=now,
            )

            assistant_metadata = {
                "confidence": result.confidence,
                "considered_context": result.considered_context,
            }

            assistant_message = AIMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=result.answer,
                metadata_json=assistant_metadata,
                created_at=assistant_created_at,
            )

            self.repo.add_all((user_message, assistant_message))

            if result.confidence in {"medium", "high"}:
                self.repo.add(
                    PlantDiagnosis(
                        plant_id=plant.id,
                        source="assistant",
                        confidence=result.confidence,
                        summary=result.answer,
                        details_json={
                            "confidence": result.confidence,
                            "considered_context": result.considered_context,
                            "mode": "local_rules",
                        },
                        created_at=assistant_created_at,
                    )
                )

            self.repo.commit()

            logger.info(
                "ai.ask.completed",
                extra={
                    "plant_id": plant.id,
                    "user_id": current_user.id,
                    "conversation_id": conversation.id,
                    "confidence": result.confidence,
                },
            )

            return self._serialize_answer(
                result=result,
                conversation_id=conversation.id,
            )
        except Exception:
            self.repo.rollback()
            logger.exception(
                "ai.ask.failed",
                extra={
                    "plant_id": getattr(plant, "id", None),
                    "user_id": getattr(current_user, "id", None),
                },
            )
            raise

    def list_conversations(
        self,
        *,
        current_user,
        plant_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        conversations, total = self.repo.list_conversations(
            user_id=current_user.id,
            plant_id=plant_id,
            page=page,
            page_size=page_size,
        )

        return [self._serialize_conversation(item) for item in conversations], total

    def get_conversation(
        self,
        *,
        current_user,
        plant_id: int,
        conversation_id: int,
    ) -> dict[str, Any] | None:
        conversation = self.repo.get_conversation(
            user_id=current_user.id,
            plant_id=plant_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return None

        return self._serialize_conversation(conversation)

    def _clean_question(self, question: str) -> str:
        if not isinstance(question, str):
            raise ValidationError(
                "Dados inválidos.",
                details={"question": "Informe uma pergunta em texto."},
            )

        cleaned = " ".join(question.split())

        if len(cleaned) < self.MIN_QUESTION_LENGTH:
            raise ValidationError(
                "Dados inválidos.",
                details={
                    "question": f"Informe uma pergunta com pelo menos {self.MIN_QUESTION_LENGTH} caracteres."
                },
            )

        if len(cleaned) > self.MAX_QUESTION_LENGTH:
            raise ValidationError(
                "Dados inválidos.",
                details={
                    "question": f"A pergunta deve ter no máximo {self.MAX_QUESTION_LENGTH} caracteres."
                },
            )

        return cleaned

    def _serialize_answer(
        self,
        *,
        result: LocalPlantAiResult,
        conversation_id: int,
    ) -> dict[str, Any]:
        return {
            "answer": result.answer,
            "resposta": result.answer,
            "message": result.answer,
            "recommendation": result.answer,
            "summary": result.answer,
            "diagnosis": result.answer,
            "confidence": result.confidence,
            "considered_context": result.considered_context,
            "conversation_id": conversation_id,
        }

    def _serialize_conversation(self, conversation: AIConversation) -> dict[str, Any]:
        messages = self._ordered_messages(conversation)
        first_user_message = next(
            (message for message in messages if message.role == "user"),
            None,
        )
        last_assistant_message = next(
            (message for message in reversed(messages) if message.role == "assistant"),
            None,
        )

        question = (
            first_user_message.content if first_user_message else conversation.title
        )
        answer_payload = (
            self._build_answer_payload(last_assistant_message)
            if last_assistant_message
            else None
        )

        return {
            "id": conversation.id,
            "title": conversation.title,
            "question": question,
            "answer": answer_payload,
            "response": answer_payload,
            "messages": [self._serialize_message(message) for message in messages],
            "created_at": self._iso(conversation.created_at),
            "updated_at": self._iso(conversation.updated_at),
        }

    def _build_answer_payload(self, message: AIMessage | None) -> dict[str, Any] | None:
        if message is None:
            return None

        metadata = message.metadata_json or {}

        return {
            "answer": message.content,
            "confidence": metadata.get("confidence", "low"),
            "considered_context": metadata.get("considered_context", {}),
        }

    def _serialize_message(self, message: AIMessage) -> dict[str, Any]:
        metadata = message.metadata_json

        if message.role == "user":
            metadata = None

        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": self._iso(message.created_at),
            "metadata_json": metadata,
        }

    @staticmethod
    def _ordered_messages(conversation: AIConversation) -> list[AIMessage]:
        return sorted(
            list(conversation.messages or []),
            key=lambda message: (
                message.created_at.isoformat() if message.created_at else "",
                message.id or 0,
            ),
        )

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None
