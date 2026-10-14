
"""
Embedding utilities for the RAG pipeline.

Loads and caches the sentence-transformer model, generates normalized
embeddings, and validates embedding dimensions and numeric values.
"""

from __future__ import annotations

import logging
import math
from threading import Lock
from typing import List
from collections.abc import Sequence
from typing import Any


from sentence_transformers import SentenceTransformer

from config import settings


logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_model_lock = Lock()


# ============================================================
# Embedding Model
# ============================================================

def get_embedding_model() -> SentenceTransformer:
    """Load and cache the embedding model safely across threads."""
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        # Another thread may have loaded the model while we waited.
        if _model is not None:
            return _model

        model_name = settings.EMBEDDING_MODEL.strip()

        if not model_name:
            raise ValueError("EMBEDDING_MODEL cannot be empty.")

        logger.info("Loading embedding model: %s", model_name)

        try:
            loaded_model = SentenceTransformer(model_name)
        except Exception:
            logger.exception("Failed to load the embedding model.")
            raise

        _model = loaded_model
        logger.info("Embedding model loaded successfully.")

        return _model


# ============================================================
# Embedding Validation
# ============================================================

def _validate_embedding(embedding: object) -> List[float]:
    """Convert an embedding vector to finite Python floats."""
    tolist=getattr(embedding, "tolist", None)

    if tolist is not None:
        values = tolist()
    else:
        values = embedding

    if not isinstance(values, (list, tuple)) or not values:
        raise RuntimeError("The model returned an invalid embedding.")

    try:
        vector = [float(value) for value in values]
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError(
            "The model returned non-numeric embedding values."
        ) from exc

    if not all(math.isfinite(value) for value in vector):
        raise RuntimeError(
            "The model returned non-finite embedding values."
        )

    return vector


# ============================================================
# Generate Embedding For One Text
# ============================================================

def generate_embedding(text: str) -> List[float]:
    """Generate a normalized embedding for one text string."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a non-empty string.")

    model = get_embedding_model()

    try:
        embedding = model.encode(
            text.strip(),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception:
        logger.exception("Failed to generate a text embedding.")
        raise

    vector = _validate_embedding(embedding)

    expected_dimension = get_embedding_dimension()

    if len(vector) != expected_dimension:
        raise RuntimeError(
            "Generated embedding dimension does not match "
            "the model's reported dimension."
        )

    return vector


# ============================================================
# Generate Embeddings For Multiple Texts
# ============================================================

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate normalized embeddings for multiple text chunks.

    Empty or whitespace-only entries are skipped, preserving the
    behavior of the original implementation.
    """
    if not texts:
        return []

    if isinstance(texts, (str, bytes)):
        raise TypeError("texts must be a list of strings.")

    cleaned_texts: List[str] = []

    for text in texts:
        if not isinstance(text, str):
            raise TypeError("Every item in texts must be a string.")

        cleaned = text.strip()

        if cleaned:
            cleaned_texts.append(cleaned)

    if not cleaned_texts:
        return []

    model = get_embedding_model()

    try:
        embeddings = model.encode(
            cleaned_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception:
        logger.exception("Failed to generate batch embeddings.")
        raise

    try:
        vectors = [_validate_embedding(item) for item in embeddings]
    except (TypeError, RuntimeError):
        logger.exception("Invalid embedding returned during batch processing.")
        raise

    expected_dimension = get_embedding_dimension()

    if len(vectors) != len(cleaned_texts):
        raise RuntimeError(
            "Embedding count does not match the number of input texts."
        )

    if any(len(vector) != expected_dimension for vector in vectors):
        raise RuntimeError(
            "One or more embedding dimensions do not match the model."
        )

    return vectors


# ============================================================
# Embedding Dimension
# ============================================================

def get_embedding_dimension() -> int:
    """Return the configured model's embedding dimension."""
    model = get_embedding_model()
    dimension = model.get_sentence_embedding_dimension()

    if (
        isinstance(dimension, bool)
        or not isinstance(dimension, int)
        or dimension <= 0
    ):
        raise RuntimeError(
            "Unable to determine a valid embedding dimension."
        )

    return dimension
