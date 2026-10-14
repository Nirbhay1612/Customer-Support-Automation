
"""Webhook endpoints for external services and automation tools."""

from __future__ import annotations

import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from config import settings


router = APIRouter(tags=["Webhooks"])


ALLOWED_EVENTS = frozenset(
    {
        "order_created",
        "order_updated",
        "refund_requested",
        "refund_completed",
        "customer_escalated",
    }
)


class WebhookPayload(BaseModel):
    """Validated payload accepted by the generic webhook endpoint."""

    event: str = Field(..., min_length=1, max_length=100)
    data: dict[str, Any] = Field(default_factory=dict)


@router.post("/events", status_code=status.HTTP_200_OK)
async def receive_webhook(
    payload: WebhookPayload,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    """Authenticate and validate an incoming webhook event."""

    configured_secret = settings.WEBHOOK_SECRET

    # Preserve the existing optional-secret configuration behavior.
    # Configure WEBHOOK_SECRET before exposing this endpoint publicly.
    if configured_secret:
        if not x_webhook_secret or not hmac.compare_digest(
            x_webhook_secret,
            configured_secret,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret.",
            )

    event = payload.event.strip()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event must not be empty.",
        )

    if event not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported event.",
        )

    # TODO: Dispatch the validated event to the automation layer.
    # Do not report that the event was processed until dispatch succeeds.

    return {
        "success": True,
        "event": event,
        "message": "Webhook received successfully.",
    }
