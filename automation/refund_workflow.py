"""
Refund workflow for the AI Customer Support Automation system.

Validates refund requests, verifies order ownership and eligibility,
submits requests to the external order API, and optionally notifies
the customer by email.
"""

import logging
import math
from typing import Any

from integrations.email import send_email
from integrations.order_api import create_refund, get_order

logger = logging.getLogger(__name__)


def _failure(status: str, message: str) -> dict[str, Any]:
    """Build a consistent failure response for workflow callers."""
    return {
        "success": False,
        "status": status,
        "error": message,
        "message": message,
    }


def handle_refund_workflow(data: dict[str, Any]) -> dict[str, Any]:
    """Handle customer refund requests."""
    if not isinstance(data, dict):
        return _failure(
            "invalid_input",
            "Refund request data must be a dictionary.",
        )

    order_id = data.get("order_id")
    customer_id = data.get("customer_id")
    customer_email = data.get("customer_email")
    reason = data.get("reason")

    if not isinstance(order_id, str) or not order_id.strip():
        return _failure("missing_order_id", "Order ID is required for a refund.")

    if customer_id is None or (
        isinstance(customer_id, str) and not customer_id.strip()
    ):
        return _failure("missing_customer_id", "Customer ID is required.")

    if not isinstance(reason, str) or not reason.strip():
        return _failure("missing_reason", "Refund reason is required.")

    if customer_email is not None and not isinstance(customer_email, str):
        return _failure(
            "invalid_customer_email",
            "Customer email must be a string.",
        )

    order_id = order_id.strip()
    expected_customer_id = str(customer_id).strip()
    reason = reason.strip()

    try:
        order = get_order(order_id)
    except Exception as exc:
        logger.error(
            "Refund order lookup failed. error_type=%s",
            type(exc).__name__,
        )
        return _failure("order_lookup_failed", "Unable to verify the order.")

    if order is None or order == {}:
        return _failure(
            "order_not_found",
            f"Order not found: {order_id}.",
        )

    if not isinstance(order, dict):
        return _failure(
            "invalid_order_data",
            "Unable to verify the order information.",
        )

    actual_customer_id = order.get("customer_id")
    if (
        actual_customer_id is None
        or str(actual_customer_id).strip() != expected_customer_id
    ):
        logger.warning("Refund ownership verification failed.")
        return _failure(
            "customer_mismatch",
            "Order ownership could not be verified.",
        )

    eligibility = check_refund_eligibility(order)
    if not eligibility["eligible"]:
        return _failure("refund_not_eligible", eligibility["reason"])

    try:
        external_result = create_refund(
            order_id=order_id,
            reason=reason,
        )
    except Exception as exc:
        logger.error(
            "Refund request submission failed. error_type=%s",
            type(exc).__name__,
        )
        return _failure(
            "refund_creation_failed",
            "Unable to submit the refund request.",
        )

    if not isinstance(external_result, dict):
        return _failure(
            "invalid_refund_response",
            "Unable to confirm the refund request.",
        )

    # Respect an explicit failure returned by the external service.
    if external_result.get("success") is False:
        service_message = (
            external_result.get("error")
            or external_result.get("message")
        )
        if not isinstance(service_message, str) or not service_message.strip():
            service_message = "The refund service rejected the request."
        return _failure("refund_creation_failed", service_message)

    refund_request = dict(external_result)
    refund_request.setdefault("order_id", order_id)
    refund_request.setdefault("customer_id", expected_customer_id)
    refund_request.setdefault("reason", reason)
    refund_request.setdefault("amount", order.get("amount"))
    refund_request.setdefault("status", "pending")

    logger.info("Refund request accepted by the external API.")

    notification_sent = False
    if isinstance(customer_email, str) and customer_email.strip():
        try:
            send_email(
                to=customer_email.strip(),
                subject=f"Refund Request - {order_id}",
                body=(
                    f"Your refund request for order {order_id} "
                    "has been submitted for review."
                ),
            )
            notification_sent = True
        except Exception as exc:
            logger.warning(
                "Refund notification failed. error_type=%s",
                type(exc).__name__,
            )

    return {
        "success": True,
        "status": "refund_pending",
        "message": "Your refund request has been submitted for review.",
        "refund_request": refund_request,
        "notification_sent": notification_sent,
    }


def check_refund_eligibility(order: dict[str, Any]) -> dict[str, Any]:
    """Check basic refund eligibility."""
    if not isinstance(order, dict):
        return {
            "eligible": False,
            "reason": "Order information could not be verified.",
        }

    raw_status = order.get("status")
    if not isinstance(raw_status, str) or not raw_status.strip():
        return {
            "eligible": False,
            "reason": "Order status could not be verified.",
        }

    order_status = raw_status.strip().lower()
    if order_status == "refunded":
        return {
            "eligible": False,
            "reason": "This order has already been refunded.",
        }

    if order_status == "cancelled":
        return {
            "eligible": False,
            "reason": "Cancelled orders require a separate refund process.",
        }

    amount = order.get("amount")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or not math.isfinite(amount)
        or amount <= 0
    ):
        return {
            "eligible": False,
            "reason": "Refund amount could not be verified.",
        }

    return {
        "eligible": True,
        "reason": "Order passed the basic refund eligibility checks.",
    }
