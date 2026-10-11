from typing import Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
)
from src.services.template_loader import TemplateLoader

from src.contracts.message_sanitizer import MessageSanitizer
from src.services.notification_message_sanitizer import NotificationMessageSanitizer
from src.services.notification_manager_service import NotificationManagerService
from src.contracts.notification_service import NotificationService
from itmentorsoft_persistence.repositories import NotificationRepository
from itmentorsoft_persistence.mappers import NotificationMapper
from src.infrastructure.databases.postgres_notification_repository import (
    PostgresNotificationRepository,
)


def get_message_sanitizer() -> MessageSanitizer:
    return NotificationMessageSanitizer()


def get_notification_service() -> BrevoNotificationService:
    return BrevoNotificationService()


def get_template_loader() -> TemplateLoader:
    return TemplateLoader()


def _get_notification_repository_factory() -> (
    Callable[[AsyncSession], NotificationRepository]
):
    return lambda session: PostgresNotificationRepository(session, NotificationMapper)


def get_notification_manager_service(
    notify_service: NotificationService = Depends(get_notification_service),
    template_loader: TemplateLoader = Depends(get_template_loader),
    notification_repository_factory: Callable[
        [AsyncSession], NotificationRepository
    ] = Depends(_get_notification_repository_factory),
) -> NotificationManagerService:
    return NotificationManagerService(
        notify_service=notify_service,
        template_loader=template_loader,
        notification_repository_factory=notification_repository_factory,
    )
