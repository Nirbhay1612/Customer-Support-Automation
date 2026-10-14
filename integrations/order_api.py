
"""
External order API integration.

Provides order lookup and refund-request operations with
input validation, bounded request timeouts, and safe error handling.
"""

import logging
from typing import Any
from urllib.parse import quote, urlsplit

import requests

from config import settings


logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


# ============================================================
# Configuration
# ============================================================

def _get_base_url() -> str:
    """Validate and return the configured order API base URL."""

    base_url = settings.ORDER_API_URL

    if not isinstance(base_url, str) or not base_url.strip():
        raise RuntimeError("ORDER_API_URL is not configured.")

    base_url = base_url.strip().rstrip("/")
    parsed_url = urlsplit(base_url)

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise RuntimeError("ORDER_API_URL is invalid.")

    return base_url


def _validate_order_id(order_id: str) -> str:
    """Validate and URL-encode an order identifier."""

    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError("order_id cannot be empty.")

    return quote(order_id.strip(), safe="")


# ============================================================
# Headers
# ============================================================

def _get_headers() -> dict[str, str]:
    """Return headers required by the order API."""

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ============================================================
# Response Handling
# ============================================================

def _parse_json_object(
    response: requests.Response,
    operation: str,
) -> dict[str, Any]:
    """Parse a JSON response and require a JSON object."""

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(
            "%s API returned invalid JSON.",
            operation,
        )
        message = (
            "Order API returned invalid data."
            if operation == "Order"
            else "Refund API returned invalid data."
        )
        raise RuntimeError(message) from exc

    if not isinstance(data, dict):
        logger.error(
            "%s API returned an unexpected response type.",
            operation,
        )
        message = (
            "Order API returned invalid data."
            if operation == "Order"
            else "Refund API returned invalid data."
        )
        raise RuntimeError(message)

    return data


# ============================================================
# Get Order
# ============================================================

def get_order(
    order_id: str,
) -> dict[str, Any] | None:
    """
    Fetch order information from the external order API.

    Returns:
        Order dictionary if found, otherwise None.

    Raises:
        ValueError: If the order ID is empty or invalid.
        RuntimeError: If configuration or the API request fails.
    """

    encoded_order_id = _validate_order_id(order_id)
    base_url = _get_base_url()

    url = f"{base_url}/orders/{encoded_order_id}"

    try:
        response = requests.get(
            url,
            headers=_get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )

        if response.status_code == 404:
            logger.info("Order lookup returned not found.")
            return None

        response.raise_for_status()

        return _parse_json_object(response, "Order")

    except requests.Timeout as exc:
        logger.error("Order API request timed out.")
        raise RuntimeError(
            "Order API request timed out."
        ) from exc

    except requests.RequestException as exc:
        logger.error(
            "Order API request failed. Error type: %s",
            type(exc).__name__,
        )
        raise RuntimeError(
            "Unable to connect to order API."
        ) from exc


# ============================================================
# Create Refund Request
# ============================================================

def create_refund(
    order_id: str,
    reason: str,
) -> dict[str, Any]:
    """
    Submit a refund request to the external order API.

    This requests a refund; it does not imply that money has
    already been returned to the customer.

    Automatic retries are intentionally avoided because the
    remote server may process a request even if the client times out.
    """

    encoded_order_id = _validate_order_id(order_id)

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Refund reason cannot be empty.")

    base_url = _get_base_url()

    url = f"{base_url}/orders/{encoded_order_id}/refund"

    payload = {
        "reason": reason.strip(),
    }

    try:
        response = requests.post(
            url,
            headers=_get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()

        return _parse_json_object(response, "Refund")

    except requests.Timeout as exc:
        logger.error("Refund API request timed out.")
        raise RuntimeError(
            "Refund API request timed out."
        ) from exc

    except requests.RequestException as exc:
        logger.error(
            "Refund API request failed. Error type: %s",
            type(exc).__name__,
        )
        raise RuntimeError(
            "Unable to create refund request."
        ) from exc
