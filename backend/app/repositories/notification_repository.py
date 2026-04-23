from __future__ import annotations

from app.extensions import db
from app.models import NotificationDispatch, NotificationEvent
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def list_for_user(
        self, *, user_id: int, status: str | None, page: int, page_size: int
    ):
        stmt = (
            db.select(NotificationEvent)
            .where(NotificationEvent.user_id == user_id)
            .order_by(NotificationEvent.created_at.desc())
        )
        if status:
            stmt = stmt.where(NotificationEvent.status == status)
        return self.paginate(stmt, page=page, page_size=page_size)

    def get_by_id(self, notification_id: int) -> NotificationEvent | None:
        return self.session.get(NotificationEvent, notification_id)

    def get_by_dedupe_key(self, dedupe_key: str) -> NotificationEvent | None:
        stmt = db.select(NotificationEvent).where(
            NotificationEvent.dedupe_key == dedupe_key
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def pending_for_dispatch(self, limit: int = 100) -> list[NotificationEvent]:
        stmt = (
            db.select(NotificationEvent)
            .where(NotificationEvent.status == "pending")
            .order_by(NotificationEvent.created_at.asc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def create_dispatch(self, dispatch: NotificationDispatch) -> NotificationDispatch:
        self.add(dispatch)
        return dispatch
