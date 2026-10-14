
"""
Intent classification for AI Customer Support Automation.

Classifies customer messages into supported intents, validates LLM
responses, and safely falls back to UNKNOWN when classification fails.
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
    """
    Build the classifier prompt safely.

    If the template contains unescaped JSON braces, fall back to
    replacing only the explicit message placeholder.
    """

    try:
        return CLASSIFIER_PROMPT.format(message=message)

    except (KeyError, ValueError, IndexError):
        logger.warning(
            "Classifier prompt formatting failed; using safe fallback."
        )

        # Do not run format() again: literal JSON braces must remain intact.
        return CLASSIFIER_PROMPT.replace("{message}", message)


# ============================================================
# Intent Normalization
# ============================================================

def _normalize_intent(value: Any) -> str:
    """
    Normalize a model-generated intent into a supported label.

    Handles case differences, surrounding formatting, aliases,
    and enum-style names such as SupportIntent.RETURN.
    """

    if not isinstance(value, str):
        return "unknown"

    intent = value.strip()

    if not intent:
        return "unknown"

    # Remove surrounding Markdown formatting and quotes.
    intent = intent.strip("`'\"* \t\r\n")

    # Handle enum-style labels.
    if "." in intent:
        intent = intent.rsplit(".", 1)[-1]

    # Handle enum-like text such as "intent: return".
    if ":" in intent:
        intent = intent.split(":", 1)[0]

    intent = intent.strip("`'\"* \t\r\n").lower()

    # Normalize spaces and hyphens.
    intent = re.sub(r"[\s-]+", "_", intent)

    compact_intent = intent.replace("_", "")

    if compact_intent in INTENT_ALIASES:
        return INTENT_ALIASES[compact_intent]

    if intent in INTENT_ALIASES:
        return INTENT_ALIASES[intent]

    if intent in SUPPORTED_INTENTS:
        return intent

    return "unknown"


# ============================================================
# Response Parsing
# ============================================================

def _extract_json(response: str) -> dict[str, Any] | None:
    """
    Extract a JSON object from a model response.

    Supports plain JSON and JSON wrapped in Markdown code fences.
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

    try:
        result = json.loads(text)

    except json.JSONDecodeError:
        decoder = json.JSONDecoder()

        # Allow short text before a JSON object.
        for match in re.finditer(r"\{", text):
            try:
                result, _ = decoder.raw_decode(text[match.start():])
                break
            except json.JSONDecodeError:
                continue
        else:
            return None

    if not isinstance(result, dict):
        return None

    return result


def _parse_response(response: str) -> dict[str, Any]:
    """
    Parse and validate the classifier response.

    Invalid structures or unsupported intents fall back to UNKNOWN.
    """

    result = _extract_json(response)

    if result is None:
        logger.warning("Classifier returned an invalid JSON object.")
        return _unknown_result("Invalid classifier response.")

    intent = _normalize_intent(result.get("intent"))

    raw_confidence = result.get("confidence", 0.0)

    # Booleans are numeric subclasses in Python; reject them explicitly.
    if isinstance(raw_confidence, bool):
        confidence = 0.0
    else:
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError, OverflowError):
            confidence = 0.0

    if not math.isfinite(confidence):
        confidence = 0.0
    else:
        confidence = max(0.0, min(confidence, 1.0))

    # An unsupported intent must not carry a high confidence score.
    if intent == "unknown":
        confidence = 0.0

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

    Returns:
        A dictionary containing intent, confidence, and reason.
    """

    if not isinstance(message, str) or not message.strip():
        return _unknown_result("Empty or invalid message.")

    try:
        prompt = _build_classifier_prompt(message.strip())
        response = generate_text(prompt)

        return _parse_response(response)

    except Exception:
        # Do not log customer messages or exception details.
        logger.error(
            "Intent classification failed.",
            exc_info=False,
        )
        return _unknown_result("Classification failed.")


# ============================================================
# Convenience Function
# ============================================================

def get_intent(message: str) -> str:
    """Return only the normalized intent label."""

    return classify_intent(message)["intent"]
