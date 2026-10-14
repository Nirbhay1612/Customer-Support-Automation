
"""
Document loading utilities for the RAG pipeline.

Supports TXT, Markdown, and PDF files with consistent metadata,
input validation, and per-document error handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config import settings


logger = logging.getLogger(__name__)


# ============================================================
# Supported File Types
# ============================================================

SUPPORTED_EXTENSIONS = frozenset({
    ".txt",
    ".md",
    ".pdf",
})


# ============================================================
# Load Single Text File
# ============================================================

def load_text_file(file_path: Path) -> str:
    """Load a UTF-8 encoded text or Markdown file."""
    file_path = Path(file_path)

    try:
        return file_path.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        logger.warning(
            "Unable to decode document as UTF-8: %s",
            file_path.name,
        )
        raise

    except OSError:
        logger.exception(
            "Unable to read document: %s",
            file_path.name,
        )
        raise


# ============================================================
# Load PDF File
# ============================================================

def load_pdf_file(file_path: Path) -> str:
    """Extract text from a PDF document."""
    file_path = Path(file_path)

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support requires pypdf. Install it with: pip install pypdf"
        ) from exc

    try:
        reader = PdfReader(str(file_path))

        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
            except Exception as exc:
                raise ValueError(
                    "The PDF is encrypted and cannot be read without "
                    "a supported password."
                ) from exc

            if not decrypted:
                raise ValueError(
                    "The PDF is password-protected and cannot be read."
                )

        pages: list[str] = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
            except Exception as exc:
                logger.warning(
                    "Text extraction failed for %s, page %d.",
                    file_path.name,
                    page_number,
                )
                raise RuntimeError(
                    f"Failed to extract text from PDF page {page_number}."
                ) from exc

            if page_text and page_text.strip():
                pages.append(page_text.strip())

        extracted_text = "\n\n".join(pages)

        if not extracted_text.strip():
            logger.warning(
                "No extractable text found in PDF: %s",
                file_path.name,
            )

        return extracted_text

    except (ValueError, RuntimeError):
        raise

    except Exception as exc:
        logger.exception(
            "Failed to read PDF document: %s",
            file_path.name,
        )
        raise RuntimeError(
            f"Unable to process PDF document: {file_path.name}"
        ) from exc


# ============================================================
# Load Single Document
# ============================================================

def load_document(
    file_path: str | Path,
) -> dict[str, Any]:
    """
    Load one supported document.

    Returns:
        {
            "text": "...",
            "metadata": {
                "source": "...",
                "file_name": "...",
                "file_type": "..."
            }
        }
    """
    path = Path(file_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(
            f"Document does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension or '<none>'}"
        )

    if extension in {".txt", ".md"}:
        text = load_text_file(path)
    else:
        text = load_pdf_file(path)

    text = text.strip()

    if not text:
        logger.warning(
            "Document contains no extractable text: %s",
            path.name,
        )

    return {
        "text": text,
        "metadata": {
            "source": str(path),
            "file_name": path.name,
            "file_type": extension,
        },
    }


# ============================================================
# Load Documents From Directory
# ============================================================

def load_documents(
    directory: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Recursively load supported documents from a directory.

    Unreadable documents are skipped so that one bad file does not
    prevent the remaining documents from being processed.
    """
    if directory is None:
        directory = settings.DOCUMENTS_PATH

    directory = Path(directory).expanduser()

    if not directory.exists():
        raise FileNotFoundError(
            f"Document directory does not exist: {directory}"
        )

    if not directory.is_dir():
        raise ValueError(
            f"Path is not a directory: {directory}"
        )

    documents: list[dict[str, Any]] = []
    skipped_count = 0

    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            document = load_document(file_path)

            if document["text"]:
                documents.append(document)
            else:
                skipped_count += 1

        except Exception:
            skipped_count += 1

            logger.warning(
                "Skipping unreadable document: %s",
                file_path.name,
                exc_info=True,
            )

    logger.info(
        "Document loading completed: loaded=%d, skipped=%d",
        len(documents),
        skipped_count,
    )

    return documents
