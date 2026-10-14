
"""
Input validation and text sanitization utilities.

Provides reusable validators for customer support, order management,
AI confidence scores, monetary amounts, and workflow data.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Set
from typing import Any


# ============================================================
# Validation Patterns
# ============================================================

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

ORDER_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]{3,50}$"
)

CUSTOMER_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]{2,50}$"
)


# ============================================================
# Email Validation
# ============================================================

def validate_email(email: str) -> bool:
    """Return whether an email matches the application's email format."""
    if not isinstance(email, str):
        return False

    email = email.strip()

    if not email or len(email) > 254:
        return False

    return EMAIL_PATTERN.fullmatch(email) is not None


# ============================================================
# Identifier Validation
# ============================================================

def validate_order_id(order_id: str) -> bool:
    """Return whether an order ID contains valid characters and length."""
    if not isinstance(order_id, str):
        return False

    order_id = order_id.strip()

    return ORDER_ID_PATTERN.fullmatch(order_id) is not None


def validate_customer_id(customer_id: str) -> bool:
    """Return whether a customer ID contains valid characters and length."""
    if not isinstance(customer_id, str):
        return False

    customer_id = customer_id.strip()

    return CUSTOMER_ID_PATTERN.fullmatch(customer_id) is not None


# ============================================================
# Message Validation
# ============================================================

def validate_message(message: str, max_length: int = 5000) -> bool:
    """Validate a non-empty message within the specified length limit."""
    if not isinstance(message, str):
        return False

    if isinstance(max_length, bool) or not isinstance(max_length, int):
        return False

    if max_length < 0:
        return False

    message = message.strip()

    return bool(message) and len(message) <= max_length


# ============================================================
# Required Field Validation
# ============================================================

def validate_required_fields(
    data: dict[str, Any],
    required_fields: list[str],
) -> tuple[bool, list[str]]:
    """
    Check whether required fields exist and contain non-empty values.

    Returns:
        A tuple containing (all_fields_valid, missing_fields).
    """
    if not isinstance(data, Mapping):
        raise TypeError("data must be a mapping.")

    if isinstance(required_fields, (str, bytes)) or not isinstance(
        required_fields, (list, tuple)
    ):
        raise TypeError("required_fields must be a list or tuple.")

    missing_fields: list[str] = []

    for field in required_fields:
        if not isinstance(field, str):
            raise TypeError("Required field names must be strings.")

        value = data.get(field)

        if value is None:
            missing_fields.append(field)
        elif isinstance(value, str) and not value.strip():
            missing_fields.append(field)

    return not missing_fields, missing_fields


# ============================================================
# AI Confidence Validation
# ============================================================

def validate_confidence(
    confidence: float,
    minimum: float = 0.50,
) -> bool:
    """Validate a finite confidence score within the range [minimum, 1]."""
    if isinstance(confidence, bool) or not isinstance(
        confidence, (int, float)
    ):
        return False

    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
        return False

    if not math.isfinite(confidence) or not math.isfinite(minimum):
        return False

    if not 0.0 <= minimum <= 1.0:
        return False

    return minimum <= confidence <= 1.0


# ============================================================
# Monetary Amount Validation
# ============================================================

def validate_positive_amount(amount: float) -> bool:
    """Return whether an amount is a finite, strictly positive number."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return False

    return math.isfinite(amount) and amount > 0


# ============================================================
# Status Validation
# ============================================================

def validate_status(
    status: str,
    allowed_statuses: set[str],
) -> bool:
    """Validate a status using case-insensitive comparison."""
    if not isinstance(status, str) or not status.strip():
        return False

    if not isinstance(allowed_statuses, Set):
        return False

    normalized_status = status.strip().casefold()

    normalized_allowed = {
        value.casefold()
        for value in allowed_statuses
        if isinstance(value, str)
    }

    return normalized_status in normalized_allowed


# ============================================================
# Text Sanitization
# ============================================================

def sanitize_text(text: str) -> str:
    """
    Normalize surrounding whitespace and consecutive whitespace characters.

    This is text cleanup, not HTML escaping or security sanitization.
    """
    if not isinstance(text, str):
        return ""

    return " ".join(text.split())
