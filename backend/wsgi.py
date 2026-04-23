from __future__ import annotations

from app import create_app


def build_app():
    return create_app()


app = build_app()
application = app

__all__ = ["app", "application", "build_app"]
