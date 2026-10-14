
"""
Outgoing webhook integration.

Sends customer-support events to configured HTTP endpoints
with input validation, bounded timeouts, and safe error handling.
"""

import logging
from typing import Any
from urllib.parse import urlsplit

import requests

from config import settings


logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10

WEBHOOK_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# ============================================================
# Validation
# ============================================================

def _validate_event(event: str) -> str:
    """Validate and normalize an event name."""

    if not isinstance(event, str) or not event.strip():
        raise ValueError("Webhook event cannot be empty.")

    return event.strip()


def _validate_payload(data: dict[str, Any]) -> None:
    """Validate the top-level webhook payload."""

    if not isinstance(data, dict):
        raise ValueError("Webhook data must be a dictionary.")


def _validate_webhook_url(url: str) -> str:
    """
    Validate the webhook destination URL.

    Only HTTP and HTTPS URLs with a hostname are accepted.
    URLs containing embedded credentials are rejected.
    """

    if not isinstance(url, str) or not url.strip():
        raise RuntimeError("Webhook URL is not configured.")

    url = url.strip()

    try:
        parsed = urlsplit(url)
        # Accessing port also validates malformed port values.
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("Webhook URL is invalid.") from exc

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("Webhook URL is invalid.")

    return url


def _resolve_webhook_url(
    webhook_url: str | None = None,
) -> str:
    """Resolve the explicit URL or configured default."""

    configured_url = getattr(settings, "WEBHOOK_URL", "")
    url = webhook_url if webhook_url is not None else configured_url

    if not url:
        raise RuntimeError("Webhook URL is not configured.")

    return _validate_webhook_url(url)


# ============================================================
# Send Webhook
# ============================================================

def send_webhook(
    event: str,
    data: dict[str, Any],
    webhook_url: str | None = None,
) -> bool:
    """
    Send an event to an external webhook endpoint.

    Returns:
        True if the endpoint responds with a successful HTTP status.

    Raises:
        ValueError: If the event, payload, or URL is invalid.
        RuntimeError: If configuration or delivery fails.
    """

    event_name = _validate_event(event)
    _validate_payload(data)
    url = _resolve_webhook_url(webhook_url)

    payload = {
        "event": event_name,
        "data": data,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=WEBHOOK_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()

        logger.info(
            "Webhook delivered successfully. event=%s",
            event_name,
        )

        return True

    except requests.Timeout as exc:
        logger.error(
            "Webhook delivery timed out. event=%s",
            event_name,
        )
        raise RuntimeError(
            "Webhook request timed out."
        ) from exc

    except requests.RequestException as exc:
        logger.error(
            "Webhook delivery failed. event=%s error_type=%s",
            event_name,
            type(exc).__name__,
        )
        raise RuntimeError(
            "Unable to send webhook."
        ) from exc


# ============================================================
# Convenience Functions
# ============================================================

def send_refund_webhook(
    order_id: str,
    customer_id: str,
    status: str,
) -> bool:
    """Send a refund-status update webhook."""

    return send_webhook(
        event="refund_updated",
        data={
            "order_id": order_id,
            "customer_id": customer_id,
            "status": status,
        },
    )


def send_escalation_webhook(
    escalation_id: str,
    customer_id: str,
    priority: str,
) -> bool:
    """Send a customer-escalation webhook."""

    return send_webhook(
        event="customer_escalated",
        data={
            "escalation_id": escalation_id,
            "customer_id": customer_id,
            "priority": priority,
        },
    )
