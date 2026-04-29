from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import AIConversation
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository):
    def list_conversations(
        self,
        *,
        user_id: int,
        plant_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[AIConversation], int]:
        stmt = (
            db.select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.plant_id == plant_id,
            )
            .options(selectinload(AIConversation.messages))
            .order_by(AIConversation.updated_at.desc(), AIConversation.id.desc())
        )

        return self.paginate(stmt, page=page, page_size=page_size)

    def get_conversation(
        self,
        *,
        user_id: int,
        plant_id: int,
        conversation_id: int,
    ) -> AIConversation | None:
        if conversation_id <= 0:
            return None

        stmt = (
            db.select(AIConversation)
            .where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
                AIConversation.plant_id == plant_id,
            )
            .options(selectinload(AIConversation.messages))
        )

        return self.session.execute(stmt).scalar_one_or_none()
