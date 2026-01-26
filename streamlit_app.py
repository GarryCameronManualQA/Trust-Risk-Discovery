import streamlit as st
from datetime import datetime

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="QA Radar 2.0 — Trust Risk Discovery",
    layout="centered"
)

# -----------------------------
# Header
# -----------------------------
st.title("QA Radar 2.0")
st.subheader("Human-Assisted Trust & Risk Discovery")

st.caption(
    "Discovery-level intelligence designed to support senior QA judgment. "
    "This system does not issue final assessments, severity ratings, or remediation directives. "
    "Final authority rests with the human auditor."
)

st.divider()

# -----------------------------
# Input: Target Website
# -----------------------------
st.markdown("### Target Website")

target_url = st.text_input(
    "Enter website domain (public origin only)",
   
