
"""
Notification handler for the AI Customer Support Automation system.

Routes escalation, refund, order, and general notifications
through the email integration.
"""

import logging
from typing import Any

from config import settings
from integrations.email import send_email


logger = logging.getLogger(__name__)

# Prefer configured support email; retain the original fallback.
SUPPORT_EMAIL = getattr(
    settings,
    "SUPPORT_EMAIL",
    "support@example.com",
)

SUPPORTED_NOTIFICATION_TYPES = {
    "escalation",
    "refund",
    "order",
    "general",
}


# ============================================================
# Main Notification Handler
# ============================================================

def handle_notification(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle supported system notification types.

    Supported types:
        escalation, refund, order, general
    """

    if not isinstance(data, dict):
        return {
            "success": False,
            "status": "invalid_input",
            "message": "Notification data must be a dictionary.",
        }

    notification_type = data.get("type", "general")

    if not isinstance(notification_type, str):
        return {
            "success": False,
            "status": "invalid_type",
            "message": "Notification type must be a string.",
        }

    notification_type = notification_type.strip().lower()

    if notification_type not in SUPPORTED_NOTIFICATION_TYPES:
        return {
            "success": False,
            "status": "unsupported_type",
            "message": "Notification type is not supported.",
        }

    handlers = {
        "escalation": _send_escalation_notification,
        "refund": _send_refund_notification,
        "order": _send_order_notification,
        "general": _send_general_notification,
    }

    try:
        return handlers[notification_type](data)

    except Exception as exc:
        logger.error(
            "Notification failed. type=%s error_type=%s",
            notification_type,
            type(exc).__name__,
        )

        return {
            "success": False,
            "status": "notification_failed",
            "message": "Notification could not be sent.",
        }


# ============================================================
# Shared Helpers
# ============================================================

def _required_text(
    data: dict[str, Any],
    field: str,
) -> str | None:
    """Return a non-empty string, or None when invalid/missing."""

    value = data.get(field)

    if not isinstance(value, str) or not value.strip():
        return None

    return value.strip()


def _notification_result(
    notification_type: str,
) -> dict[str, Any]:
    """Build a successful notification result."""

    return {
        "success": True,
        "status": "notification_sent",
        "type": notification_type,
    }


def _missing_email_result() -> dict[str, Any]:
    """Build a consistent missing-email response."""

    return {
        "success": False,
        "status": "missing_email",
        "message": "A valid recipient email is required.",
    }


# ============================================================
# Escalation Notification
# ============================================================

def _send_escalation_notification(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Notify the support team about an escalation."""

    escalation_id = _required_text(data, "escalation_id")
    customer_id = _required_text(data, "customer_id")
    priority = _required_text(data, "priority") or "medium"
    customer_message = _required_text(data, "message")
    reason = _required_text(data, "reason")

    if not SUPPORT_EMAIL or not SUPPORT_EMAIL.strip():
        logger.error("Support email is not configured.")

        return {
            "success": False,
            "status": "missing_support_email",
            "message": "Support email is not configured.",
        }

    subject_id = escalation_id or "N/A"
    subject = f"[{priority.upper()}] Customer Escalation - {subject_id}"

    body = (
        "A customer support escalation has been created.\n\n"
        f"Escalation ID:\n{escalation_id or 'N/A'}\n\n"
        f"Customer ID:\n{customer_id or 'N/A'}\n\n"
        f"Priority:\n{priority}\n\n"
        f"Reason:\n{reason or 'Not provided'}\n\n"
        f"Customer Message:\n{customer_message or 'Not provided'}\n\n"
        "Please review this case."
    )

    send_email(
        to=SUPPORT_EMAIL.strip(),
        subject=subject,
        body=body,
    )

    logger.info(
        "Escalation notification sent. escalation_id=%s",
        subject_id,
    )

    return _notification_result("escalation")


# ============================================================
# Refund Notification
# ============================================================

def _send_refund_notification(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Notify a customer about a refund request."""

    customer_email = _required_text(data, "customer_email")
    order_id = _required_text(data, "order_id")

    if not customer_email:
        return _missing_email_result()

    if not order_id:
        return {
            "success": False,
            "status": "missing_order_id",
            "message": "Order ID is required.",
        }

    subject = f"Refund Update - {order_id}"

    body = (
        f"Your refund request for order {order_id} "
        "has been received and is being processed."
    )

    send_email(
        to=customer_email,
        subject=subject,
        body=body,
    )

    return _notification_result("refund")


# ============================================================
# Order Notification
# ============================================================

def _send_order_notification(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Notify a customer about an order update."""

    customer_email = _required_text(data, "customer_email")
    order_id = _required_text(data, "order_id")
    message = _required_text(data, "message")

    if not customer_email:
        return _missing_email_result()

    if not order_id:
        return {
            "success": False,
            "status": "missing_order_id",
            "message": "Order ID is required.",
        }

    send_email(
        to=customer_email,
        subject=f"Order Update - {order_id}",
        body=message or "Your order has been updated.",
    )

    return _notification_result("order")


# ============================================================
# General Notification
# ============================================================

def _send_general_notification(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Send a general customer support notification."""

    customer_email = _required_text(data, "customer_email")
    subject = _required_text(data, "subject") or "Customer Support Update"
    message = _required_text(data, "message") or "You have a new update."

    if not customer_email:
        return _missing_email_result()

    send_email(
        to=customer_email,
        subject=subject,
        body=message,
    )

    return _notification_result("general")
