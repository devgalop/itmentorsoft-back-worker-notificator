"""Integration tests for NotificationManagerService with real template loader and mocked notification service."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.notification_manager_service import NotificationManagerService
from src.services.template_loader import TemplateLoader
from src.models.notification_email_request import (
    NotificationEmailRequest,
    MessageVariables,
)
from src.contracts.notification_service import NotificationConfig, NotificationService


@pytest.fixture
def real_template_loader():
    """TemplateLoader that reads actual templates from the assets/templates directory."""
    return TemplateLoader()


@pytest.fixture
def mock_notification_service():
    """Mock NotificationService that records send calls."""
    service = MagicMock(spec=NotificationService)
    service.send_notification = AsyncMock(return_value=True)
    return service


@pytest.fixture
def manager(real_template_loader, mock_notification_service):
    """NotificationManagerService wired with a real template loader and a mocked notification service."""
    return NotificationManagerService(
        notify_service=mock_notification_service,
        template_loader=real_template_loader,
    )


def _make_email_request(
    recipient="user@example.com",
    subject="Test Subject",
    html_template_code="otp",
    message_variables=None,
):
    """Build a NotificationEmailRequest with the given parameters."""
    if message_variables is None:
        message_variables = [
            MessageVariables(key="%code%", value="654321"),
        ]
    return NotificationEmailRequest(
        recipient=recipient,
        subject=subject,
        html_template_code=html_template_code,
        message_variables=message_variables,
    )


@pytest.mark.asyncio
async def test_send_uses_real_template_loader_with_otp_template(
    manager, mock_notification_service
):
    """send() loads the otp template from the real template directory and sends it."""
    request = _make_email_request(
        html_template_code="otp",
        message_variables=[
            MessageVariables(key="%OTP_CODE%", value="654321"),
            MessageVariables(key="%USER%", value="Test User"),
        ],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()
    config = mock_notification_service.send_notification.call_args[0][0]
    assert isinstance(config, NotificationConfig)
    assert config.destination == "user@example.com"
    assert config.subject == "Test Subject"
    assert "%OTP_CODE%" not in config.template  # variable was replaced
    assert "654321" in config.template


@pytest.mark.asyncio
async def test_send_recover_password_template(manager, mock_notification_service):
    """send() loads the recovery_password template successfully."""
    request = _make_email_request(
        html_template_code="recovery_password",
        message_variables=[
            MessageVariables(key="%URL_BASE%", value="https://example.com/reset"),
            MessageVariables(key="%URL_TOKEN%", value="abc123"),
            MessageVariables(key="%ID_TRX%", value="trx-001"),
            MessageVariables(key="%USER%", value="Test User"),
        ],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()
    config = mock_notification_service.send_notification.call_args[0][0]
    assert "%URL_BASE%" not in config.template
    assert "https://example.com/reset" in config.template


@pytest.mark.asyncio
async def test_send_user_created_template(manager, mock_notification_service):
    """send() loads the user_created template successfully."""
    request = _make_email_request(
        html_template_code="user_created",
        message_variables=[MessageVariables(key="%name%", value="John")],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_item_created_template(manager, mock_notification_service):
    """send() loads the item_created template successfully."""
    request = _make_email_request(
        html_template_code="item_created",
        message_variables=[MessageVariables(key="%item_name%", value="Report")],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_template_not_found_returns_false(
    manager, mock_notification_service
):
    """send() returns False when the template does not exist."""
    request = _make_email_request(html_template_code="nonexistent_template")

    result = await manager.send(request)

    assert result is False
    mock_notification_service.send_notification.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_notification_service_returns_false(
    manager, mock_notification_service
):
    """send() returns False when the notification service fails to send."""
    mock_notification_service.send_notification = AsyncMock(return_value=False)
    request = _make_email_request()

    result = await manager.send(request)

    assert result is False


@pytest.mark.asyncio
async def test_send_replaces_multiple_variables(manager, mock_notification_service):
    """send() replaces all message_variables in the template."""
    request = _make_email_request(
        message_variables=[
            MessageVariables(key="%USER%", value="Alice"),
            MessageVariables(key="%OTP_CODE%", value="111"),
        ],
    )

    result = await manager.send(request)

    assert result is True
    config = mock_notification_service.send_notification.call_args[0][0]
    assert "%USER%" not in config.template
    assert "%OTP_CODE%" not in config.template
    assert "Alice" in config.template
    assert "111" in config.template


@pytest.mark.asyncio
async def test_send_replaces_variables_with_empty_list(
    manager, mock_notification_service
):
    """send() works when there are no variables to replace."""
    request = _make_email_request(message_variables=[])

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()


def test_replace_variables_replaces_all(manager):
    """replace_variables substitutes every variable key with its value."""
    html = "<p>Hello %name%, your code is %code%.</p>"
    request = _make_email_request(
        message_variables=[
            MessageVariables(key="%name%", value="Bob"),
            MessageVariables(key="%code%", value="999"),
        ],
    )

    result = manager.replace_variables(html, request)

    assert result == "<p>Hello Bob, your code is 999.</p>"


def test_replace_variables_empty_list_returns_original(manager):
    """replace_variables returns the original content when there are no variables."""
    html = "<p>No variables here.</p>"
    request = _make_email_request(message_variables=[])

    result = manager.replace_variables(html, request)

    assert result == html


def test_replace_variables_no_match_returns_original(manager):
    """replace_variables returns content unchanged when no variables match."""
    html = "<p>Nothing to replace.</p>"
    request = _make_email_request(
        message_variables=[MessageVariables(key="%xyz%", value="value")],
    )

    result = manager.replace_variables(html, request)

    assert result == html
