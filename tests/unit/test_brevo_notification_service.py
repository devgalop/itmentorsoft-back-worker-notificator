import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.contracts.notification_service import NotificationConfig
from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
    BrevoNotificationBody,
    BrevoNotificationUser,
    BrevoNotificationHeader,
)


def _make_config():
    return NotificationConfig(
        sender="sender@test.com",
        destination="dest@test.com",
        subject="Subject",
    )


class TestBrevoNotificationPayload:
    def test_to_brevo_payload_structure(self):
        svc = BrevoNotificationService()
        cfg = _make_config()
        cfg.template = "<h1>Hello</h1>"

        body = svc.to_brevo_payload(cfg)

        assert isinstance(body, BrevoNotificationBody)
        assert body.sender.email == "sender@test.com"
        assert len(body.to) == 1
        assert body.to[0].email == "dest@test.com"
        assert body.subject == "Subject"
        assert body.htmlContent == "<h1>Hello</h1>"
        assert isinstance(body.headers, BrevoNotificationHeader)
        assert body.headers.idempotencyKey == cfg.uuid

    def test_to_brevo_payload_empty_template(self):
        svc = BrevoNotificationService()
        cfg = _make_config()
        cfg.template = None

        body = svc.to_brevo_payload(cfg)
        assert body.htmlContent == ""


class _FakeResponse:
    """Synchronous stand-in for an aiohttp response used inside async-with."""

    def __init__(self, status, json_data):
        self.status = status
        self._json_data = json_data

    async def json(self):
        return self._json_data


class _FakeSession:
    """Synchronous stand-in for aiohttp.ClientSession."""

    def __init__(self, response):
        self._response = response

    def post(self, *args, **kwargs):
        return _FakeCtxManager(self._response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass


class _FakeCtxManager:
    """Implements the async-context-manager protocol for `async with session.post(...)`."""

    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc):
        pass


class TestBrevoNotificationService:
    VALID_API_KEY = "test-api-key-123"
    VALID_API_URL = "https://api.brevo.com/v3"

    def _patch_env(self, monkeypatch):
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_API_KEY",
            self.VALID_API_KEY,
        )
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_BASE_API_URL",
            self.VALID_API_URL,
        )

    # ── send_notification success ─────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_send_notification_success(self, monkeypatch):
        self._patch_env(monkeypatch)

        fake_response = _FakeResponse(status=201, json_data={"messageId": "<msg-id>"})
        fake_session = _FakeSession(fake_response)

        with patch(
            "src.infrastructure.notificator.brevo_notification_service.aiohttp.ClientSession",
            return_value=fake_session,
        ):
            svc = BrevoNotificationService()
            cfg = _make_config()
            cfg.template = "<h1>Hello</h1>"
            result = await svc.send_notification(cfg)

        assert result is True

    # ── send_notification returns False on non-201 ────────────────────────
    @pytest.mark.asyncio
    async def test_send_notification_returns_false_on_non_201(self, monkeypatch):
        self._patch_env(monkeypatch)

        fake_response = _FakeResponse(status=400, json_data={"message": "Bad request"})
        fake_session = _FakeSession(fake_response)

        with patch(
            "src.infrastructure.notificator.brevo_notification_service.aiohttp.ClientSession",
            return_value=fake_session,
        ):
            svc = BrevoNotificationService()
            cfg = _make_config()
            cfg.template = "<h1>Hello</h1>"
            result = await svc.send_notification(cfg)

        assert result is False

    # ── raises when BREVO_API_KEY missing ─────────────────────────────────
    @pytest.mark.asyncio
    async def test_send_notification_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_API_KEY",
            "",
        )
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_BASE_API_URL",
            self.VALID_API_URL,
        )

        svc = BrevoNotificationService()
        cfg = _make_config()
        cfg.template = "<h1>Hello</h1>"

        with pytest.raises(EnvironmentError, match="BREVO_API_KEY"):
            await svc.send_notification(cfg)

    # ── raises when BREVO_BASE_API_URL missing ────────────────────────────
    @pytest.mark.asyncio
    async def test_send_notification_raises_when_api_url_missing(self, monkeypatch):
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_API_KEY",
            self.VALID_API_KEY,
        )
        monkeypatch.setattr(
            "src.infrastructure.notificator.brevo_notification_service.EnvironmentVariablesConstants.BREVO_BASE_API_URL",
            "",
        )

        svc = BrevoNotificationService()
        cfg = _make_config()
        cfg.template = "<h1>Hello</h1>"

        with pytest.raises(EnvironmentError, match="BREVO_BASE_API_URL"):
            await svc.send_notification(cfg)
