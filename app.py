# -*- coding: utf-8 -*-
"""
InvestigateIQ — app entry point / navigation router.

This file used to BE the landing page directly, using Streamlit's classic
pages/-directory auto-discovery for every other screen. That convention
derives each sidebar label from the raw filename — which is exactly why
the entry point showed up in the sidebar as the literal, lowercase "app":
there's no capital letter in "app.py" for Streamlit to show. Every other
page looked fine only because their filenames already happened to be
capitalized ("0_Case_Queue.py" -> "Case Queue").

st.navigation() replaces that filename-guessing with an explicit list
below — every page gets a real title and icon, not a derived one. The
landing page's own content moved to pages/home.py; this file is now just
the router. URL paths are unchanged (still derived from each file's name,
e.g. /Case_Queue), so every existing st.switch_page()/st.page_link() call
elsewhere in the app keeps working without modification.
"""
import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home", icon="🔎", default=True),
        st.Page("pages/7_Project_Team.py", title="Project & Team", icon="👥"),
        st.Page("pages/0_Case_Queue.py", title="Case Queue", icon="🗂️"),
        st.Page("pages/2_Investigation_Demo.py", title="Investigation Workspace", icon="🕵️", url_path="Investigation_Workspace"),
        st.Page("pages/8_Evidence_RAG.py", title="Evidence & RAG", icon="🧩"),
        st.Page("pages/3_Compliance_Queue.py", title="Compliance Queue", icon="🛡️"),
        st.Page("pages/5_Analytics.py", title="Analytics", icon="📊"),
        st.Page("pages/6_Global_Search.py", title="Global Search", icon="🔍"),
        st.Page("pages/1_Admin_Knowledge_Base.py", title="Admin: Knowledge Base", icon="🔐"),
        st.Page("pages/4_Admin_Rule_Config.py", title="Admin: Rule Config", icon="⚙️"),
    ]
)
pg.run()
