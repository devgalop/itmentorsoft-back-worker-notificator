"""Integration tests for NotificationEmailRequest and MessageVariables models."""

import json
import pytest
from pydantic import ValidationError

from src.models.notification_email_request import (
    NotificationEmailRequest,
    MessageVariables,
    EMAIL_PATTERN,
    MESSAGE_KEY_PATTERN,
)

# -- MessageVariables --


def test_message_variables_to_dict():
    """MessageVariables.to_dict() returns a dict with key and value."""
    mv = MessageVariables(key="%code%", value="123456")
    result = mv.to_dict()
    assert result == {"key": "%code%", "value": "123456"}


def test_message_variables_valid_key_format():
    """MessageVariables accepts keys in the %word% format."""
    mv = MessageVariables(key="%name%", value="Alice")
    assert mv.key == "%name%"
    assert mv.value == "Alice"


def test_message_variables_rejects_invalid_key_format():
    """MessageVariables rejects keys not matching %word% pattern."""
    with pytest.raises(ValidationError, match="Invalid message variable key format"):
        MessageVariables(key="name", value="Alice")

    with pytest.raises(ValidationError, match="Invalid message variable key format"):
        MessageVariables(key="name%", value="Alice")

    with pytest.raises(ValidationError, match="Invalid message variable key format"):
        MessageVariables(key="%name", value="Alice")


def test_message_variables_rejects_empty_key():
    """MessageVariables rejects an empty key (fails regex before empty check)."""
    with pytest.raises(ValidationError, match="Invalid message variable key format"):
        MessageVariables(key="", value="value")


def test_message_variables_rejects_empty_value():
    """MessageVariables rejects an empty value."""
    with pytest.raises(ValidationError, match="Field cannot be empty"):
        MessageVariables(key="%key%", value="")


# -- NotificationEmailRequest --


def test_notification_email_request_get_content():
    """get_content() returns a JSON string of the request fields."""
    request = NotificationEmailRequest(
        recipient="user@example.com",
        subject="Test",
        html_template_code="otp",
        message_variables=[MessageVariables(key="%code%", value="123")],
    )
    content = request.get_content()
    data = json.loads(content)
    assert data["recipient"] == "user@example.com"
    assert data["subject"] == "Test"
    assert data["html_template_code"] == "otp"
    assert data["message_variables"] == [{"key": "%code%", "value": "123"}]


def test_notification_email_request_valid():
    """NotificationEmailRequest validates a well-formed request."""
    request = NotificationEmailRequest(
        recipient="alice@example.com",
        subject="Welcome to the platform",
        html_template_code="user_created",
        message_variables=[
            MessageVariables(key="%name%", value="Alice"),
            MessageVariables(key="%link%", value="https://example.com"),
        ],
    )
    assert request.recipient == "alice@example.com"
    assert request.subject == "Welcome to the platform"
    assert request.html_template_code == "user_created"
    assert len(request.message_variables) == 2


def test_notification_email_request_rejects_invalid_email():
    """NotificationEmailRequest rejects invalid email addresses."""
    with pytest.raises(ValidationError):
        NotificationEmailRequest(
            recipient="not-an-email",
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )

    with pytest.raises(ValidationError):
        NotificationEmailRequest(
            recipient="@example.com",
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )

    with pytest.raises(ValidationError):
        NotificationEmailRequest(
            recipient="user@",
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_empty_recipient():
    """NotificationEmailRequest rejects an empty recipient."""
    with pytest.raises(ValidationError, match="Recipient email address is required"):
        NotificationEmailRequest(
            recipient="",
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_short_recipient():
    """NotificationEmailRequest rejects recipient shorter than 5 characters."""
    with pytest.raises(ValidationError, match="too short"):
        NotificationEmailRequest(
            recipient="a@b",
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_long_recipient():
    """NotificationEmailRequest rejects recipient longer than 254 characters."""
    long_email = "a" * 245 + "@example.com"  # 257 chars total > 254
    with pytest.raises(ValidationError, match="too long"):
        NotificationEmailRequest(
            recipient=long_email,
            subject="Test",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_empty_subject():
    """NotificationEmailRequest rejects an empty subject."""
    with pytest.raises(ValidationError, match="Subject is required"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject="",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_short_subject():
    """NotificationEmailRequest rejects subject shorter than 3 characters."""
    with pytest.raises(ValidationError, match="too short"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject="Hi",
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_long_subject():
    """NotificationEmailRequest rejects subject longer than 255 characters."""
    long_subject = "S" * 256
    with pytest.raises(ValidationError, match="too long"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject=long_subject,
            html_template_code="otp",
            message_variables=[],
        )


def test_notification_email_request_rejects_empty_template_code():
    """NotificationEmailRequest rejects an empty html_template_code."""
    with pytest.raises(ValidationError, match="HTML template code is required"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject="Test",
            html_template_code="",
            message_variables=[],
        )


def test_notification_email_request_rejects_short_template_code():
    """NotificationEmailRequest rejects html_template_code shorter than 3 characters."""
    with pytest.raises(ValidationError, match="too short"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject="Test",
            html_template_code="ab",
            message_variables=[],
        )


def test_notification_email_request_rejects_long_template_code():
    """NotificationEmailRequest rejects html_template_code longer than 100 characters."""
    long_code = "t" * 101
    with pytest.raises(ValidationError, match="too long"):
        NotificationEmailRequest(
            recipient="user@example.com",
            subject="Test",
            html_template_code=long_code,
            message_variables=[],
        )


def test_notification_email_request_serializes_message_variables():
    """NotificationEmailRequest with multiple variables serializes correctly in get_content()."""
    request = NotificationEmailRequest(
        recipient="user@example.com",
        subject="Multi-var",
        html_template_code="otp",
        message_variables=[
            MessageVariables(key="%a%", value="1"),
            MessageVariables(key="%b%", value="2"),
            MessageVariables(key="%c%", value="3"),
        ],
    )
    data = json.loads(request.get_content())
    assert len(data["message_variables"]) == 3
    assert data["message_variables"][0] == {"key": "%a%", "value": "1"}
    assert data["message_variables"][2] == {"key": "%c%", "value": "3"}
