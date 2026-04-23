from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.extensions import db

EntityT = TypeVar("EntityT")


class BaseRepository:
    DEFAULT_MAX_PAGE_SIZE = 100
    DEFAULT_MAX_LIST_LIMIT = 1000

    @property
    def session(self) -> Session:
        return db.session

    def add(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        return entity

    def add_all(
        self, entities: list[EntityT] | tuple[EntityT, ...]
    ) -> list[EntityT] | tuple[EntityT, ...]:
        self.session.add_all(list(entities))
        return entities

    def delete(self, entity: Any) -> None:
        self.session.delete(entity)

    def commit(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def rollback(self) -> None:
        self.session.rollback()

    def flush(self) -> None:
        self.session.flush()

    @staticmethod
    def clean_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @classmethod
    def build_like_pattern(cls, value: str | None) -> str | None:
        cleaned = cls.clean_text(value)
        if cleaned is None:
            return None
        escaped = cleaned.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped.lower()}%"

    @classmethod
    def normalize_limit(
        cls, limit: int | None, *, default: int = 10, max_value: int | None = None
    ) -> int:
        if max_value is None:
            max_value = cls.DEFAULT_MAX_LIST_LIMIT
        if limit is None:
            return max(1, min(default, max_value))
        return max(1, min(int(limit), max_value))

    def paginate(
        self, stmt: Select[Any], *, page: int, page_size: int
    ) -> tuple[list[Any], int]:
        safe_page = max(int(page), 1)
        safe_page_size = max(1, min(int(page_size), self.DEFAULT_MAX_PAGE_SIZE))

        total_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = int(self.session.execute(total_stmt).scalar_one())

        paginated_stmt = stmt.limit(safe_page_size).offset(
            (safe_page - 1) * safe_page_size
        )
        items = self.session.execute(paginated_stmt).scalars().unique().all()
        return items, total
