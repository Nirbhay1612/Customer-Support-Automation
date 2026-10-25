
"""Streamlit dashboard for the AI Customer Support Automation System."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlsplit
import math
import requests
from ui_theme import apply_dark_theme
import streamlit as st


# ------------------------------------------------------------
# PROJECT CONFIGURATION
# ------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import settings
from ai.classifier import classify_intent
from rag.retriever import retrieve_context


# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="AI Automation Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_dark_theme()


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def bounded_setting(
    value: object,
    minimum: float,
    maximum: float,
    fallback: float,
) -> float:
    """Return a numeric setting clamped to the supported range."""

    try:
        if isinstance(value,(int,float,str)):
         number = float(value)

        if not 0 <= abs(number) < float("inf"):
            return fallback

        return max(minimum, min(maximum, number))
    except (TypeError, ValueError, OverflowError):
        return fallback


def valid_api_url(url: str) -> bool:
    """Allow HTTP(S) URLs with a hostname and no embedded credentials."""

    try:
        parsed = urlsplit(url.strip())

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and parsed.port != 0
        )
    except ValueError:
        return False


def safe_error_message(action: str) -> None:
    """Show a generic UI error without exposing internal exception details."""

    st.error(
        f"{action} failed. Check the application logs for details."
    )


# ------------------------------------------------------------
# STYLING
# ------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 10px;
            padding: 14px;
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🤖 AI Automation System")
st.caption(
    "Customer support intelligence, knowledge retrieval "
    "and backend connectivity."
)

st.divider()


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ System Configuration")

    st.write("**Application**")
    st.code(str(settings.APP_NAME))

    st.write("**Environment**")
    st.code(str(settings.ENVIRONMENT))

    st.write("**LLM Provider**")
    st.code(str(settings.LLM_PROVIDER))

    st.write("**LLM Model**")
    st.code(str(settings.LLM_MODEL))

    st.write("**Embedding Model**")
    st.code(str(settings.EMBEDDING_MODEL))

    st.divider()

    st.caption(
        "Service status is confirmed only when the corresponding "
        "health check or operation succeeds."
    )


# ------------------------------------------------------------
# DASHBOARD OVERVIEW
# ------------------------------------------------------------

st.subheader("System Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Environment", str(settings.ENVIRONMENT))

with col2:
    st.metric("LLM Provider", str(settings.LLM_PROVIDER).upper())

with col3:
    st.metric("Knowledge Retrieval", "Configured")

st.caption(
    "These values describe the configured system, not live service health."
)

st.divider()


# ------------------------------------------------------------
# FEATURE TABS
# ------------------------------------------------------------

classifier_tab, rag_tab, api_tab = st.tabs(
    [
        "🧠 Intent Classifier",
        "📚 Knowledge Search",
        "🔌 API Health",
    ]
)


# ------------------------------------------------------------
# AI INTENT CLASSIFIER
# ------------------------------------------------------------

with classifier_tab:
    st.subheader("AI Intent Classifier")

    st.write(
        "Enter a customer message to identify the predicted support intent."
    )

    with st.form("intent_classifier_form"):
        message = st.text_area(
            "Customer message",
            placeholder="Example: Where is my order?",
            height=130,
            max_chars=5000,
        )

        classify_submitted = st.form_submit_button(
            "Classify Intent",
            type="primary",
        )

    if classify_submitted:
        if not message.strip():
            st.warning("Please enter a customer message.")
        else:
            with st.spinner("Classifying customer request..."):
                try:
                    result = classify_intent(message.strip())

                    if not isinstance(result, dict):
                        raise ValueError("Unexpected classifier response.")

                    intent = result.get("intent", "unknown")
                    confidence = bounded_setting(
                        result.get("confidence", 0.0),
                        0.0,
                        1.0,
                        0.0,
                    )

                    metric_col1, metric_col2 = st.columns(2)

                    with metric_col1:
                        st.metric("Detected Intent", str(intent))

                    with metric_col2:
                        st.metric("Confidence", f"{confidence:.0%}")

                    st.write("**Reason**")
                    st.write(
                        str(
                            result.get(
                                "reason",
                                "No explanation provided.",
                            )
                        )
                    )

                    with st.expander("Classifier Response"):
                        st.json(result)

                except Exception:
                    safe_error_message("Intent classification")


# ------------------------------------------------------------
# RAG KNOWLEDGE SEARCH
# ------------------------------------------------------------

with rag_tab:
    st.subheader("RAG Knowledge Search")

    st.write(
        "Retrieve relevant knowledge-base documents for a customer question."
    )

    default_top_k = int(
        bounded_setting(
            settings.TOP_K,
            1,
            10,
            3,
        )
    )

    default_threshold = bounded_setting(
        settings.SIMILARITY_THRESHOLD,
        0.0,
        1.0,
        0.5,
    )

    with st.form("rag_search_form"):
        rag_query = st.text_area(
            "Knowledge-base question",
            placeholder="Example: What is the refund policy?",
            height=110,
            max_chars=5000,
        )

        top_k = st.slider(
            "Maximum documents",
            min_value=1,
            max_value=10,
            value=default_top_k,
        )

        min_score = st.slider(
            "Minimum similarity score",
            min_value=0.0,
            max_value=1.0,
            value=default_threshold,
            step=0.05,
        )

        rag_submitted = st.form_submit_button(
            "Search Knowledge Base",
            type="primary",
        )

    if rag_submitted:
        if not rag_query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Searching the knowledge base..."):
                try:
                    result = retrieve_context(
                        query=rag_query.strip(),
                        top_k=top_k,
                        min_score=min_score,
                    )

                    if not isinstance(result, dict):
                        raise ValueError("Unexpected retrieval response.")

                    documents = result.get("results", [])

                    if not isinstance(documents, list):
                        raise ValueError("Invalid retrieval results.")

                    if not result.get("found") or not documents:
                        st.warning(
                            "No sufficiently relevant information was found."
                        )
                    else:
                        st.success(
                            f"Retrieved {len(documents)} relevant document(s)."
                        )

                        for index, document in enumerate(
                            documents,
                            start=1,
                        ):
                            if not isinstance(document, dict):
                                continue

                            score = bounded_setting(
                                document.get("score", 0.0),
                                0.0,
                                1.0,
                                0.0,
                            )

                            metadata = document.get("metadata", {})

                            if not isinstance(metadata, dict):
                                metadata = {}

                            source = metadata.get(
                                "source",
                                "Unknown source",
                            )

                            with st.expander(
                                f"Document {index} · Similarity: {score:.3f}"
                            ):
                                st.caption(f"Source: {source}")
                                st.write(
                                    document.get(
                                        "text",
                                        "No document text available.",
                                    )
                                )

                        context = result.get("context", "")

                        if context:
                            with st.expander("Combined Retrieved Context"):
                                st.code(str(context), language="text")

                except Exception:
                    safe_error_message("Knowledge-base search")


# ------------------------------------------------------------
# API HEALTH CHECK
# ------------------------------------------------------------

with api_tab:
    st.subheader("Backend API Connectivity")

    st.write(
        "Check whether the configured backend health endpoint responds."
    )

    api_url = st.text_input(
        "API Base URL",
        value="http://localhost:8000",
        help="Enter the base URL of your running FastAPI application.",
    )

    check_api = st.button(
        "Check API Health",
        type="primary",
    )

    if check_api:
        normalized_url = api_url.strip().rstrip("/")

        if not valid_api_url(normalized_url):
            st.error(
                "Enter a valid HTTP or HTTPS URL without embedded credentials."
            )
        else:
            try:
                response = requests.get(
                    f"{normalized_url}/health",
                    timeout=5,
                    allow_redirects=False,
                )

                if response.status_code == 200:
                    st.success("API health endpoint responded successfully.")

                    try:
                        body = response.json()
                        st.json(body)
                    except ValueError:
                        st.info(
                            "The endpoint returned HTTP 200, "
                            "but its response was not valid JSON."
                        )

                else:
                    st.error(
                        f"Health check returned HTTP {response.status_code}."
                    )

            except requests.RequestException:
                safe_error_message("API health check")


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.divider()

st.caption(
    f"{settings.APP_NAME} · Version {settings.APP_VERSION}"
)
