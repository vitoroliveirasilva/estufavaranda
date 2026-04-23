from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30
_ALLOWED_CONFIDENCE = {"low", "medium", "high"}


@dataclass(slots=True)
class AIAnswer:
    answer: str
    confidence: str
    metadata: dict[str, Any]


class ExternalAIProvider:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or self._build_session()

    def ask(self, *, question: str, context: dict) -> AIAnswer:
        normalized_question = self._normalize_question(question)
        normalized_context = self._normalize_context(context)
        settings = get_settings()
        provider_url = str(getattr(settings, "ai_provider_url", "") or "").strip()
        provider_key = str(getattr(settings, "ai_provider_key", "") or "").strip()

        if not provider_url or not provider_key:
            raise RuntimeError("Provider externo de IA não configurado.")

        payload = {
            "model": getattr(settings, "ai_provider_model", None),
            "question": normalized_question,
            "context": normalized_context,
        }
        headers = {
            "Authorization": f"Bearer {provider_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = self._session.post(
                provider_url,
                json=payload,
                headers=headers,
                timeout=self._get_timeout_seconds(settings),
                allow_redirects=False,
            )
            self._raise_for_status(response)
            response_payload = response.json()
        except requests.Timeout as exc:
            logger.warning(
                "provider.ai.timeout",
                extra={
                    "provider_url": provider_url,
                    "timeout_seconds": self._get_timeout_seconds(settings),
                },
                exc_info=exc,
            )
            raise RuntimeError(
                "Tempo esgotado ao consultar provider externo de IA."
            ) from exc
        except requests.RequestException as exc:
            logger.exception(
                "provider.ai.request_failed",
                extra={"provider_url": provider_url},
            )
            raise RuntimeError("Falha ao consultar provider externo de IA.") from exc
        except ValueError as exc:
            logger.exception(
                "provider.ai.invalid_json",
                extra={"provider_url": provider_url},
            )
            raise RuntimeError(
                "Provider externo de IA retornou JSON inválido."
            ) from exc

        if not isinstance(response_payload, dict):
            logger.error(
                "provider.ai.invalid_payload_type",
                extra={
                    "provider_url": provider_url,
                    "payload_type": type(response_payload).__name__,
                },
            )
            raise RuntimeError("Provider externo de IA retornou payload inválido.")

        answer = str(response_payload.get("answer") or "").strip()
        confidence = self._normalize_confidence(response_payload.get("confidence"))

        return AIAnswer(
            answer=answer,
            confidence=confidence,
            metadata=response_payload,
        )

    @staticmethod
    def _build_session() -> Session:
        session = requests.Session()
        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"POST"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _normalize_question(question: str) -> str:
        normalized = str(question or "").strip()
        if not normalized:
            raise ValueError("Pergunta inválida para o provider de IA.")
        return normalized

    @staticmethod
    def _normalize_context(context: Any) -> dict[str, Any]:
        if context is None:
            return {}
        if isinstance(context, dict):
            return context
        if isinstance(context, Mapping):
            return dict(context)
        raise ValueError("Contexto inválido para o provider de IA.")

    @staticmethod
    def _normalize_confidence(value: Any) -> str:
        normalized = str(value or "low").strip().lower()
        if normalized not in _ALLOWED_CONFIDENCE:
            return "low"
        return normalized

    @staticmethod
    def _get_timeout_seconds(settings: Any) -> float:
        raw_timeout = getattr(
            settings, "ai_request_timeout_seconds", _DEFAULT_TIMEOUT_SECONDS
        )
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError):
            return float(_DEFAULT_TIMEOUT_SECONDS)
        return timeout if timeout > 0 else float(_DEFAULT_TIMEOUT_SECONDS)

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.warning(
                "provider.ai.http_error",
                extra={
                    "status_code": response.status_code,
                    "response_preview": response.text[:500],
                },
            )
            raise exc


_EXTERNAL_AI_PROVIDER: ExternalAIProvider | None = None


def get_ai_provider() -> ExternalAIProvider | None:
    global _EXTERNAL_AI_PROVIDER

    settings = get_settings()
    provider_mode = str(getattr(settings, "ai_provider_mode", "") or "").strip().lower()
    if provider_mode != "external":
        return None

    if _EXTERNAL_AI_PROVIDER is None:
        _EXTERNAL_AI_PROVIDER = ExternalAIProvider()
    return _EXTERNAL_AI_PROVIDER
