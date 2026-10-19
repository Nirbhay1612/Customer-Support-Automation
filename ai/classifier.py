"""
Intent classification for AI Customer Support Automation.

Features:
- Classifies customer messages into supported intents.
- Normalizes model-generated intent labels.
- Parses JSON and Markdown-wrapped JSON responses.
- Validates confidence scores.
- Provides safe fallbacks for invalid responses.
- Logs unexpected exceptions for debugging.
"""

from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

from ai.generator import generate_text
from ai.prompts import CLASSIFIER_PROMPT


logger = logging.getLogger(__name__)


# ============================================================
# Supported Intents
# ============================================================

SUPPORTED_INTENTS = {
    "order_status",
    "order_issue",
    "refund_request",
    "return_request",
    "faq",
    "complaint",
    "escalation",
    "unknown",
}


# ============================================================
# Intent Aliases
# ============================================================

INTENT_ALIASES = {
    "orderstatus": "order_status",
    "orderissue": "order_issue",
    "refund": "refund_request",
    "refundrequest": "refund_request",
    "return": "return_request",
    "returnrequest": "return_request",
    "human": "escalation",
    "humansupport": "escalation",
    "support": "escalation",
}


# ============================================================
# Safe Fallback
# ============================================================

def _unknown_result(reason: str) -> dict[str, Any]:
    """Return a consistent fallback classification."""

    return {
        "intent": "unknown",
        "confidence": 0.0,
        "reason": reason,
    }


# ============================================================
# Prompt Formatting
# ============================================================

def _build_classifier_prompt(message: str) -> str:
    """Insert the customer message without formatting JSON braces."""

    return CLASSIFIER_PROMPT.replace("{message}", message)


# ============================================================
# Intent Normalization
# ============================================================

def _normalize_intent(value: Any) -> str:
    """
    Normalize model-generated intent labels.

    Examples:
        RETURN                  -> return_request
        SupportIntent.RETURN    -> return_request
        refund                  -> refund_request
        order-status            -> order_status
        FAQ                     -> faq
    """

    if not isinstance(value, str):
        return "unknown"

    intent = value.strip()

    if not intent:
        return "unknown"

    # Remove surrounding Markdown formatting and quotes.
    intent = intent.strip("`'\"* \t\r\n")

    # Handle enum-style values, such as SupportIntent.RETURN.
    if "." in intent:
        intent = intent.rsplit(".", 1)[-1]

    # Handle labels such as "intent: return".
    if ":" in intent:
        parts = intent.split(":", 1)

        # Only use the portion after the colon when the prefix
        # indicates that this is an intent label.
        if parts[0].strip().lower() in {"intent", "label"}:
            intent = parts[1]

    # Normalize case and surrounding formatting.
    intent = intent.strip("`'\"* \t\r\n").lower()

    # Normalize spaces and hyphens.
    intent = re.sub(r"[\s-]+", "_", intent)

    compact_intent = intent.replace("_", "")

    # Resolve aliases.
    if compact_intent in INTENT_ALIASES:
        return INTENT_ALIASES[compact_intent]

    if intent in INTENT_ALIASES:
        return INTENT_ALIASES[intent]

    # Accept supported canonical labels.
    if intent in SUPPORTED_INTENTS:
        return intent

    return "unknown"


# ============================================================
# JSON Extraction
# ============================================================

def _extract_json(response: str) -> dict[str, Any] | None:
    """
    Extract a JSON object from a model response.

    Supports:
    - Plain JSON.
    - JSON wrapped in Markdown code fences.
    - Short explanatory text before a JSON object.
    """

    if not isinstance(response, str) or not response.strip():
        return None

    text = response.strip()

    # Remove an optional Markdown code fence.
    text = re.sub(
        r"\A```(?:json)?\s*|\s*```\Z",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # First try parsing the entire response.
    try:
        result = json.loads(text)

    except json.JSONDecodeError:
        # If extra text surrounds the JSON, locate the object.
        decoder = json.JSONDecoder()
        result = None

        for match in re.finditer(r"\{", text):
            try:
                candidate, _ = decoder.raw_decode(
                    text[match.start():]
                )

                result = candidate
                break

            except json.JSONDecodeError:
                continue

        if result is None:
            return None

    if not isinstance(result, dict):
        return None

    return result


# ============================================================
# Response Parsing and Validation
# ============================================================

def _parse_response(response: str) -> dict[str, Any]:
    """
    Parse and validate the model-generated classification.
    """

    result = _extract_json(response)

    if result is None:
        logger.warning(
            "Classifier returned an invalid JSON response."
        )

        return _unknown_result(
            "Invalid classifier response."
        )

    # Normalize the intent.
    intent = _normalize_intent(
        result.get("intent")
    )

    # Validate confidence.
    raw_confidence = result.get("confidence", 0.0)

    if isinstance(raw_confidence, bool):
        confidence = 0.0

    else:
        try:
            confidence = float(raw_confidence)

        except (TypeError, ValueError, OverflowError):
            confidence = 0.0

    # Prevent NaN and infinity.
    if not math.isfinite(confidence):
        confidence = 0.0

    else:
        confidence = max(
            0.0,
            min(confidence, 1.0),
        )

    # Unknown intents should never have high confidence.
    if intent == "unknown":
        confidence = 0.0

    # Validate the reason.
    reason = result.get("reason", "")

    if not isinstance(reason, str):
        reason = ""

    reason = " ".join(reason.split())[:500]

    return {
        "intent": intent,
        "confidence": confidence,
        "reason": reason,
    }


# ============================================================
# Intent Classification
# ============================================================

def classify_intent(message: str) -> dict[str, Any]:
    """
    Classify a customer message into a supported intent.

    Args:
        message: Customer's input message.

    Returns:
        Dictionary containing:
        - intent
        - confidence
        - reason
    """

    # Validate input.
    if not isinstance(message, str):
        return _unknown_result(
            "Invalid message type."
        )

    message = message.strip()

    if not message:
        return _unknown_result(
            "Empty message."
        )

    try:
        # Build the classifier prompt.
        prompt = _build_classifier_prompt(message)

        if not isinstance(prompt, str) or not prompt.strip():
            logger.error(
                "Classifier prompt is empty or invalid."
            )

            return _unknown_result(
                "Classifier prompt is invalid."
            )

        # Generate the model response.
        response = generate_text(prompt)

        # Validate the response type.
        if not isinstance(response, str):
            logger.error(
                "Generator returned an unexpected response type: %s",
                type(response).__name__,
            )

            return _unknown_result(
                "Invalid generator response type."
            )

        # Parse and validate the response.
        return _parse_response(response)

    except Exception:
        # Keep the customer message and secrets out of the logs.
        # logger.exception records the traceback for debugging.
        logger.exception(
            "Unexpected error during intent classification."
        )

        return _unknown_result(
            "Classification failed."
        )


# ============================================================
# Convenience Function
# ============================================================

def get_intent(message: str) -> str:
    """Return only the normalized intent label."""

    return classify_intent(message)["intent"]