from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import AskAIInput
from app.services import AIService, PlantService
from app.utils.pagination import build_pagination_meta

ai_bp = Blueprint("ai", __name__)
plants = PlantService()
service = AIService()


@ai_bp.post("/<int:plant_id>/ai/ask")
@auth_required
def ask_ai(plant_id: int):
    payload = parse_json(AskAIInput)
    plant = plants.get_plant(plant_id, current_user=g.current_user)
    return ok(
        service.ask(current_user=g.current_user, plant=plant, question=payload.question)
    )


@ai_bp.get("/<int:plant_id>/ai/conversations")
@auth_required
def list_conversations(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    items, total = service.list_conversations(
        current_user=g.current_user, plant_id=plant_id, page=page, page_size=page_size
    )
    return ok(
        [
            {
                "id": item.id,
                "title": item.title,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )
