"""Integration tests for NotificationManagerService with real template loader and mocked notification service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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
def mock_notification_repository():
    repo = AsyncMock()
    repo.create_notification = AsyncMock()
    return repo


@pytest.fixture
def mock_notification_repository_factory(mock_notification_repository):
    return MagicMock(return_value=mock_notification_repository)


@pytest.fixture
def manager(
    real_template_loader,
    mock_notification_service,
    mock_notification_repository_factory,
):
    """NotificationManagerService wired with a real template loader and a mocked notification service."""
    return NotificationManagerService(
        notify_service=mock_notification_service,
        template_loader=real_template_loader,
        notification_repository_factory=mock_notification_repository_factory,
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
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_uses_real_template_loader_with_otp_template(
    mock_session_local, manager, mock_notification_service
):
    """send() loads the otp template from the real template directory and sends it."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

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
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_recover_password_template(
    mock_session_local, manager, mock_notification_service
):
    """send() loads the recovery_password template successfully."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

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
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_user_created_template(
    mock_session_local, manager, mock_notification_service
):
    """send() loads the user_created template successfully."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

    request = _make_email_request(
        html_template_code="user_created",
        message_variables=[MessageVariables(key="%name%", value="John")],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_item_created_template(
    mock_session_local,
    manager,
    mock_notification_service,
    mock_notification_repository_factory,
    mock_notification_repository,
):
    """send() loads the item_created template successfully and persists a notification."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

    request = _make_email_request(
        html_template_code="item_created",
        message_variables=[MessageVariables(key="%item_name%", value="Report")],
    )

    result = await manager.send(request)

    assert result is True
    mock_notification_service.send_notification.assert_awaited_once()
    # item_created has a summary message in MESSAGES, so insert_notification should be called
    mock_notification_repository_factory.assert_called_once_with(mock_session)
    mock_notification_repository.create_notification.assert_awaited_once()


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
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_notification_service_returns_false(
    mock_session_local, manager, mock_notification_service
):
    """send() returns False when the notification service fails to send."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session
    mock_notification_service.send_notification = AsyncMock(return_value=False)
    request = _make_email_request()

    result = await manager.send(request)

    assert result is False


@pytest.mark.asyncio
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_replaces_multiple_variables(
    mock_session_local, manager, mock_notification_service
):
    """send() replaces all message_variables in the template."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

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
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_send_replaces_variables_with_empty_list(
    mock_session_local, manager, mock_notification_service
):
    """send() works when there are no variables to replace."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

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


# ── New tests for get_summary_message() ──────────────────────────────────


def test_get_summary_message_returns_real_summary_for_known_template(manager):
    """get_summary_message() returns the real summary from MESSAGES for a known template."""
    result = manager.get_summary_message("item_created")
    assert result == "Un nuevo item ha sido creado."


def test_get_summary_message_returns_empty_for_unknown_template(manager):
    """get_summary_message() returns empty string for a template not in MESSAGES."""
    result = manager.get_summary_message("otp")
    assert result == ""


def test_get_summary_message_returns_empty_for_evaluation_end(manager):
    """get_summary_message() returns the real summary for evaluation_end template."""
    result = manager.get_summary_message("evaluation_end")
    assert result == "La evaluación ha sido completada."


# ── New tests for insert_notification() ──────────────────────────────────


@pytest.mark.asyncio
@patch("src.services.notification_manager_service.AsyncSessionLocal")
async def test_insert_notification_persists_notification_with_real_summary(
    mock_session_local,
    manager,
    mock_notification_repository_factory,
    mock_notification_repository,
):
    """insert_notification() creates a notification when the template has a real summary."""
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

    request = _make_email_request(html_template_code="item_created")

    await manager.insert_notification(request)

    mock_notification_repository_factory.assert_called_once_with(mock_session)
    mock_notification_repository.create_notification.assert_awaited_once()
    call_arg = mock_notification_repository.create_notification.call_args[0][0]
    assert call_arg.user_id == "user@example.com"
    assert call_arg.subject == "Test Subject"
    assert call_arg.message == "Un nuevo item ha sido creado."


@pytest.mark.asyncio
async def test_insert_notification_skips_when_no_summary(
    manager, mock_notification_repository_factory
):
    """insert_notification() does nothing when the template has no summary message."""
    request = _make_email_request(html_template_code="otp")

    await manager.insert_notification(request)

    mock_notification_repository_factory.assert_not_called()
