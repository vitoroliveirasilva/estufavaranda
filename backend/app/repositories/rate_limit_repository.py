from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import AuthRateLimitEvent
from app.repositories.base import BaseRepository


class AuthRateLimitRepository(BaseRepository):
    def count_recent(
        self,
        *,
        action: str,
        scope_key: str,
        window_start: datetime,
    ) -> int:
        stmt = db.select(db.func.count(AuthRateLimitEvent.id)).where(
            AuthRateLimitEvent.action == action,
            AuthRateLimitEvent.scope_key == scope_key,
            AuthRateLimitEvent.created_at >= window_start,
        )
        return int(self.session.execute(stmt).scalar_one())

    def register_hit(
        self,
        *,
        action: str,
        scope_key: str,
        created_at: datetime,
    ) -> AuthRateLimitEvent:
        item = AuthRateLimitEvent(
            action=action,
            scope_key=scope_key,
            created_at=created_at,
        )
        self.add(item)
        return item

    def register_hits(
        self,
        *,
        action: str,
        scope_keys: list[str],
        created_at: datetime,
    ) -> list[AuthRateLimitEvent]:
        items = [
            AuthRateLimitEvent(
                action=action,
                scope_key=scope_key,
                created_at=created_at,
            )
            for scope_key in scope_keys
        ]
        self.add_all(items)
        return items

    def delete_older_than(self, *, older_than: datetime) -> int:
        result = self.session.execute(
            db.delete(AuthRateLimitEvent).where(
                AuthRateLimitEvent.created_at < older_than
            )
        )
        return result.rowcount or 0
