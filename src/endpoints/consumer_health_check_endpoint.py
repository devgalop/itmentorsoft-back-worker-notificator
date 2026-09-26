from typing_extensions import Annotated
from fastapi import HTTPException
from fastapi import APIRouter, Depends

from src.dependencies import get_template_loader
from src.services.template_loader import TemplateLoader

router = APIRouter()


@router.get(
    "/health",
    status_code=200,
    summary="Health check endpoint",
    description="Endpoint to check the health status of the consumer service",
    tags=["Health"],
    responses={200: {"service": "healthy"}, 503: {"service": "unhealthy"}},
)
async def health_check(
    template_loader: Annotated[TemplateLoader, Depends(get_template_loader)],
):
    template = template_loader.load("item_created")
    if not template:
        raise HTTPException(status_code=503, detail={"service": "unhealthy"})
    return {"service": "healthy"}
