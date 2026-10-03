# -*- coding: utf-8 -*-
"""Public project identity and draft capstone team roster.

Only the names recorded in the team's planning workbook are shown. The
workbook's role assignments are proposals, so this page does not present
them as actual contributions.
"""

import os
import sys
from html import escape

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project_identity import (
    COURSE_LABEL, GROUP_LABEL, PROJECT_DESCRIPTION, PROJECT_NAME,
    ROSTER_NOTE, TEAM_MEMBERS, TEAM_RESPONSIBILITIES,
)
from ui_common import LOGO_FULL_DARK, LOGO_FULL_LIGHT, page_banner, page_flow, require_login, render_context_copilot


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
page_flow("Meet the draft team and understand the product's boundaries", [
    ("Read the purpose", "See the problem and the human-controlled workflow."),
    ("Meet the group", "Review names transcribed from the team-plan workbook."),
    ("Set up your workspace", "Choose a readable theme and enter a display identity on Home."),
], "Names and roles require final team confirmation before academic submission.")

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
    st.caption("Group label pending final team confirmation")

st.divider()
st.subheader("Team members")
st.caption("Proposed responsibility areas for team confirmation—not verified claims about completed work.")
member_cards = []
for name in TEAM_MEMBERS:
    parts = name.split()
    initials = (parts[0][:2] if len(parts) == 1 and len(parts[0]) == 2
                else "".join(part[0] for part in parts)[:2]).upper()
    area, responsibility = TEAM_RESPONSIBILITIES[name]
    member_cards.append(
        f'<article class="iq-team-card" aria-label="Team member: {escape(name)}">'
        f'<div class="iq-team-initials" aria-hidden="true">{escape(initials)}</div>'
        f'<h3 class="iq-team-name">{escape(name)}</h3>'
        f'<p class="iq-team-role">{escape(area)}</p>'
        f'<p class="iq-team-note">{escape(responsibility)}</p>'
        '</article>'
    )
st.markdown('<section class="iq-team-grid" aria-label="Capstone team members">'
            + ''.join(member_cards) + '</section>', unsafe_allow_html=True)

st.info(ROSTER_NOTE)
st.caption("Another planning sheet mentions Soumya as a proposed backup presenter; team membership is still unconfirmed.")

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
