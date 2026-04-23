from __future__ import annotations

from app.extensions import db
from app.models import AIConversation
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository):
    def list_conversations(
        self, *, user_id: int, plant_id: int, page: int, page_size: int
    ):
        stmt = (
            db.select(AIConversation)
            .where(
                AIConversation.user_id == user_id, AIConversation.plant_id == plant_id
            )
            .order_by(AIConversation.updated_at.desc())
        )
        return self.paginate(stmt, page=page, page_size=page_size)

    def get_conversation(self, conversation_id: int) -> AIConversation | None:
        return self.session.get(AIConversation, conversation_id)
