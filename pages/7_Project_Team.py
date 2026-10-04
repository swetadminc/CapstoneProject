# -*- coding: utf-8 -*-
"""Public project identity and confirmed capstone team roster."""

import os
import sys
from html import escape

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project_identity import (
    COURSE_LABEL, GROUP_LABEL, PROJECT_DESCRIPTION, PROJECT_NAME,
    ROSTER_NOTE, TEAM_MEMBERS,
)
from ui_common import (
    LOGO_FULL_DARK, LOGO_FULL_LIGHT, WORKFLOW_ROLE_DETAILS, page_banner,
    page_flow, require_login, render_context_copilot,
)


def flip_theme():
    new_value = not bool(st.session_state.get("iq_dark_mode"))
    st.session_state["iq_dark_mode"] = new_value
    st.session_state["dark_mode_toggle"] = new_value


def clear_demo_identity():
    st.session_state.pop("user_name", None)
    st.session_state.pop("user_role", None)

st.set_page_config(page_title="InvestigateIQ — Project & Team", page_icon="👥", layout="wide")
user_name, user_role = require_login(allow_guest=True)
render_context_copilot("Project & Team", st.session_state.get("active_case_id"))

page_banner("👥", "Project & Team", "The people and purpose behind InvestigateIQ")
page_flow("Meet the team and understand the product's boundaries", [
    ("Read the purpose", "See the problem and the human-controlled workflow."),
    ("Meet the group", "Review the confirmed project roster."),
    ("Set up your workspace", "Choose a readable theme and enter a display identity on Home."),
], "Contact details and unverified individual contribution claims are not displayed.")

intro, identity = st.columns([2, 1])
with intro:
    st.markdown(f"## {PROJECT_NAME}")
    st.markdown(f"**{PROJECT_DESCRIPTION}.**")
    st.write(
        "Our goal is to show how an investigator can move from an alert to an "
        "evidence-linked draft, make a reasoned human decision, and keep an audit trail. "
        "Escalated cases then receive separate human Compliance follow-up."
    )
    st.caption("All customer and transaction data is fictional. This is not a bank deployment or regulatory filing tool.")
with identity:
    logo = LOGO_FULL_DARK if st.session_state.get("iq_dark_mode") else LOGO_FULL_LIGHT
    st.image(logo, width=300)
    st.markdown("**Trace the evidence. Own the decision.**")
    st.markdown(f"**{GROUP_LABEL}**")
    st.caption(COURSE_LABEL)
    st.caption("Project group label")

st.divider()
st.subheader("Team members")
st.caption("Confirmed project roster. Contact details and individual contribution claims are not displayed.")
member_cards = []
for name in TEAM_MEMBERS:
    parts = name.split()
    initials = (parts[0][:2] if len(parts) == 1 and len(parts[0]) == 2
                else "".join(part[0] for part in parts)[:2]).upper()
    member_cards.append(
        f'<article class="iq-team-card" aria-label="Team member: {escape(name)}">'
        f'<div class="iq-team-initials" aria-hidden="true">{escape(initials)}</div>'
        f'<h3 class="iq-team-name">{escape(name)}</h3>'
        '<p class="iq-team-role">Confirmed project member</p>'
        '<p class="iq-team-note">Individual responsibilities are not attributed on this page.</p>'
        '</article>'
    )
st.markdown('<section class="iq-team-grid" aria-label="Capstone team members">'
            + ''.join(member_cards) + '</section>', unsafe_allow_html=True)

st.info(ROSTER_NOTE)

st.divider()
st.subheader("Workflow roles in this demo")
st.caption("These describe how the application is used. They are not titles or responsibilities assigned to the people listed above.")
with st.expander("What each role can do", expanded=False):
    role_cards = []
    for role, (purpose, actions, boundary) in WORKFLOW_ROLE_DETAILS.items():
        role_cards.append(
            f'<article class="iq-role-card" aria-label="Workflow role: {escape(role)}">'
            f'<h3>{escape(role)}</h3><p class="iq-role-purpose">{escape(purpose)}</p>'
            f'<p>{escape(actions)}</p><p class="iq-role-boundary"><strong>Boundary:</strong> {escape(boundary)}</p>'
            '</article>'
        )
    st.markdown('<section class="iq-role-grid" aria-label="Workflow role definitions">'
                + ''.join(role_cards) + '</section>', unsafe_allow_html=True)
    st.caption("Selecting a role is a display label for this fictional demo. It does not enforce permissions; restricted Admin areas require the separate passcode.")

st.divider()
st.subheader("Display settings")
st.write("Choose the display that is easiest to read. Your display identity attributes decisions; this environment does not authenticate users.")
st.button(
    "Use light mode" if st.session_state.get("iq_dark_mode") else "Use dark mode",
    on_click=flip_theme,
    key="team_theme_button",
    help="Change the display theme for this browser session; no case data is changed.",
)
if user_name:
    st.caption(f"Current display identity: {user_name} · {user_role}.")
    st.button("Change display identity", on_click=clear_demo_identity, key="team_change_user_button",
              help="Clear the current display name and role; previously recorded decisions remain in the audit log.")
else:
    st.page_link("pages/home.py", label="Return Home to enter your workspace →",
                 help="Choose a display name and workflow role on Home before investigating a case.")

st.page_link("pages/0_Case_Queue.py", label="Explore the Case Queue →",
             help="Browse preloaded fictional alerts and open a case for investigation.")
