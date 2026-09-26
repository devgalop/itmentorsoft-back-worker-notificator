"""Integration tests for the dependency injection system in dependencies.py."""

import pytest
from fastapi import FastAPI, Depends
from httpx import AsyncClient, ASGITransport

from src.dependencies import (
    get_message_sanitizer,
    get_notification_service,
    get_template_loader,
    get_notification_manager_service,
)
from src.services.notification_message_sanitizer import NotificationMessageSanitizer
from src.services.template_loader import TemplateLoader
from src.services.notification_manager_service import NotificationManagerService
from src.contracts.notification_service import NotificationService
from src.infrastructure.notificator.brevo_notification_service import (
    BrevoNotificationService,
)


def test_get_message_sanitizer_returns_concrete_instance():
    """get_message_sanitizer returns a NotificationMessageSanitizer implementing MessageSanitizer."""
    result = get_message_sanitizer()
    assert isinstance(result, NotificationMessageSanitizer)


def test_get_template_loader_returns_concrete_instance():
    """get_template_loader returns a TemplateLoader."""
    result = get_template_loader()
    assert isinstance(result, TemplateLoader)


def test_get_notification_service_returns_concrete_instance():
    """get_notification_service returns a BrevoNotificationService implementing NotificationService."""
    result = get_notification_service()
    assert isinstance(result, BrevoNotificationService)
    assert isinstance(result, NotificationService)


def test_get_notification_manager_service_wires_dependencies():
    """get_notification_manager_service receives the two annotated dependencies and returns a NotificationManagerService."""
    notify_service = get_notification_service()
    template_loader = get_template_loader()
    result = get_notification_manager_service(notify_service, template_loader)
    assert isinstance(result, NotificationManagerService)
    assert result.notify_service is notify_service
    assert result.template_loader is template_loader


@pytest.fixture
def di_test_app():
    """FastAPI app that exercises all dependency functions through endpoints."""
    app = FastAPI()

    @app.get("/di/sanitizer")
    def diagnose_sanitizer(sanitizer=Depends(get_message_sanitizer)):
        return {"type": type(sanitizer).__name__}

    @app.get("/di/template-loader")
    def diagnose_template_loader(loader=Depends(get_template_loader)):
        return {"type": type(loader).__name__}

    @app.get("/di/notification-service")
    def diagnose_notification_service(service=Depends(get_notification_service)):
        return {"type": type(service).__name__}

    @app.get("/di/manager-service")
    def diagnose_manager_service(service=Depends(get_notification_manager_service)):
        return {"type": type(service).__name__}

    return app


@pytest.mark.asyncio
async def test_fastapi_injects_message_sanitizer(di_test_app):
    """FastAPI dependency injection resolves get_message_sanitizer through an endpoint."""
    async with AsyncClient(
        transport=ASGITransport(app=di_test_app), base_url="http://test"
    ) as client:
        response = await client.get("/di/sanitizer")
    assert response.status_code == 200
    assert response.json()["type"] == "NotificationMessageSanitizer"


@pytest.mark.asyncio
async def test_fastapi_injects_template_loader(di_test_app):
    """FastAPI dependency injection resolves get_template_loader through an endpoint."""
    async with AsyncClient(
        transport=ASGITransport(app=di_test_app), base_url="http://test"
    ) as client:
        response = await client.get("/di/template-loader")
    assert response.status_code == 200
    assert response.json()["type"] == "TemplateLoader"


@pytest.mark.asyncio
async def test_fastapi_injects_notification_service(di_test_app):
    """FastAPI dependency injection resolves get_notification_service through an endpoint."""
    async with AsyncClient(
        transport=ASGITransport(app=di_test_app), base_url="http://test"
    ) as client:
        response = await client.get("/di/notification-service")
    assert response.status_code == 200
    assert response.json()["type"] == "BrevoNotificationService"


@pytest.mark.asyncio
async def test_fastapi_injects_notification_manager_service(di_test_app):
    """FastAPI dependency injection resolves get_notification_manager_service through an endpoint.

    This endpoint transitively exercises get_notification_service and
    get_template_loader because the manager service Depends on them.
    """
    async with AsyncClient(
        transport=ASGITransport(app=di_test_app), base_url="http://test"
    ) as client:
        response = await client.get("/di/manager-service")
    assert response.status_code == 200
    assert response.json()["type"] == "NotificationManagerService"
