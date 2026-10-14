
"""
Escalation workflow for the AI Customer Support Automation system.

Validates support escalations, creates an escalation record, and
attempts to notify the support team.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from automation.notification import handle_notification


logger = logging.getLogger(__name__)

ALLOWED_PRIORITIES = {"low", "medium", "high"}


# ============================================================
# Escalation Workflow
# ============================================================

def handle_escalation(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Escalate a customer issue to human support.

    Expected data:
        {
            "customer_id": "CUS-1001",
            "customer_email": "customer@example.com",
            "message": "I want to speak to a human",
            "reason": "Customer requested human support",
            "priority": "medium"
        }
    """

    # --------------------------------------------------------
    # Validate Input
    # --------------------------------------------------------

    if not isinstance(data, dict):
        return {
            "success": False,
            "status": "invalid_input",
            "message": "Escalation data must be a dictionary.",
        }

    customer_id = data.get("customer_id")

    if (
        customer_id is None
        or isinstance(customer_id, bool)
        or not isinstance(customer_id, (str, int))
        or not str(customer_id).strip()
    ):
        return {
            "success": False,
            "status": "missing_customer_id",
            "message": "A valid customer ID is required.",
        }

    customer_id = str(customer_id).strip()

    customer_email = data.get("customer_email")
    customer_message = data.get("message")
    reason = data.get(
        "reason",
        "Issue requires human support.",
    )
    priority = data.get("priority", "medium")

    if customer_email is not None and not isinstance(customer_email, str):
        return {
            "success": False,
            "status": "invalid_customer_email",
            "message": "Customer email must be a string.",
        }

    if customer_message is not None and not isinstance(
        customer_message, str
    ):
        return {
            "success": False,
            "status": "invalid_message",
            "message": "Escalation message must be a string.",
        }

    if not isinstance(reason, str) or not reason.strip():
        return {
            "success": False,
            "status": "invalid_reason",
            "message": "A valid escalation reason is required.",
        }

    if not isinstance(priority, str):
        return {
            "success": False,
            "status": "invalid_priority",
            "message": "Priority must be low, medium, or high.",
        }

    priority = priority.strip().lower()

    if priority not in ALLOWED_PRIORITIES:
        return {
            "success": False,
            "status": "invalid_priority",
            "message": "Priority must be low, medium, or high.",
        }

    if isinstance(customer_message, str):
        customer_message = customer_message.strip()

    reason = reason.strip()

    if isinstance(customer_email, str):
        customer_email = customer_email.strip() or None

    # --------------------------------------------------------
    # Create Escalation Record
    # --------------------------------------------------------

    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"

    created_at = datetime.now(timezone.utc).isoformat()

    escalation = {
        "escalation_id": escalation_id,
        "customer_id": customer_id,
        "customer_email": customer_email,
        "message": customer_message,
        "reason": reason,
        "priority": priority,
        "status": "pending",
        "created_at": created_at,
    }

    logger.info(
        "Escalation created. escalation_id=%s priority=%s",
        escalation_id,
        priority,
    )

    # --------------------------------------------------------
    # Notify Support Team
    # --------------------------------------------------------

    notification_sent = False

    try:
        notification_result = handle_notification(
            {
                "type": "escalation",
                "escalation_id": escalation_id,
                "customer_id": customer_id,
                "priority": priority,
                "message": customer_message,
                "reason": reason,
            }
        )

        if isinstance(notification_result, dict):
            notification_sent = (
                notification_result.get("success") is True
            )

        if not notification_sent:
            logger.warning(
                "Escalation notification was not confirmed. "
                "escalation_id=%s",
                escalation_id,
            )

    except Exception as exc:
        logger.warning(
            "Escalation notification failed. error_type=%s",
            type(exc).__name__,
        )

    # --------------------------------------------------------
    # Return Result
    # --------------------------------------------------------

    return {
        "success": True,
        "status": "escalated",
        "message": (
            "Your request has been forwarded "
            "to our support team."
        ),
        "escalation": escalation,
        "notification_sent": notification_sent,
    }
