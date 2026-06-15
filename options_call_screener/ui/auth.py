"""Simple PIN gate for private Streamlit Cloud deployments."""

from __future__ import annotations

import streamlit as st


def _expected_pin() -> str | None:
    """Return configured PIN, or None if auth is disabled (local dev without secrets)."""
    try:
        return str(st.secrets["app_password"]).strip()
    except (KeyError, FileNotFoundError, AttributeError):
        return None


def check_pin() -> bool:
    """Return True when the user entered the correct PIN or auth is not configured."""
    expected = _expected_pin()
    if not expected:
        return True

    if st.session_state.get("pin_ok"):
        return True

    st.title("Private Scanner")
    st.caption("Enter your security PIN to continue.")

    pin = st.text_input(
        "4–6 digit PIN",
        type="password",
        max_chars=6,
        key="app_pin_input",
    )

    if pin:
        if not pin.isdigit():
            st.error("PIN must be numbers only.")
        elif pin == expected:
            st.session_state["pin_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")

    return False
