import pytest
from unittest.mock import AsyncMock, MagicMock

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
        return MagicMock()

    @pytest.fixture
    def service(self, mock_notify_service, mock_template_loader):
        return NotificationManagerService(
            notify_service=mock_notify_service,
            template_loader=mock_template_loader,
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
