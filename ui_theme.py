
import streamlit as st


def apply_dark_theme():
    """Apply a clean, professional navy-and-blue Streamlit theme."""

    st.markdown(
        """
        <style>
        /* Main application background */
        .stApp {
            background: #080d18;
            color: #e5edf9;
        }

        /* Main content spacing */
        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #0c1424;
            border-right: 1px solid #1e2b42;
        }

        [data-testid="stSidebar"] * {
            color: #dce7f7;
        }

        /* Headings */
        h1, h2, h3 {
            color: #f1f5ff !important;
            letter-spacing: -0.4px;
        }

        /* Paragraphs and labels */
        p, label, .stMarkdown {
            color: #c1cee0;
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"],
        .stNumberInput input {
            background: #101a2c !important;
            color: #edf4ff !important;
            border: 1px solid #293954 !important;
            border-radius: 10px !important;
        }

        /* Buttons */
        .stButton > button {
            background: #2563eb;
            color: white;
            border: 1px solid #3b82f6;
            border-radius: 10px;
            padding: 0.55rem 1rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background: #1d4ed8;
            border-color: #60a5fa;
            color: white;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: #101a2c;
            border: 1px solid #22324c;
            padding: 18px;
            border-radius: 14px;
        }

        [data-testid="stMetricLabel"] {
            color: #9eb0ca !important;
        }

        [data-testid="stMetricValue"] {
            color: #60a5fa !important;
        }

        /* Chat messages */
        [data-testid="stChatMessage"] {
            background: #101a2c;
            border: 1px solid #22324c;
            border-radius: 14px;
            padding: 12px;
            margin-bottom: 12px;
        }

        /* Tables */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid #22324c;
            border-radius: 10px;
            overflow: hidden;
        }

        /* Dividers */
        hr {
            border-color: #22324c;
        }

        /* Success, warning and error messages */
        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        /* Remove Streamlit top header background */
        [data-testid="stHeader"] {
            background: rgba(8, 13, 24, 0.9);
        }

        /* Footer */
        footer {
            visibility: hidden;
        }

        /* Links */
        a {
            color: #60a5fa !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
