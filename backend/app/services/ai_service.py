from __future__ import annotations

from app.core.security import utcnow
from app.models import AIConversation, AIMessage, PlantDiagnosis
from app.providers.ai import get_ai_provider
from app.repositories import AIRepository, PlantRepository
from app.services.watering_service import WateringService


class AIService:
    def __init__(self):
        self.repo = AIRepository()
        self.plants = PlantRepository()
        self.watering = WateringService()

    def build_context(self, plant) -> dict:
        recent_events = self.plants.recent_events(plant.id, limit=8)
        recent_photos = self.plants.recent_photos(plant.id, limit=5)
        recent_climate = self.plants.recent_climate_snapshots(plant.id, limit=5)
        watering_summary = self.watering.get_summary(plant)

        return {
            "plant_name": plant.name,
            "species": (
                plant.species_profile.common_name if plant.species_profile else None
            ),
            "scientific_name": (
                plant.species_profile.scientific_name if plant.species_profile else None
            ),
            "environment": plant.environment,
            "light_exposure": plant.light_exposure,
            "ventilation": plant.ventilation,
            "location_label": plant.location_label,
            "city_name": plant.city_name,
            "health_status": plant.health_status,
            "watering_summary": watering_summary,
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at.isoformat(),
                    "title": event.title,
                    "description": event.description,
                }
                for event in recent_events
            ],
            "recent_photos": [
                {
                    "photo_type": photo.photo_type,
                    "caption": photo.caption,
                    "taken_at": (photo.taken_at or photo.uploaded_at).isoformat(),
                }
                for photo in recent_photos
            ],
            "recent_climate": [
                {
                    "recorded_at": snapshot.recorded_at.isoformat(),
                    "temperature_c": (
                        float(snapshot.temperature_c)
                        if snapshot.temperature_c is not None
                        else None
                    ),
                    "humidity_percent": snapshot.humidity_percent,
                    "rain_mm": (
                        float(snapshot.rain_mm)
                        if snapshot.rain_mm is not None
                        else None
                    ),
                    "uv_index": (
                        float(snapshot.uv_index)
                        if snapshot.uv_index is not None
                        else None
                    ),
                }
                for snapshot in recent_climate
            ],
        }

    def _rule_based_answer(
        self, *, plant, question: str, context: dict
    ) -> tuple[str, str, dict]:
        question_lower = question.lower()
        watering = context["watering_summary"]
        recent_events = {event["event_type"] for event in context["recent_events"]}
        recent_heat = watering.get("recent_heat")
        considered_context = {
            "last_watering_days": watering.get("days_since_last_watering"),
            "recent_heat": recent_heat,
            "recent_repotting": "repotting" in recent_events,
            "recent_wilt": "wilt" in recent_events,
            "watering_score": watering.get("score"),
            "risk_level": watering.get("risk_level"),
        }

        if "regar" in question_lower or "sede" in question_lower:
            if watering["score"] >= 80:
                answer = "Pode haver sede sim. O score está alto e vale revisar a umidade real do substrato antes de regar."
                confidence = "medium"
            elif watering["score"] >= 60:
                answer = "Há indícios moderados de sede, mas ainda não é certeza. Verifique o substrato e a firmeza das folhas."
                confidence = "medium"
            else:
                answer = "Pelos sinais atuais, não parece uma urgência de rega. Ainda assim, confirme o substrato antes de decidir."
                confidence = "low"
            return answer, confidence, considered_context

        if "o que pode" in question_lower or "acontecendo" in question_lower:
            if "repotting" in recent_events and "wilt" in recent_events:
                return (
                    "Pode ser estresse pós-transplante, especialmente se a murcha apareceu depois da troca de vaso. Observe recuperação gradual e evite intervenções agressivas.",
                    "medium",
                    considered_context,
                )
            if recent_heat and watering["score"] >= 60:
                return (
                    "O clima recente pode estar contribuindo para desidratação ou estresse térmico. Vale revisar umidade do substrato, incidência de sol e ventilação.",
                    "medium",
                    considered_context,
                )
            return (
                "Com o contexto atual, existem hipóteses, mas não um diagnóstico absoluto. Vale observar substrato, evolução das folhas e mudanças recentes de ambiente.",
                "low",
                considered_context,
            )

        return (
            "Consigo sugerir hipóteses com base no histórico da planta, mas prefiro tratar a resposta como apoio contextual e não como diagnóstico fechado.",
            "low",
            considered_context,
        )

    def ask(self, *, current_user, plant, question: str) -> dict:
        context = self.build_context(plant)
        answer, confidence, considered_context = self._rule_based_answer(
            plant=plant, question=question, context=context
        )

        external_provider = get_ai_provider()
        metadata = {"considered_context": considered_context, "mode": "rules"}
        if external_provider is not None:
            try:
                external = external_provider.ask(question=question, context=context)
                answer = external.answer or answer
                confidence = external.confidence or confidence
                metadata["external"] = external.metadata
                metadata["mode"] = "external"
            except Exception:
                metadata["external_error"] = "fallback_to_rules"

        conversation = AIConversation(
            user_id=current_user.id,
            plant_id=plant.id,
            title=question[:120],
        )
        self.repo.add(conversation)
        self.repo.flush()

        self.repo.add(
            AIMessage(
                conversation_id=conversation.id,
                role="user",
                content=question,
                metadata_json={"asked_at": utcnow().isoformat()},
                created_at=utcnow(),
            )
        )
        self.repo.add(
            AIMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                metadata_json=metadata,
                created_at=utcnow(),
            )
        )

        if confidence in {"medium", "high"}:
            self.repo.add(
                PlantDiagnosis(
                    plant_id=plant.id,
                    source="assistant",
                    confidence=confidence,
                    summary=answer,
                    details_json=metadata,
                    created_at=utcnow(),
                )
            )

        self.repo.commit()
        return {
            "answer": answer,
            "confidence": confidence,
            "considered_context": considered_context,
        }

    def list_conversations(
        self, *, current_user, plant_id: int, page: int, page_size: int
    ):
        return self.repo.list_conversations(
            user_id=current_user.id, plant_id=plant_id, page=page, page_size=page_size
        )
