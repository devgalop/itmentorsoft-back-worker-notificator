"""Integration tests for notification service contracts (NotificationConfig, NotificationConfigBuilder)."""

import pytest
import uuid

from src.contracts.notification_service import (
    NotificationConfig,
    NotificationConfigBuilder,
    NotificationService,
)
from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants

# -- NotificationConfig --


def test_notification_config_has_uuid():
    """NotificationConfig generates a uuid on construction."""
    config = NotificationConfig(
        sender="sender@example.com",
        destination="dest@example.com",
        subject="Test",
    )
    assert config.uuid is not None
    assert len(config.uuid) == 32  # uuid4().hex is 32 chars


def test_notification_config_stores_attributes():
    """NotificationConfig stores sender, destination, subject, and defaults template/attachments."""
    config = NotificationConfig(
        sender="sender@example.com",
        destination="dest@example.com",
        subject="Test Subject",
    )
    assert config.sender == "sender@example.com"
    assert config.destination == "dest@example.com"
    assert config.subject == "Test Subject"
    assert config.template is None
    assert config.attachments == []


def test_notification_config_uuid_is_unique():
    """Each NotificationConfig instance gets a unique uuid."""
    c1 = NotificationConfig("a@b.com", "c@d.com", "S1")
    c2 = NotificationConfig("a@b.com", "c@d.com", "S1")
    assert c1.uuid != c2.uuid


# -- NotificationConfigBuilder --


def test_builder_sets_template_and_builds():
    """NotificationConfigBuilder sets template and returns the config via build()."""
    builder = NotificationConfigBuilder(
        destination="user@example.com",
        subject="Hello",
    )
    builder.set_template("<p>Hello world</p>")
    config = builder.build()

    assert isinstance(config, NotificationConfig)
    assert config.template == "<p>Hello world</p>"
    assert config.destination == "user@example.com"
    assert config.subject == "Hello"


def test_builder_adds_attachment():
    """NotificationConfigBuilder.add_attachment appends to the attachments list."""
    builder = NotificationConfigBuilder(
        destination="user@example.com",
        subject="With attachment",
    )
    builder.add_attachment("/path/to/file1.pdf")
    builder.add_attachment("/path/to/file2.pdf")
    config = builder.build()

    assert len(config.attachments) == 2
    assert config.attachments[0] == "/path/to/file1.pdf"
    assert config.attachments[1] == "/path/to/file2.pdf"


def test_builder_returns_self_for_chaining():
    """set_template and add_attachment return the builder instance for fluent chaining."""
    builder = NotificationConfigBuilder(
        destination="user@example.com",
        subject="Chained",
    )
    result_set = builder.set_template("<p>Test</p>")
    result_add = builder.add_attachment("file.pdf")

    assert result_set is builder
    assert result_add is builder


def test_builder_raises_when_env_sender_not_set():
    """NotificationConfigBuilder raises ValueError when EMAIL_DEFAULT_SENDER is empty."""
    original = EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER
    try:
        EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = ""
        with pytest.raises(ValueError, match="EMAIL_DEFAULT_SENDER"):
            NotificationConfigBuilder(
                destination="user@example.com",
                subject="No sender",
            )
    finally:
        EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = original


def test_builder_fluent_interface_full_chain():
    """Full fluent chain: destination, subject, template, attachment, then build."""
    builder = (
        NotificationConfigBuilder(
            destination="user@example.com",
            subject="Full chain",
        )
        .set_template("<h1>Welcome</h1>")
        .add_attachment("welcome.pdf")
    )
    config = builder.build()

    assert config.destination == "user@example.com"
    assert config.subject == "Full chain"
    assert config.template == "<h1>Welcome</h1>"
    assert config.attachments == ["welcome.pdf"]


# -- NotificationService contract --


def test_notification_service_is_abstract():
    """NotificationService cannot be instantiated directly because it is abstract."""
    with pytest.raises(TypeError):
        NotificationService()
