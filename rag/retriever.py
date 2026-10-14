"""
Document retrieval utilities for the RAG pipeline.

Generates query embeddings, searches the FAISS vector store,
filters results by similarity, and builds context for the LLM.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from rag.embeddings import generate_embedding
from rag.vectorstore import search_vectors

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    top_k: int = 5,
    min_score: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Retrieve relevant document chunks for a query.

    Args:
        query: Customer question or search query.
        top_k: Maximum number of candidate results.
        min_score: Minimum accepted cosine-similarity score.

    Returns:
        Relevant document chunks with text, score, and metadata.

    Raises:
        ValueError: If the query is empty or arguments are invalid.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    if (
        isinstance(min_score, bool)
        or not isinstance(min_score, (int, float))
        or not math.isfinite(min_score)
        or not -1.0 <= min_score <= 1.0
    ):
        raise ValueError(
            "min_score must be a finite number between -1.0 and 1.0."
        )

    normalized_query = query.strip()

    # Generate the query embedding.
    query_embedding = generate_embedding(normalized_query)

    # Search the vector store. Operational search failures return no results.
    try:
        results = search_vectors(
            query_embedding=query_embedding,
            top_k=top_k,
        )
    except Exception:
        logger.exception("Vector search failed.")
        return []

    if not isinstance(results, list):
        logger.error("Vector search returned an invalid result collection.")
        return []

    filtered_results: list[dict[str, Any]] = []

    for result in results:
        if not isinstance(result, dict):
            continue

        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            continue

        raw_score = result.get("score")
        if isinstance(raw_score, bool) or not isinstance(
            raw_score, (int, float, str)
        ):
            continue

        try:
            score = float(raw_score)
        except (TypeError, ValueError, OverflowError):
            continue

        if not math.isfinite(score) or not -1.0 <= score <= 1.0:
            continue

        if score < min_score:
            continue

        metadata = result.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        filtered_results.append(
            {
                "text": text.strip(),
                "score": score,
                "metadata": metadata,
            }
        )

    logger.info(
        "Retrieval completed: candidates=%d, accepted=%d",
        len(results),
        len(filtered_results),
    )
    return filtered_results


def build_context(results: list[dict[str, Any]]) -> str:
    """
    Format retrieved chunks into context for the language model.

    Empty or malformed chunks are skipped. Document content should
    be treated as untrusted data by downstream prompt handling.
    """
    if not isinstance(results, (list, tuple)):
        raise TypeError("results must be a list or tuple.")

    context_parts: list[str] = []

    for result in results:
        if not isinstance(result, dict):
            continue

        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            continue

        document_number = len(context_parts) + 1
        context_parts.append(f"[Document {document_number}]\n{text.strip()}")

    return "\n\n".join(context_parts)


def retrieve_context(
    query: str,
    top_k: int = 5,
    min_score: float = 0.5,
) -> dict[str, Any]:
    """
    Retrieve relevant chunks and build LLM-ready context.

    Returns:
        A dictionary containing query, results, context, and found.
    """
    results = retrieve(
        query=query,
        top_k=top_k,
        min_score=min_score,
    )
    context = build_context(results)

    return {
        "query": query,
        "results": results,
        "context": context,
        "found": bool(results),
    }
