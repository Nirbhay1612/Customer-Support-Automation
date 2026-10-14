
"""
FAISS vector-store utilities for the RAG pipeline.

Creates, persists, loads, and searches normalized embedding vectors
alongside their corresponding document metadata.
"""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any

import faiss
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Paths
# ============================================================

VECTORSTORE_DIR = Path(settings.VECTOR_STORE_PATH)
INDEX_PATH = VECTORSTORE_DIR / "index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

_store_lock = RLock()


def _index_path() -> Path:
    """Resolve the index path using the current vector-store directory."""
    return Path(VECTORSTORE_DIR).resolve() / "index.faiss"


def _metadata_path() -> Path:
    """Resolve the metadata path using the current vector-store directory."""
    return Path(VECTORSTORE_DIR).resolve() / "metadata.json"


# ============================================================
# Directory Setup
# ============================================================

def _ensure_directory() -> None:
    """Create the vector-store directory when necessary."""
    Path(VECTORSTORE_DIR).resolve().mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# Validation Helpers
# ============================================================

def _prepare_vectors(embeddings: Any) -> np.ndarray:
    """Convert embeddings to a validated float32 matrix."""
    try:
        vectors = np.asarray(embeddings, dtype=np.float32)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "Embeddings must contain numeric vectors."
        ) from exc

    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a 2D array.")

    if vectors.shape[0] == 0 or vectors.shape[1] == 0:
        raise ValueError("Embeddings cannot contain empty vectors.")

    if not np.isfinite(vectors).all():
        raise ValueError("Embeddings must contain only finite values.")

    norms = np.linalg.norm(vectors, axis=1)

    if np.any(norms <= 0):
        raise ValueError(
            "Embedding vectors cannot have zero magnitude."
        )

    return np.ascontiguousarray(vectors, dtype=np.float32)


def _normalize_query(query_embedding: Any) -> np.ndarray:
    """Validate and L2-normalize a single query embedding."""
    try:
        vector = np.asarray(query_embedding, dtype=np.float32)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "Query embedding must contain numeric values."
        ) from exc

    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(
            "Query embedding must be a non-empty 1D vector."
        )

    if not np.isfinite(vector).all():
        raise ValueError(
            "Query embedding must contain finite values."
        )

    norm = float(np.linalg.norm(vector))

    if not math.isfinite(norm) or norm <= 0:
        raise ValueError(
            "Query embedding cannot have zero magnitude."
        )

    vector = vector / norm

    return np.ascontiguousarray(
        vector.reshape(1, -1),
        dtype=np.float32,
    )


# ============================================================
# Create Vector Store
# ============================================================

