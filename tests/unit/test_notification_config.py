import pytest
from unittest.mock import patch

from src.contracts.notification_service import (
    NotificationConfig,
    NotificationConfigBuilder,
)


class TestNotificationConfig:
    def test_fields_initialised(self):
        cfg = NotificationConfig(
            sender="sender@test.com",
            destination="dest@test.com",
            subject="Subject",
        )
        assert cfg.sender == "sender@test.com"
        assert cfg.destination == "dest@test.com"
        assert cfg.subject == "Subject"
        assert cfg.template is None
        assert cfg.attachments == []

    def test_uuid_is_generated(self):
        cfg1 = NotificationConfig("a@b.com", "c@d.com", "S")
        cfg2 = NotificationConfig("a@b.com", "c@d.com", "S")
        assert cfg1.uuid  # non-empty
        assert cfg1.uuid != cfg2.uuid  # unique


class TestNotificationConfigBuilder:
    VALID_SENDER_ENV = "noreply@test.com"

    def _patch_sender(self, monkeypatch):
        monkeypatch.setattr(
            "src.contracts.notification_service.EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER",
            self.VALID_SENDER_ENV,
        )

    def test_build_success(self, monkeypatch):
        self._patch_sender(monkeypatch)
        builder = NotificationConfigBuilder(destination="dest@test.com", subject="Hi")
        config = builder.build()
        assert config.sender == self.VALID_SENDER_ENV
        assert config.destination == "dest@test.com"
        assert config.subject == "Hi"

    def test_value_error_when_sender_empty(self, monkeypatch):
        monkeypatch.setattr(
            "src.contracts.notification_service.EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER",
            "",
        )
        with pytest.raises(
            ValueError, match="EMAIL_DEFAULT_SENDER environment variable is not set"
        ):
            NotificationConfigBuilder(destination="dest@test.com", subject="Hi")

    def test_set_template_returns_builder(self, monkeypatch):
        self._patch_sender(monkeypatch)
        builder = NotificationConfigBuilder(destination="d@test.com", subject="S")
        result = builder.set_template("<p>HTML</p>")
        assert result is builder  # fluent interface

    def test_set_template_sets_value(self, monkeypatch):
        self._patch_sender(monkeypatch)
        builder = NotificationConfigBuilder(destination="d@test.com", subject="S")
        builder.set_template("<h1>Title</h1>")
        config = builder.build()
        assert config.template == "<h1>Title</h1>"

    def test_add_attachment_appends(self, monkeypatch):
        self._patch_sender(monkeypatch)
        builder = NotificationConfigBuilder(destination="d@test.com", subject="S")
        builder.add_attachment("file1.pdf")
        builder.add_attachment("file2.pdf")
        config = builder.build()
        assert config.attachments == ["file1.pdf", "file2.pdf"]

    def test_build_returns_notification_config(self, monkeypatch):
        self._patch_sender(monkeypatch)
        builder = NotificationConfigBuilder(destination="d@test.com", subject="S")
        config = builder.build()
        assert isinstance(config, NotificationConfig)
