"""Integration tests for SqsNotificatorConsumer.process_message()."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from common_py_aws import SqsMessageReceived

from src.infrastructure.broker.aws.aws_sqs_notificator_consumer import (
    SqsNotificatorConsumer,
)
from src.models.notification_email_request import NotificationEmailRequest


def _make_valid_message_body():
    """Return a valid JSON string for NotificationEmailRequest."""
    return json.dumps(
        {
            "recipient": "user@example.com",
            "subject": "Test Notification",
            "html_template_code": "otp",
            "message_variables": [
                {"key": "%code%", "value": "123456"},
            ],
        }
    )


@pytest.fixture
def mock_sanitizer():
    """Mock MessageSanitizer that returns a sanitized InputMessage."""
    sanitizer = MagicMock()
    sanitized = MagicMock()
    sanitized.get_content.return_value = _make_valid_message_body()
    sanitizer.sanitize.return_value = sanitized
    return sanitizer


@pytest.fixture
def mock_notification_manager():
    """Mock NotificationManagerService with async send method."""
    manager = MagicMock()
    manager.send = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def consumer(mock_sanitizer, mock_notification_manager):
    """SqsNotificatorConsumer with mocked dependencies."""
    return SqsNotificatorConsumer(
        message_sanitizer=mock_sanitizer,
        notification_manager_service=mock_notification_manager,
    )


def _make_sqs_message(body: str) -> SqsMessageReceived:
    """Create a real SqsMessageReceived instance."""
    return SqsMessageReceived(
        message_id="test-msg-id",
        body=body,
        receipt_handle="test-receipt-handle",
    )


@pytest.mark.asyncio
async def test_process_message_valid_returns_true(
    consumer, mock_sanitizer, mock_notification_manager
):
    """process_message with valid message returns True."""
    message = _make_sqs_message(_make_valid_message_body())

    result = await consumer.process_message(message)

    assert result is True
    mock_sanitizer.sanitize.assert_called_once_with(message.body)
    mock_notification_manager.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_message_sanitizer_raises_valueerror_returns_false(
    consumer, mock_sanitizer
):
    """process_message with invalid message (ValueError from sanitizer) returns False."""
    mock_sanitizer.sanitize.side_effect = ValueError("Invalid message format")
    message = _make_sqs_message("not valid json")

    result = await consumer.process_message(message)

    assert result is False


@pytest.mark.asyncio
async def test_process_message_notification_manager_returns_false(
    consumer, mock_notification_manager
):
    """process_message when notification_manager.send returns False returns False."""
    mock_notification_manager.send.return_value = False
    message = _make_sqs_message(_make_valid_message_body())

    result = await consumer.process_message(message)

    assert result is False


@pytest.mark.asyncio
async def test_process_message_calls_sanitizer_with_body(
    consumer, mock_sanitizer, mock_notification_manager
):
    """process_message calls sanitizer.sanitize with message.body."""
    body = _make_valid_message_body()
    message = _make_sqs_message(body)

    await consumer.process_message(message)

    mock_sanitizer.sanitize.assert_called_once_with(body)


@pytest.mark.asyncio
async def test_process_message_calls_notification_manager_with_correct_request(
    consumer, mock_sanitizer, mock_notification_manager
):
    """process_message calls notification_manager.send with correct NotificationEmailRequest."""
    body = _make_valid_message_body()
    message = _make_sqs_message(body)

    await consumer.process_message(message)

    mock_notification_manager.send.assert_awaited_once()
    call_args = mock_notification_manager.send.call_args[0][0]
    assert isinstance(call_args, NotificationEmailRequest)
    assert call_args.recipient == "user@example.com"
    assert call_args.subject == "Test Notification"
    assert call_args.html_template_code == "otp"
    assert len(call_args.message_variables) == 1
    assert call_args.message_variables[0].key == "%code%"
    assert call_args.message_variables[0].value == "123456"