def create_vectorstore(
    embeddings: list[list[float]],
    documents: list[dict[str, Any]],
) -> faiss.Index:
    """
    Create and persist a FAISS inner-product index and its metadata.

    Embeddings are normalized so inner product corresponds to
    cosine similarity.

    Returns:
        The created FAISS index.

    Raises:
        ValueError: If embeddings or documents are invalid.
        RuntimeError: If the index cannot be created or persisted.
    """
    if (
        not isinstance(embeddings, (list, tuple))
        or not embeddings
    ):
        raise ValueError("Embeddings cannot be empty.")

    if (
        not isinstance(documents, (list, tuple))
        or not documents
    ):
        raise ValueError("Documents cannot be empty.")

    if len(embeddings) != len(documents):
        raise ValueError(
            "Number of embeddings must match number of documents."
        )

    if not all(isinstance(doc, dict) for doc in documents):
        raise ValueError("Every document must be a dictionary.")

    vectors = _prepare_vectors(embeddings)

    if vectors.shape[0] != len(documents):
        raise ValueError(
            "Embedding count does not match document count."
        )

    # Normalize stored vectors for cosine similarity.
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    if index.ntotal != len(documents):
        raise RuntimeError(
            "FAISS index count does not match document count."
        )

    with _store_lock:
        _ensure_directory()

        index_path = _index_path()
        metadata_path = _metadata_path()

        index_tmp: str | None = None
        metadata_tmp: str | None = None

        try:
            # Create temporary files in the destination directory.
            with tempfile.NamedTemporaryFile(
                dir=str(index_path.parent),
                prefix="index_",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                index_tmp = temp_file.name

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(metadata_path.parent),
                prefix="metadata_",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                metadata_tmp = temp_file.name

                json.dump(
                    list(documents),
                    temp_file,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )

                temp_file.flush()
                os.fsync(temp_file.fileno())

            # Write the FAISS index before replacing destination files.
            faiss.write_index(index, index_tmp)

            # Replace destination files from the same directory.
            os.replace(index_tmp, index_path)
            index_tmp = None

            os.replace(metadata_tmp, metadata_path)
            metadata_tmp = None

        except Exception:
            logger.exception(
                "Failed to persist the FAISS vector store."
            )
            raise

        finally:
            for temporary_path in (index_tmp, metadata_tmp):
                if temporary_path:
                    try:
                        Path(temporary_path).unlink(missing_ok=True)
                    except OSError:
                        logger.warning(
                            "Could not remove a temporary store file."
                        )

    logger.info(
        "Vector store created: vectors=%d",
        index.ntotal,
    )

    return index


# ============================================================
# Load Vector Store
# ============================================================

def load_vectorstore() -> tuple[faiss.Index, list[dict[str, Any]]]:
    """
    Load and validate the persisted FAISS index and metadata.

    Returns:
        A tuple containing the FAISS index and document metadata.
    """
    with _store_lock:
        index_path = _index_path()
        metadata_path = _metadata_path()

        if not index_path.is_file():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not metadata_path.is_file():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}"
            )

        try:
            index = faiss.read_index(str(index_path))

            with metadata_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                documents = json.load(file)

        except (
            OSError,
            RuntimeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                "Unable to load the vector store."
            ) from exc

        if not isinstance(documents, list):
            raise RuntimeError(
                "Vector-store metadata must be a JSON list."
            )

        if not all(isinstance(doc, dict) for doc in documents):
            raise RuntimeError(
                "Vector-store metadata contains invalid documents."
            )

        if index.d <= 0:
            raise RuntimeError(
                "FAISS index dimension must be positive."
            )

        if index.ntotal != len(documents):
            raise RuntimeError(
                "FAISS vector count does not match metadata "
                "document count."
            )

        return index, documents


# ============================================================
# Search Vectors
# ============================================================

def search_vectors(
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Search for documents with the highest cosine similarity.

    Returns:
        Dictionaries containing text, score, and metadata.
    """
    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or top_k <= 0
    ):
        raise ValueError("top_k must be a positive integer.")

    if query_embedding is None:
        return []

    if (
        isinstance(query_embedding, (list, tuple))
        and not query_embedding
    ):
        return []

    query_vector = _normalize_query(query_embedding)

    index, documents = load_vectorstore()

    if index.ntotal == 0:
        return []

    if query_vector.shape[1] != index.d:
        raise ValueError(
            f"Query dimension ({query_vector.shape[1]}) "
            f"does not match index dimension ({index.d})."
        )

    search_k = min(top_k, index.ntotal)

    scores, indices = index.search(
        query_vector,
        search_k,
    )

    results: list[dict[str, Any]] = []

    for score, index_id in zip(scores[0], indices[0]):
        if index_id < 0 or index_id >= len(documents):
            continue

        document = documents[index_id]
        similarity = float(score)

        if not math.isfinite(similarity):
            continue

        text = document.get("text", "")
        if not isinstance(text, str):
            text = ""

        metadata = document.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        results.append(
            {
                "text": text,
                "score": similarity,
                "metadata": metadata,
            }
        )

    return results


# ============================================================
# Vector Store Status
# ============================================================

def vectorstore_exists() -> bool:
    """Check whether both persisted vector-store files exist."""
    return (
        _index_path().is_file()
        and _metadata_path().is_file()
    )


def get_vector_count() -> int:
    """Return the number of stored vectors, or zero if absent."""
    if not vectorstore_exists():
        return 0

    index, _ = load_vectorstore()

    return int(index.ntotal)
