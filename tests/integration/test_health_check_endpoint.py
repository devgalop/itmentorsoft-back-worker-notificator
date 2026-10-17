"""Integration tests for the health check endpoint."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch

from src.endpoints.consumer_health_check_endpoint import router as health_router
from src.services.template_loader import TemplateLoader


@pytest.fixture
def app_with_real_template_loader():
    """FastAPI app with health router and real TemplateLoader."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
def app_with_mocked_template_loader():
    """FastAPI app with health router and a mocked TemplateLoader dependency."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.mark.asyncio
async def test_health_check_returns_200_with_real_template(
    app_with_real_template_loader,
):
    """GET /health returns 200 when the item_created template loads successfully."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_real_template_loader),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_returns_503_when_template_empty(
    app_with_mocked_template_loader,
):
    """GET /health returns 503 when the template loader returns an empty/falsy value."""
    mock_loader = MagicMock(spec=TemplateLoader)
    mock_loader.load.return_value = ""

    app_with_mocked_template_loader.dependency_overrides[
        __import__(
            "src.dependencies", fromlist=["get_template_loader"]
        ).get_template_loader
    ] = lambda: mock_loader

    async with AsyncClient(
        transport=ASGITransport(app=app_with_mocked_template_loader),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"] == {"service": "unhealthy"}


@pytest.mark.asyncio
async def test_health_check_returns_503_when_template_none(
    app_with_mocked_template_loader,
):
    """GET /health returns 503 when the template loader returns None."""
    mock_loader = MagicMock(spec=TemplateLoader)
    mock_loader.load.return_value = None

    app_with_mocked_template_loader.dependency_overrides[
        __import__(
            "src.dependencies", fromlist=["get_template_loader"]
        ).get_template_loader
    ] = lambda: mock_loader

    async with AsyncClient(
        transport=ASGITransport(app=app_with_mocked_template_loader),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_health_check_response_structure(app_with_real_template_loader):
    """GET /health returns the expected JSON structure."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_real_template_loader),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    body = response.json()
    assert "service" in body
    assert body["service"] == "healthy"
