"""Integration tests for the consumer management endpoints."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

from src.endpoints.init import router as endpoints_router


@pytest.fixture
def test_app():
    """Build a minimal FastAPI app with only the endpoint routers and mocked SQS consumer."""
    app = FastAPI()
    app.include_router(endpoints_router, prefix="/api")

    mock_consumer = MagicMock()
    mock_consumer.sqs_config = MagicMock()
    mock_consumer.sqs_config.is_enabled = True
    app.state.sqs_consumer = mock_consumer

    return app


@pytest.mark.asyncio
async def test_consumer_status_returns_enabled_when_true(test_app):
    """GET /api/consumer/status returns 200 with is_enabled=True when consumer is enabled."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/api/consumer/status")

    assert response.status_code == 200
    body = response.json()
    assert body["is_enabled"] is True
    assert body["message"] == "Consumer is enabled"


@pytest.mark.asyncio
async def test_consumer_status_returns_disabled_when_false(test_app):
    """GET /api/consumer/status returns 200 with is_enabled=False when consumer is disabled."""
    test_app.state.sqs_consumer.sqs_config.is_enabled = False

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/api/consumer/status")

    assert response.status_code == 200
    body = response.json()
    assert body["is_enabled"] is False
    assert body["message"] == "Consumer is disabled"


@pytest.mark.asyncio
async def test_consumer_enable_with_status_true(test_app):
    """GET /api/consumer/enable?status=true returns 200 with is_enabled=True."""
    test_app.state.sqs_consumer.sqs_config.is_enabled = False

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/api/consumer/enable", params={"status": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["is_enabled"] is True
    assert body["message"] == "Consumer enabled successfully"


@pytest.mark.asyncio
async def test_consumer_enable_with_status_false(test_app):
    """GET /api/consumer/enable?status=false returns 200 with is_enabled=False."""
    test_app.state.sqs_consumer.sqs_config.is_enabled = True

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/api/consumer/enable", params={"status": "false"})

    assert response.status_code == 200
    body = response.json()
    assert body["is_enabled"] is False
    assert body["message"] == "Consumer disabled successfully"


@pytest.mark.asyncio
async def test_consumer_enable_then_status_reflects_change(test_app):
    """Toggling enable then checking status reflects the change."""
    # Start with enabled = True
    test_app.state.sqs_consumer.sqs_config.is_enabled = True

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Disable the consumer
        response = await client.get("/api/consumer/enable", params={"status": "false"})
        assert response.status_code == 200
        assert response.json()["is_enabled"] is False

        # Check status reflects the change
        status_response = await client.get("/api/consumer/status")
        assert status_response.status_code == 200
        assert status_response.json()["is_enabled"] is False
        assert status_response.json()["message"] == "Consumer is disabled"

        # Re-enable the consumer
        enable_response = await client.get(
            "/api/consumer/enable", params={"status": "true"}
        )
        assert enable_response.status_code == 200
        assert enable_response.json()["is_enabled"] is True

        # Verify status is back to enabled
        final_status = await client.get("/api/consumer/status")
        assert final_status.status_code == 200
        assert final_status.json()["is_enabled"] is True
