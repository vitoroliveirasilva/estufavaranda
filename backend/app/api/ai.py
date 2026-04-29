from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import AskAIInput
from app.services import AIService, PlantService
from app.utils.pagination import build_pagination_meta

ai_bp = Blueprint("ai", __name__)
plants = PlantService()
service = AIService()


def _parse_positive_int_arg(
    name: str,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    raw_value = request.args.get(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: "Informe um número inteiro válido."},
        ) from exc

    if value < minimum or (maximum is not None and value > maximum):
        limit_text = (
            f"entre {minimum} e {maximum}" if maximum is not None else f">= {minimum}"
        )

        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: f"Informe um valor {limit_text}."},
        )

    return value


@ai_bp.post("/<int:plant_id>/ai/ask")
@auth_required
def ask_ai(plant_id: int):
    payload = parse_json(AskAIInput)
    plant = plants.get_plant(plant_id, current_user=g.current_user)

    return ok(
        service.ask(
            current_user=g.current_user,
            plant=plant,
            question=payload.question,
        )
    )


@ai_bp.get("/<int:plant_id>/ai/conversations")
@auth_required
def list_conversations(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)

    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)

    items, total = service.list_conversations(
        current_user=g.current_user,
        plant_id=plant_id,
        page=page,
        page_size=page_size,
    )

    return ok(
        items,
        meta=build_pagination_meta(
            page=page,
            page_size=page_size,
            total=total,
        ),
    )


@ai_bp.get("/<int:plant_id>/ai/conversations/<int:conversation_id>")
@auth_required
def get_conversation(plant_id: int, conversation_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)

    item = service.get_conversation(
        current_user=g.current_user,
        plant_id=plant_id,
        conversation_id=conversation_id,
    )

    if item is None:
        raise ValidationError(
            "Conversa não encontrada.",
            details={
                "conversation_id": "A conversa não existe ou não pertence a esta planta."
            },
        )

    return ok(item)
