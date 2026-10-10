from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
)
from src.services.template_loader import TemplateLoader

from src.contracts.message_sanitizer import MessageSanitizer
from src.services.notification_message_sanitizer import NotificationMessageSanitizer


def get_message_sanitizer() -> MessageSanitizer:
    return NotificationMessageSanitizer()


def get_notification_service() -> BrevoNotificationService:
    return BrevoNotificationService()


def get_template_loader() -> TemplateLoader:
    return TemplateLoader()
