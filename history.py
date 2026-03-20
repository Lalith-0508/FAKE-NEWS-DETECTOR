"""
history.py — Manages session-based analysis history using Streamlit session state.
"""

import streamlit as st
from datetime import datetime


def add_to_history(text: str, result: dict):
    """Add an analysis result to session history."""
    if "fakescope_history" not in st.session_state:
        st.session_state["fakescope_history"] = []

    entry = {
        "text": text,
        "verdict": result.get("verdict", "UNCLEAR"),
        "confidence": result.get("confidence", 0),
        "summary": result.get("summary", ""),
        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
    }
    st.session_state["fakescope_history"].append(entry)


def get_history() -> list:
    """Return the full history list."""
    return st.session_state.get("fakescope_history", [])


def clear_history():
    """Clear all history entries."""
    st.session_state["fakescope_history"] = []
