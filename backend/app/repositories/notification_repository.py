from __future__ import annotations

from app.extensions import db
from app.models import NotificationDispatch, NotificationEvent
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def list_for_user(
        self, *, user_id: int, status: str | None, page: int, page_size: int
    ) -> tuple[list[NotificationEvent], int]:
        if user_id <= 0:
            return [], 0

        stmt = (
            db.select(NotificationEvent)
            .where(NotificationEvent.user_id == user_id)
            .order_by(NotificationEvent.created_at.desc(), NotificationEvent.id.desc())
        )

        cleaned_status = self.clean_text(status)
        if cleaned_status is not None:
            stmt = stmt.where(NotificationEvent.status == cleaned_status)

        return self.paginate(stmt, page=page, page_size=page_size)

    def get_by_id(self, notification_id: int) -> NotificationEvent | None:
        if notification_id <= 0:
            return None
        return self.session.get(NotificationEvent, notification_id)

    def get_by_dedupe_key(self, dedupe_key: str | None) -> NotificationEvent | None:
        cleaned_dedupe_key = self.clean_text(dedupe_key)
        if cleaned_dedupe_key is None:
            return None
        stmt = db.select(NotificationEvent).where(
            NotificationEvent.dedupe_key == cleaned_dedupe_key
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def pending_for_dispatch(self, limit: int = 100) -> list[NotificationEvent]:
        stmt = (
            db.select(NotificationEvent)
            .where(NotificationEvent.status == "pending")
            .order_by(NotificationEvent.created_at.asc(), NotificationEvent.id.asc())
            .limit(self.normalize_limit(limit, default=100, max_value=1000))
        )
        return self.session.execute(stmt).scalars().all()

    def create_dispatch(self, dispatch: NotificationDispatch) -> NotificationDispatch:
        return self.add(dispatch)
