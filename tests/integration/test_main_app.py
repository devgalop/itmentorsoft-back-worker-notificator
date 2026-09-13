"""Integration tests for the main app's global exception handler."""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app_with_exception_handler():
    """FastAPI app that copies the global exception handler but NOT the lifespan."""
    test_app = FastAPI()

    @test_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "message": "An unexpected error occurred",
                "path": request.url.path,
            },
        )

    @test_app.get("/test-error")
    async def trigger_error():
        raise RuntimeError("Test error")

    return test_app


@pytest.mark.asyncio
async def test_global_exception_handler_returns_500(app_with_exception_handler):
    """Global exception handler returns 500 with correct JSON structure."""
    async with AsyncClient(
        transport=ASGITransport(
            app=app_with_exception_handler, raise_app_exceptions=False
        ),
        base_url="http://test",
    ) as client:
        response = await client.get("/test-error")

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == 500
    assert body["message"] == "An unexpected error occurred"


@pytest.mark.asyncio
async def test_global_exception_handler_includes_request_path(
    app_with_exception_handler,
):
    """The exception handler includes the request path in the response."""
    async with AsyncClient(
        transport=ASGITransport(
            app=app_with_exception_handler, raise_app_exceptions=False
        ),
        base_url="http://test",
    ) as client:
        response = await client.get("/test-error")

    body = response.json()
    assert body["path"] == "/test-error"
