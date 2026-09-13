from typing import Annotated
from fastapi import Depends
from src.contracts.notification_service import NotificationService
from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
)
from src.services.notification_manager_service import NotificationManagerService
from src.services.template_loader import TemplateLoader

from src.contracts.message_sanitizer import MessageSanitizer
from src.services.notification_message_sanitizer import NotificationMessageSanitizer


def get_message_sanitizer() -> MessageSanitizer:
    return NotificationMessageSanitizer()


def get_notification_service() -> BrevoNotificationService:
    return BrevoNotificationService()


def get_template_loader() -> TemplateLoader:
    return TemplateLoader()


def get_notification_manager_service(
    notify_service: Annotated[NotificationService, Depends(get_notification_service)],
    template_loader: Annotated[TemplateLoader, Depends(get_template_loader)],
) -> NotificationManagerService:
    return NotificationManagerService(
        notify_service=notify_service, template_loader=template_loader
    )
