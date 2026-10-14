import json

import pytest

from rag.loader import load_document
from rag.retriever import build_context, retrieve
from rag.vectorstore import create_vectorstore, vectorstore_exists


# ============================================================
# DOCUMENT LOADER TESTS
# ============================================================

def test_load_text_document(tmp_path):
    """Text document should be loaded successfully."""

    file_path = tmp_path / "test.txt"

    file_path.write_text(
        "This is a test customer support document.",
        encoding="utf-8",
    )

    result = load_document(file_path)

    assert result["text"] == "This is a test customer support document."
    assert result["metadata"]["file_name"] == "test.txt"
    assert result["metadata"]["file_type"] == ".txt"


def test_load_markdown_document(tmp_path):
    """Markdown document should be loaded successfully."""

    file_path = tmp_path / "test.md"

    file_path.write_text(
        "# Refund Policy\nRefunds are processed after eligibility checks.",
        encoding="utf-8",
    )

    result = load_document(file_path)

    assert "Refund Policy" in result["text"]
    assert result["metadata"]["file_type"] == ".md"


def test_load_unsupported_document(tmp_path):
    """Unsupported file types should raise an error."""

    file_path = tmp_path / "test.csv"

    file_path.write_text(
        "id,name\n1,test",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_document(file_path)


# ============================================================
# VECTOR STORE TESTS
# ============================================================

def test_create_vectorstore(tmp_path, monkeypatch):
    """Vector store should be created with valid embeddings."""

    import rag.vectorstore as vectorstore_module

    monkeypatch.setattr(
        vectorstore_module,
        "VECTORSTORE_DIR",
        tmp_path,
    )

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]

    documents = [
        {
            "text": "Refunds are processed after eligibility checks.",
            "metadata": {
                "source": "refund_policy.md",
            },
        },
        {
            "text": "Orders can be tracked using the tracking ID.",
            "metadata": {
                "source": "order_policy.md",
            },
        },
    ]

    result = create_vectorstore(
        embeddings=embeddings,
        documents=documents,
    )

    assert result is not None
    assert vectorstore_exists() is True


def test_create_vectorstore_mismatched_lengths():
    """Embeddings and documents must have the same length."""

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]

    documents = [
        {
            "text": "Only one document.",
            "metadata": {},
        }
    ]

    with pytest.raises(ValueError):
        create_vectorstore(
            embeddings=embeddings,
            documents=documents,
        )


# ============================================================
# RETRIEVER TESTS
# ============================================================

def test_build_context():
    """Retrieved documents should be converted into usable context."""

    results = [
        {
            "text": "Refunds are available for eligible orders.",
            "score": 0.92,
            "metadata": {
                "source": "refund_policy.md",
            },
        },
        {
            "text": "Refund processing time depends on the payment provider.",
            "score": 0.84,
            "metadata": {
                "source": "refund_policy.md",
            },
        },
    ]

    context = build_context(results)

    assert "Refunds are available" in context
    assert "Refund processing time" in context
    assert "[Document 1]" in context
    assert "[Document 2]" in context


def test_build_context_empty_results():
    """Empty retrieval results should return empty context."""

    context = build_context([])

    assert context == ""


def test_retrieve(monkeypatch):
    """Retriever should return relevant documents."""

    fake_embedding = [0.1, 0.2, 0.3]

    fake_results = [
        {
            "text": "Refunds are available for eligible orders.",
            "score": 0.91,
            "metadata": {
                "source": "refund_policy.md",
            },
        },
        {
            "text": "Refund processing may take several business days.",
            "score": 0.82,
            "metadata": {
                "source": "refund_policy.md",
            },
        },
    ]

    monkeypatch.setattr(
        "rag.retriever.generate_embedding",
        lambda query: fake_embedding,
    )

    monkeypatch.setattr(
        "rag.retriever.search_vectors",
        lambda query_embedding, top_k=5: fake_results,
    )

    results = retrieve(
        query="How can I get a refund?",
        top_k=5,
        min_score=0.5,
    )

    assert len(results) == 2
    assert results[0]["score"] == 0.91
    assert "Refunds" in results[0]["text"]


def test_retrieve_filters_low_scores(monkeypatch):
    """Low similarity results should be filtered."""

    monkeypatch.setattr(
        "rag.retriever.generate_embedding",
        lambda query: [0.1, 0.2, 0.3],
    )

    monkeypatch.setattr(
        "rag.retriever.search_vectors",
        lambda query_embedding, top_k=5: [
            {
                "text": "Highly relevant document.",
                "score": 0.90,
                "metadata": {},
            },
            {
                "text": "Weakly relevant document.",
                "score": 0.20,
                "metadata": {},
            },
        ],
    )

    results = retrieve(
        query="refund policy",
        top_k=5,
        min_score=0.5,
    )

    assert len(results) == 1
    assert results[0]["score"] == 0.90


def test_retrieve_empty_query():
    """Empty queries should be rejected."""

    with pytest.raises(ValueError):
        retrieve("")


# ============================================================
# FULL RAG CONTEXT TEST
# ============================================================

def test_retrieval_context(monkeypatch):
    """Retriever context should contain query and retrieved information."""

    fake_results = [
        {
            "text": "Customers can request a refund using their order ID.",
            "score": 0.95,
            "metadata": {
                "source": "refund_policy.md",
            },
        }
    ]

    monkeypatch.setattr(
        "rag.retriever.generate_embedding",
        lambda query: [0.1, 0.2, 0.3],
    )

    monkeypatch.setattr(
        "rag.retriever.search_vectors",
        lambda query_embedding, top_k=5: fake_results,
    )

    from rag.retriever import retrieve_context

    result = retrieve_context(
        query="How do I request a refund?"
    )

    assert result["query"] == "How do I request a refund?"
    assert result["found"] is True
    assert len(result["results"]) == 1
    assert "refund" in result["context"].lower()