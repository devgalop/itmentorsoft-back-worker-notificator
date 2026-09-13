import pytest

from src.dependencies import (
    get_message_sanitizer,
    get_notification_service,
    get_template_loader,
)
from src.services.notification_message_sanitizer import NotificationMessageSanitizer
from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
)
from src.services.template_loader import TemplateLoader


class TestDependencies:
    def test_get_message_sanitizer_returns_correct_type(self):
        result = get_message_sanitizer()
        assert isinstance(result, NotificationMessageSanitizer)

    def test_get_notification_service_returns_correct_type(self):
        result = get_notification_service()
        assert isinstance(result, BrevoNotificationService)

    def test_get_template_loader_returns_correct_type(self):
        result = get_template_loader()
        assert isinstance(result, TemplateLoader)

    def test_get_message_sanitizer_returns_new_instance_each_time(self):
        r1 = get_message_sanitizer()
        r2 = get_message_sanitizer()
        assert r1 is not r2

    def test_get_notification_service_returns_new_instance_each_time(self):
        r1 = get_notification_service()
        r2 = get_notification_service()
        assert r1 is not r2

    def test_get_template_loader_returns_new_instance_each_time(self):
        r1 = get_template_loader()
        r2 = get_template_loader()
        assert r1 is not r2
