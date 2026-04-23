from __future__ import annotations

from sqlalchemy import Select

from app.extensions import db


class BaseRepository:
    @property
    def session(self):
        return db.session

    def add(self, entity):
        self.session.add(entity)
        return entity

    def delete(self, entity):
        self.session.delete(entity)

    def commit(self):
        self.session.commit()

    def flush(self):
        self.session.flush()

    def paginate(self, stmt: Select, *, page: int, page_size: int):
        total = self.session.execute(
            db.select(db.func.count()).select_from(stmt.subquery())
        ).scalar_one()
        items = (
            self.session.execute(stmt.limit(page_size).offset((page - 1) * page_size))
            .scalars()
            .all()
        )
        return items, total
