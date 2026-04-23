from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIAnswer:
    answer: str
    confidence: str
    metadata: dict


class ExternalAIProvider:
    def ask(self, *, question: str, context: dict) -> AIAnswer:
        settings = get_settings()
        if not settings.ai_provider_url or not settings.ai_provider_key:
            raise RuntimeError("Provider externo de IA não configurado.")

        resp = requests.post(
            settings.ai_provider_url,
            json={
                "model": settings.ai_provider_model,
                "question": question,
                "context": context,
            },
            headers={"Authorization": f"Bearer {settings.ai_provider_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        return AIAnswer(
            answer=payload.get("answer", ""),
            confidence=payload.get("confidence", "low"),
            metadata=payload,
        )


def get_ai_provider():
    settings = get_settings()
    if settings.ai_provider_mode.lower() == "external":
        return ExternalAIProvider()
    return None
