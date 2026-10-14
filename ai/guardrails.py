
"""
Security guardrails for AI Customer Support Automation.

Validates customer input, classifier output, AI responses, and basic
automation eligibility. Sensitive business operations must still be
authorized and validated by their respective backend services.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Mapping, Set
from typing import Any


logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

MAX_MESSAGE_LENGTH = 5000
MAX_RESPONSE_LENGTH = 10000
MIN_CONFIDENCE = 0.50


# ============================================================
# Blocked Patterns
# ============================================================

BLOCKED_PATTERNS = [
    re.compile(
        r"\bignore\s+(?:(?:all|any)\s+)?"
        r"(?:the\s+)?previous\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bignore\s+(?:the\s+)?system\s+prompt\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reveal|print|disclose)\s+"
        r"(?:your\s+)?system\s+prompt\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bshow\s+(?:me\s+)?your\s+hidden\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reveal|print|disclose)\s+"
        r"(?:your\s+)?(?:hidden|internal)\s+instructions\b",
        re.IGNORECASE,
    ),
]


# ============================================================
# Shared Helpers
# ============================================================

def _input_failure(reason: str) -> dict[str, Any]:
    """Return a consistent failed input-validation result."""

    return {
        "valid": False,
        "message": "",
        "reason": reason,
    }


def _confidence_is_valid_number(value: Any) -> bool:
    """Return whether a confidence value is finite and within [0, 1]."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    return math.isfinite(value) and 0.0 <= value <= 1.0


# ============================================================
# Input Validation
# ============================================================

def validate_user_input(message: str) -> dict[str, Any]:
    """
    Validate customer input and normalize surrounding whitespace.

    Returns:
        Dictionary containing valid, message, and reason.
    """

    if not isinstance(message, str):
        return _input_failure("Input must be a string.")

    normalized_message = message.strip()

    if not normalized_message:
        return _input_failure("Message cannot be empty.")

    if len(normalized_message) > MAX_MESSAGE_LENGTH:
        return _input_failure("Message is too long.")

    if contains_prompt_injection(normalized_message):
        logger.warning("Potential prompt injection detected.")
        return _input_failure("Potential prompt injection detected.")

    return {
        "valid": True,
        "message": normalized_message,
        "reason": "",
    }


# ============================================================
# Prompt Injection Detection
# ============================================================

def contains_prompt_injection(message: str) -> bool:
    """
    Detect selected common prompt-injection phrases.

    This heuristic is not a complete injection detector and must
    not be treated as the sole security control.
    """

    if not isinstance(message, str) or not message:
        return False

    return any(
        pattern.search(message) is not None
        for pattern in BLOCKED_PATTERNS
    )


# ============================================================
# Intent Validation
# ============================================================

def validate_intent(
    intent: str,
    confidence: float,
    allowed_intents: set[str],
) -> bool:
    """
    Validate an intent against the allowed set and confidence threshold.

    Returns:
        True if valid; otherwise False.
    """

    if not isinstance(allowed_intents, Set):
        return False

    if not all(isinstance(item, str) for item in allowed_intents):
        return False

    if not isinstance(intent, str) or intent not in allowed_intents:
        return False

    if not _confidence_is_valid_number(confidence):
        return False

    return confidence >= MIN_CONFIDENCE


# ============================================================
# AI Output Validation
# ============================================================

def validate_ai_response(response: str) -> bool:
    """
    Validate that an AI response is a non-empty string within
    the configured length limit.

    Returns:
        True if valid; otherwise False.

    Note:
        This does not establish factual correctness or guarantee
        that the response contains no unsafe or confidential data.
    """

    if not isinstance(response, str):
        return False

    normalized_response = response.strip()

    if not normalized_response:
        return False

    if len(normalized_response) > MAX_RESPONSE_LENGTH:
        return False

    return True


# ============================================================
# Automation Safety Check
# ============================================================

def can_execute_automation(
    intent: str,
    confidence: float,
    required_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform basic eligibility checks before an automation proceeds.

    This is not a substitute for backend authorization, order
    ownership checks, refund eligibility, or transaction safeguards.
    """

    if not isinstance(intent, str):
        return {
            "allowed": False,
            "reason": "Invalid intent.",
        }

    if not _confidence_is_valid_number(confidence):
        return {
            "allowed": False,
            "reason": "Invalid confidence value.",
        }

    if confidence < MIN_CONFIDENCE:
        return {
            "allowed": False,
            "reason": "Low classification confidence.",
        }

    if not isinstance(required_data, Mapping):
        return {
            "allowed": False,
            "reason": "Invalid required data.",
        }

    if intent == "unknown":
        return {
            "allowed": False,
            "reason": "Intent could not be determined.",
        }

    if intent == "escalation":
        return {
            "allowed": False,
            "reason": "Human intervention required.",
        }

    supported_automation_intents = {
        "order_status",
        "order_issue",
        "refund_request",
        "return_request",
        "faq",
        "complaint",
    }

    if intent not in supported_automation_intents:
        return {
            "allowed": False,
            "reason": "Unsupported automation intent.",
        }

    if intent in {
        "order_status",
        "refund_request",
        "return_request",
    }:
        order_id = required_data.get("order_id")

        if not isinstance(order_id, str) or not order_id.strip():
            return {
                "allowed": False,
                "reason": "Order ID is required.",
            }

    return {
        "allowed": True,
        "reason": "Basic automation checks passed.",
    }
