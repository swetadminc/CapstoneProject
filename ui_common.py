# -*- coding: utf-8 -*-
"""
Shared session identity — pending item #2 ("Login / role-based access").

Deliberately still mock auth (no password, no real user database) — that
matches the documented NFR scope everywhere else in this build (see the
Admin passcode gates). What this adds is a single place to say who you are
and what role you're acting in, instead of retyping your name into a
different text box on every page. Every page that records a decision still
requires that name explicitly at submit time — this doesn't remove that
requirement, it just removes the retyping.
"""
import streamlit as st

ROLES = ["Investigator", "Team Lead", "Compliance Officer", "Admin"]


def require_login():
    """Call near the top of every page. Shows a one-time name+role form if
    the session doesn't have an identity yet; otherwise renders the small
    sidebar identity badge and returns (name, role) immediately."""
    if "user_name" not in st.session_state or "user_role" not in st.session_state:
        st.markdown("### 👤 Who's using InvestigateIQ?")
        st.caption(
            "Prototype-level identity, not real authentication (no password) — matches the mock-auth scope "
            "used throughout this build. This is what gets attributed on every decision you record."
        )
        name = st.text_input("Your name")
        role = st.selectbox("Your role", ROLES)
        if st.button("Continue", type="primary"):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                st.session_state["user_name"] = name.strip()
                st.session_state["user_role"] = role
                st.rerun()
        st.stop()

    with st.sidebar:
        st.markdown(f"**👤 {st.session_state['user_name']}**")
        st.caption(f"Role: {st.session_state['user_role']}")
        if st.button("Switch user", key="switch_user_btn"):
            del st.session_state["user_name"]
            del st.session_state["user_role"]
            st.rerun()

    return st.session_state["user_name"], st.session_state["user_role"]


def role_warning(current_role: str, expected_role: str):
    """Soft nudge, not a hard block — matches the mock-auth scope. A hard,
    convincing-looking access-control wall here would overstate what this
    prototype's auth actually is."""
    if current_role != expected_role:
        st.warning(
            f"You're logged in as **{current_role}**. This screen is normally used by **{expected_role}** — "
            "you can still proceed (mock auth, no real access control), but the attribution below will reflect "
            "your actual logged-in identity."
        )
