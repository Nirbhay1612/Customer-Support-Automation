
"""
Order workflow for the AI Customer Support Automation system.

Retrieves order details, builds a customer-friendly response,
and optionally sends an email notification.
"""

import logging
from typing import Any

from integrations.email import send_email
from integrations.order_api import get_order

logger = logging.getLogger(__name__)


def handle_order_workflow(data: dict[str, Any]) -> dict[str, Any]:
    """Handle order-related customer requests."""

    if not isinstance(data, dict):
        message = "Order request data must be a dictionary."
        return {
            "success": False,
            "status": "invalid_input",
            "error": message,
            "message": message,
        }

    raw_order_id = data.get("order_id")

    if not isinstance(raw_order_id, str) or not raw_order_id.strip():
        logger.warning("Order workflow called without a valid order_id.")
        message = "Missing or invalid order_id."
        return {
            "success": False,
            "status": "invalid_input",
            "error": message,
            "message": message,
        }

    order_id = raw_order_id.strip()
    customer_email = data.get("customer_email")

    try:
        order = get_order(order_id)

        if order is None or order == {}:
            logger.warning("Order not found: %s", order_id)
            message = f"Order not found: {order_id}."
            return {
                "success": False,
                "status": "order_not_found",
                "error": message,
                "message": message,
            }

        if not isinstance(order, dict):
            message = "Unable to process the order information."
            logger.error("Order API returned an unexpected data type.")
            return {
                "success": False,
                "status": "invalid_order_data",
                "error": message,
                "message": message,
            }

        raw_status = order.get("status")
        status = (
            raw_status.strip()
            if isinstance(raw_status, str) and raw_status.strip()
            else "unknown"
        )

        raw_tracking_id = order.get("tracking_id")
        tracking_id = (
            raw_tracking_id.strip()
            if isinstance(raw_tracking_id, str) and raw_tracking_id.strip()
            else None
        )

        raw_delivery = order.get("estimated_delivery")
        estimated_delivery = (
            raw_delivery.strip()
            if isinstance(raw_delivery, str) and raw_delivery.strip()
            else None
        )

        message = _build_order_message(
            order_id=order_id,
            status=status,
            tracking_id=tracking_id,
            estimated_delivery=estimated_delivery,
        )

        if isinstance(customer_email, str) and customer_email.strip():
            try:
                send_email(
                    to=customer_email.strip(),
                    subject=f"Order Update - {order_id}",
                    body=message,
                )
            except Exception as exc:
                logger.warning(
                    "Order email notification failed. error_type=%s",
                    type(exc).__name__,
                )

        return {
            "success": True,
            "status": status,
            "order_id": order_id,
            "tracking_id": tracking_id,
            "estimated_delivery": estimated_delivery,
            "message": message,
        }

    except Exception as exc:
        logger.error(
            "Order workflow failed. error_type=%s",
            type(exc).__name__,
        )
        message = "Unable to process the order request."
        return {
            "success": False,
            "status": "workflow_error",
            "error": message,
            "message": message,
        }


def _build_order_message(
    order_id: str,
    status: str,
    tracking_id: str | None = None,
    estimated_delivery: str | None = None,
) -> str:
    """Build a customer-friendly order status message."""

    message = f"Your order {order_id} is currently '{status}'."

    if tracking_id:
        message += f" Tracking ID: {tracking_id}."

    if estimated_delivery:
        message += f" Estimated delivery: {estimated_delivery}."

    return message
