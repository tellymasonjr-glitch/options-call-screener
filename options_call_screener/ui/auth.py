"""Simple PIN gate for private Streamlit Cloud deployments."""

from __future__ import annotations

import streamlit as st


def _auth_config() -> tuple[str | None, str]:
    """
    Return (expected_pin, mode).

    mode:
      - "off"     -> no auth (local dev, no secrets file)
      - "ready"   -> PIN required; expected_pin is set
      - "missing" -> secrets exist but app_password not set (Cloud misconfiguration)
    """
    try:
        if st.secrets.get("disable_auth", False):
            return None, "off"
        pin = str(st.secrets["app_password"]).strip()
        if pin:
            return pin, "ready"
        return None, "missing"
    except FileNotFoundError:
        return None, "off"
    except (KeyError, AttributeError, TypeError):
        return None, "missing"


def check_pin() -> bool:
    """Return True when authenticated or auth is disabled for local dev."""
    mode = _auth_config()[1]
    if mode == "off":
        return True

    if st.session_state.get("pin_ok"):
        return True

    st.title("Private Scanner")
    st.caption("Enter your security PIN to open the app.")

    expected, mode = _auth_config()

    if mode == "missing" or not expected:
        st.error(
            "PIN is not configured yet. If you own this app, open **Streamlit Cloud → "
            "Settings → Secrets** and add:\n\n"
            "```toml\napp_password = \"1234\"\n```\n\n"
            "Replace `1234` with your own 4–6 digit PIN, save, and wait for the app to reboot."
        )
        return False

    pin = st.text_input(
        "Security PIN",
        type="password",
        max_chars=6,
        placeholder="Enter 4–6 digits",
        key="app_pin_input",
    )

    if pin:
        if not pin.isdigit():
            st.error("PIN must be numbers only.")
        elif pin == expected:
            st.session_state["pin_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect PIN. Try again.")

    return False
