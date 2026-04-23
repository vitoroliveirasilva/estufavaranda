from flask import jsonify


def ok(data=None, status: int = 200, meta: dict | None = None):
    payload: dict = {}
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status


def no_content():
    return "", 204


def error_payload(code: str, message: str, details: dict | None = None):
    return {"error": {"code": code, "message": message, "details": details or {}}}
