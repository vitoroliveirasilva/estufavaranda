from __future__ import annotations

import logging
from datetime import timedelta

from app.core.exceptions import NotFoundError
from app.core.security import utcnow
from app.models import NotificationDispatch, NotificationEvent
from app.models.base import NotificationStatus, PlantEventType
from app.repositories import DeviceRepository, NotificationRepository, PlantRepository
from app.services.watering_service import WateringService
from app.utils.validators import validate_choice

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()
        self.plants = PlantRepository()
        self.devices = DeviceRepository()
        self.watering = WateringService()

    def list_notifications(
        self,
        *,
        user_id: int,
        status: str | None,
        page: int,
        page_size: int,
    ):
        if status is not None:
            cleaned_status = str(status).strip().lower()
            validate_choice(
                cleaned_status,
                {item.value for item in NotificationStatus},
                "status",
            )
            status = cleaned_status
        return self.repo.list_for_user(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    def mark_read(self, *, user_id: int, notification_id: int) -> NotificationEvent:
        notification = self.repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            raise NotFoundError("Alerta não encontrado.")
        if notification.read_at is None:
            notification.status = NotificationStatus.READ.value
            notification.read_at = utcnow()
            self.repo.commit()
        return notification

    def discard(self, *, user_id: int, notification_id: int) -> NotificationEvent:
        notification = self.repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            raise NotFoundError("Alerta não encontrado.")
        if notification.discarded_at is None:
            notification.status = NotificationStatus.DISCARDED.value
            notification.discarded_at = utcnow()
            self.repo.commit()
        return notification

    def create_alert(
        self,
        *,
        user_id: int,
        plant_id: int | None,
        alert_type: str,
        title: str,
        body: str,
        dedupe_key: str | None,
    ) -> tuple[NotificationEvent, bool]:
        cleaned_dedupe_key = self.repo.clean_text(dedupe_key)
        if cleaned_dedupe_key:
            existing = self.repo.get_by_dedupe_key(cleaned_dedupe_key)
            if existing:
                return existing, False

        notification = NotificationEvent(
            user_id=user_id,
            plant_id=plant_id,
            type=self.repo.clean_text(alert_type) or "generic",
            title=self.repo.clean_text(title) or "Alerta",
            body=self.repo.clean_text(body) or "Você possui uma nova notificação.",
            status=NotificationStatus.PENDING.value,
            dedupe_key=cleaned_dedupe_key,
            created_at=utcnow(),
        )
        self.repo.add(notification)
        return notification, True

    def generate_alerts(self) -> dict:
        plants = self.plants.list_active_plants()
        generated = 0
        failures = 0

        for plant in plants:
            try:
                now = utcnow()
                summary = self.watering.get_summary(plant)
                bucket = now.strftime("%Y%m%d%H")

                if summary["score"] >= 80:
                    _, created = self.create_alert(
                        user_id=plant.user_id,
                        plant_id=plant.id,
                        alert_type="watering_risk",
                        title=f"{plant.name} pode estar com muita sede",
                        body="O score de necessidade de rega está alto. Revise o substrato antes de regar.",
                        dedupe_key=f"thirst:{plant.id}:{bucket}",
                    )
                    generated += int(created)

                recent_events = self.plants.recent_events(plant.id, limit=5)
                if any(
                    evt.event_type == PlantEventType.REPOTTING.value
                    for evt in recent_events
                ) and any(
                    evt.event_type == PlantEventType.WILT.value for evt in recent_events
                ):
                    _, created = self.create_alert(
                        user_id=plant.user_id,
                        plant_id=plant.id,
                        alert_type="stress_hypothesis",
                        title=f"{plant.name} pode estar em estresse pós-transplante",
                        body="Foram encontrados sinais recentes de troca de vaso e murcha. Observe por mais alguns dias.",
                        dedupe_key=f"post-repot-stress:{plant.id}:{now.strftime('%Y%m%d')}",
                    )
                    generated += int(created)

                photos = self.plants.recent_photos(plant.id, limit=1)
                threshold = now - timedelta(days=21)
                if not photos or (
                    (photos[0].taken_at or photos[0].uploaded_at) < threshold
                ):
                    _, created = self.create_alert(
                        user_id=plant.user_id,
                        plant_id=plant.id,
                        alert_type="evolution_reminder",
                        title=f"Hora de registrar uma nova foto de {plant.name}",
                        body="Faz algum tempo desde o último registro visual. Uma foto nova ajuda a acompanhar a evolução.",
                        dedupe_key=f"photo-reminder:{plant.id}:{now.strftime('%Y%W')}",
                    )
                    generated += int(created)
            except Exception:
                logger.exception(
                    "notification.generate.failed",
                    extra={"plant_id": plant.id},
                )
                failures += 1

        self.repo.commit()
        return {"generated": generated, "failures": failures}

    def dispatch_pending_notifications(self) -> dict:
        pending = self.repo.pending_for_dispatch(limit=100)
        processed = 0
        failures = 0

        for notification in pending:
            try:
                devices = self.devices.list_enabled_devices_for_user(
                    notification.user_id
                )
                provider_response = f"mode=log devices={len(devices)}"
                logger.info(
                    "notification.dispatched",
                    extra={
                        "notification_id": notification.id,
                        "devices": len(devices),
                        "type": notification.type,
                    },
                )
                dispatch = NotificationDispatch(
                    notification_event_id=notification.id,
                    channel="push",
                    dispatched_at=utcnow(),
                    success=True,
                    provider_response=provider_response,
                )
                self.repo.create_dispatch(dispatch)
                notification.status = NotificationStatus.SENT.value
                processed += 1
            except Exception as exc:
                logger.exception(
                    "notification.dispatch.failed",
                    extra={"notification_id": notification.id},
                )
                dispatch = NotificationDispatch(
                    notification_event_id=notification.id,
                    channel="push",
                    dispatched_at=utcnow(),
                    success=False,
                    provider_response=str(exc),
                )
                self.repo.create_dispatch(dispatch)
                notification.status = NotificationStatus.FAILED.value
                failures += 1

        self.repo.commit()
        return {"processed": processed, "failures": failures}
