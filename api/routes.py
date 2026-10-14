
"""System status, health, and application information routes."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from config import settings


router = APIRouter(tags=["System"])


@router.get("/status")
async def system_status() -> dict[str, object]:
    """Return application status and runtime configuration."""

    return {
        "success": True,
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
    }


@router.get("/health")
async def health_check(
    response: Response,
) -> dict[str, str]:
    """Return a lightweight health-check response."""

    response.status_code = status.HTTP_200_OK

    return {"status": "healthy"}


@router.get("/info")
async def system_info() -> dict[str, str]:
    """Return basic application metadata."""

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
