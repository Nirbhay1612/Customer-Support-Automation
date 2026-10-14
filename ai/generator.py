
"""
LLM text generation for AI Customer Support Automation.

Provides a reusable Groq client with validated generation parameters,
safe logging, and consistent error handling.
"""

from __future__ import annotations

import logging
import math
from functools import lru_cache
from threading import Lock

from groq import Groq

from config import settings


logger = logging.getLogger(__name__)

_client_lock = Lock()


# ============================================================
# Client Management
# ============================================================

# Lazily initialized so importing this module does not require
# an API key immediately. This also makes isolated tests easier.
client: Groq | None = None


def _get_client() -> Groq:
    """
    Return the configured Groq client, initializing it when needed.

    Raises:
        RuntimeError: If the provider or API key is invalid.
    """
    global client

    if client is not None:
        return client

    with _client_lock:
        # Check again after acquiring the lock.
        if client is not None:
            return client

        provider = settings.LLM_PROVIDER.strip().lower()

        if provider != "groq":
            raise RuntimeError(
                f"Unsupported LLM provider: {provider!r}. "
                "This generator currently supports Groq only."
            )

        api_key = settings.GROQ_API_KEY.strip()

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        try:
            client = Groq(api_key=api_key)
        except Exception:
            logger.exception("Failed to initialize the Groq client.")
            raise RuntimeError(
                "Failed to initialize the AI provider."
            ) from None

    return client


# ============================================================
# Generation Parameter Validation
# ============================================================

def _validate_generation_parameters(
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> None:
    """Validate inputs before making an external API request."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
        or not 0.0 <= temperature <= 2.0
    ):
        raise ValueError(
            "Temperature must be a finite number between 0.0 and 2.0."
        )

    if (
        isinstance(max_tokens, bool)
        or not isinstance(max_tokens, int)
        or max_tokens < 1
    ):
        raise ValueError(
            "max_tokens must be a positive integer."
        )


# ============================================================
# Text Generation
# ============================================================

def generate_text(
    prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Generate text using the configured LLM provider.

    Args:
        prompt: Prompt sent to the model.
        temperature: Optional generation temperature.
        max_tokens: Optional maximum output token count.

    Returns:
        Generated text with surrounding whitespace removed.

    Raises:
        ValueError: If the prompt or generation parameters are invalid.
        RuntimeError: If client initialization or generation fails.
    """
    resolved_temperature = (
        settings.TEMPERATURE
        if temperature is None
        else temperature
    )

    resolved_max_tokens = (
        settings.MAX_TOKENS
        if max_tokens is None
        else max_tokens
    )

    _validate_generation_parameters(
        prompt,
        resolved_temperature,
        resolved_max_tokens,
    )

    try:
        llm_client = _get_client()

        response = llm_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
            temperature=resolved_temperature,
            max_tokens=resolved_max_tokens,
        )

        if not response.choices:
            raise RuntimeError(
                "The AI provider returned no response choices."
            )

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "The AI provider returned an empty response."
            )

        return content.strip()

    except ValueError:
        # Preserve local validation errors without wrapping them.
        raise

    except Exception:
        # Avoid logging prompts, customer data, or raw provider errors.
        logger.exception("LLM text generation failed.")

        raise RuntimeError(
            "Failed to generate AI response."
        ) from None
