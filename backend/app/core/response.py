from __future__ import annotations

from typing import Any

from flask import Response, jsonify


def ok(data: Any = None, status: int = 200, meta: dict[str, Any] | None = None):
    payload: dict[str, Any] = {}
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status


def no_content() -> Response:
    return Response(status=204)


def error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        }
    }
