
"""FastAPI application entry point for the AI Automation System."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from api.webhooks import router as webhook_router
from config import settings
from utils.logger import setup_logger


# --------------------------------------------------
# LOGGER
# --------------------------------------------------

logger = setup_logger()


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

def get_allowed_origins() -> list[str]:
    """Read explicitly allowed browser origins from the environment."""

    configured_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )

    return [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]


# --------------------------------------------------
# APPLICATION LIFESPAN
# --------------------------------------------------

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log application startup and shutdown events."""

    logger.info("AI Automation System starting")

    try:
        yield
    finally:
        logger.info("AI Automation System shutting down")


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered customer support and business automation system."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS MIDDLEWARE
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Webhook-Secret"],
)


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(
    api_router,
    prefix="/api",
    tags=["API"],
)

app.include_router(
    webhook_router,
    prefix="/webhooks",
    tags=["Webhooks"],
)


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Return basic application information."""

    return {
        "name": settings.APP_NAME,
        "status": "running",
        "version": settings.APP_VERSION,
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Return the application health status."""

    return {"status": "healthy"}
