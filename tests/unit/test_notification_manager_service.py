import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.notification_manager_service import NotificationManagerService
from src.models.notification_email_request import (
    NotificationEmailRequest,
    MessageVariables,
)


def _make_request(variables=None):
    return NotificationEmailRequest(
        recipient="alice@example.com",
        subject="Test",
        html_template_code="WELCOME",
        message_variables=variables or [],
    )


class TestNotificationManagerService:
    @pytest.fixture
    def mock_notify_service(self):
        svc = MagicMock()
        svc.send_notification = AsyncMock()
        return svc

    @pytest.fixture
    def mock_template_loader(self):
        loader = MagicMock()
        # Return empty summary by default so insert_notification short-circuits
        # and existing send() tests don't need a real DB session.
        loader.get_summary_message.return_value = ""
        return loader

    @pytest.fixture
    def mock_notification_repository(self):
        repo = AsyncMock()
        repo.create_notification = AsyncMock()
        return repo

    @pytest.fixture
    def mock_notification_repository_factory(self, mock_notification_repository):
        return MagicMock(return_value=mock_notification_repository)

    @pytest.fixture
    def service(
        self,
        mock_notify_service,
        mock_template_loader,
        mock_notification_repository_factory,
    ):
        return NotificationManagerService(
            notify_service=mock_notify_service,
            template_loader=mock_template_loader,
            notification_repository_factory=mock_notification_repository_factory,
        )

    # ── send() success ────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_send_success(
        self, service, mock_notify_service, mock_template_loader
    ):
        mock_template_loader.load.return_value = "<h1>%NAME%</h1>"
        mock_notify_service.send_notification.return_value = True

        req = _make_request([MessageVariables(key="%NAME%", value="Alice")])
        result = await service.send(req)

        assert result is True
        mock_template_loader.load.assert_called_once_with("WELCOME")
        mock_notify_service.send_notification.assert_awaited_once()

    # ── send() returns False on FileNotFoundError ─────────────────────────
    @pytest.mark.asyncio
    async def test_send_returns_false_when_template_not_found(
        self, service, mock_template_loader, mock_notify_service
    ):
        mock_template_loader.load.side_effect = FileNotFoundError("missing")

        req = _make_request()
        result = await service.send(req)

        assert result is False
        mock_notify_service.send_notification.assert_not_awaited()

    # ── send() returns False when notify service fails ────────────────────
    @pytest.mark.asyncio
    async def test_send_returns_false_when_notify_service_fails(
        self, service, mock_notify_service, mock_template_loader
    ):
        mock_template_loader.load.return_value = "<p>OK</p>"
        mock_notify_service.send_notification.return_value = False

        req = _make_request()
        result = await service.send(req)

        assert result is False

    # ── replace_variables ─────────────────────────────────────────────────
    def test_replace_variables_replaces_all(self, service):
        html = "<h1>%NAME%</h1><p>%CODE%</p>"
        req = _make_request(
            [
                MessageVariables(key="%NAME%", value="Alice"),
                MessageVariables(key="%CODE%", value="42"),
            ]
        )
        result = service.replace_variables(html, req)
        assert result == "<h1>Alice</h1><p>42</p>"

    def test_replace_variables_no_variables_returns_original(self, service):
        html = "<h1>Hello</h1>"
        req = _make_request([])
        result = service.replace_variables(html, req)
        assert result == html

    def test_replace_variables_single(self, service):
        html = "Welcome %USER%!"
        req = _make_request([MessageVariables(key="%USER%", value="Bob")])
        result = service.replace_variables(html, req)
        assert result == "Welcome Bob!"

    # ── get_summary_message() ─────────────────────────────────────────────
    def test_get_summary_message_returns_message_from_loader(
        self, service, mock_template_loader
    ):
        mock_template_loader.get_summary_message.return_value = (
            "Un nuevo item ha sido creado."
        )
        result = service.get_summary_message("item_created")
        assert result == "Un nuevo item ha sido creado."
        mock_template_loader.get_summary_message.assert_called_once_with("item_created")

    def test_get_summary_message_returns_empty_when_not_found(
        self, service, mock_template_loader
    ):
        mock_template_loader.get_summary_message.return_value = ""
        result = service.get_summary_message("unknown_template")
        assert result == ""

    # ── insert_notification() ─────────────────────────────────────────────
    @pytest.mark.asyncio
    @patch("src.services.notification_manager_service.AsyncSessionLocal")
    async def test_insert_notification_creates_notification_when_summary_exists(
        self,
        mock_session_local,
        service,
        mock_notification_repository_factory,
        mock_notification_repository,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        req = _make_request()
        # Manually set get_summary_message to return a real string
        service.template_loader.get_summary_message.return_value = (
            "Test summary message"
        )

        await service.insert_notification(req)

        mock_notification_repository_factory.assert_called_once_with(mock_session)
        mock_notification_repository.create_notification.assert_awaited_once()
        call_arg = mock_notification_repository.create_notification.call_args[0][0]
        assert call_arg.user_id == "alice@example.com"
        assert call_arg.subject == "Test"
        assert call_arg.message == "Test summary message"

    @pytest.mark.asyncio
    async def test_insert_notification_skips_when_summary_is_empty(
        self, service, mock_notification_repository_factory
    ):
        service.template_loader.get_summary_message.return_value = ""
        req = _make_request()

        await service.insert_notification(req)

        mock_notification_repository_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_insert_notification_skips_when_summary_is_whitespace(
        self, service, mock_notification_repository_factory
    ):
        service.template_loader.get_summary_message.return_value = "   "
        req = _make_request()

        await service.insert_notification(req)

        mock_notification_repository_factory.assert_not_called()

    # ── send() calls insert_notification before sending ───────────────────
    @pytest.mark.asyncio
    @patch("src.services.notification_manager_service.AsyncSessionLocal")
    async def test_send_calls_insert_notification_before_sending(
        self,
        mock_session_local,
        service,
        mock_notify_service,
        mock_template_loader,
        mock_notification_repository_factory,
        mock_notification_repository,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session
        mock_template_loader.load.return_value = "<p>Hello</p>"
        mock_template_loader.get_summary_message.return_value = "A notification"
        mock_notify_service.send_notification.return_value = True

        req = _make_request()
        result = await service.send(req)

        assert result is True
        mock_notification_repository_factory.assert_called_once_with(mock_session)
        mock_notification_repository.create_notification.assert_awaited_once()
        mock_notify_service.send_notification.assert_awaited_once()
