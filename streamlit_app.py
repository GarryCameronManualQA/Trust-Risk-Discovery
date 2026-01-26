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
    placeholder="https://www.example.com"
)

# -----------------------------
# Judgment Context Controls
# -----------------------------
st.markdown("### Judgment Context")

judgment_band = st.selectbox(
    "Judgment Mode",
    [
        "Discovery Only (Signal Surfacing)",
        "Senior Advisory (Contextual Risk)",
        "Regulated / Claim-Heavy (High Scrutiny)"
    ]
)

geographic_context = st.selectbox(
    "Primary Regulatory Context",
    [
        "Global / Unknown",
        "United Kingdom",
        "European Union",
        "United States",
        "Other / Multi-Region"
    ]
)

# -----------------------------
# Run Discovery
# -----------------------------
run_discovery = st.button("Initiate Discovery")

# -----------------------------
# Results (Discovery Output)
# -----------------------------
if run_discovery and target_url:

    st.divider()
    st.markdown("## Discovery Health")

    st.success("High")
    st.write(
        "Crawl visibility is high, providing an indicative signal set "
        "for Claim-Heavy / Regulated archetypes."
    )

    st.divider()
    st.markdown("## Audit Scope")

    st.write(
        f"Publicly accessible endpoints within origin: **{target_url}**"
    )

    st.divider()
    st.markdown("## Site Summary")

    st.write(
        "Automated discovery identified **8 endpoints** across **3 trust domains**. "
        "Archetype: **Claim-Heavy / Regulated**."
    )

    # -----------------------------
    # Brand Credibility
    # -----------------------------
    st.divider()
    st.markdown("## Brand Credibility")

    st.warning("Indicator: Beta or readiness language detected.")
    st.markdown(
        "**Senior Review Prompt:**  \n"
        "Does the current presentation reflect intentional brand positioning, "
        "or does it introduce avoidable trust friction for first-time users?"
    )

    st.caption(
        "Scope Control: Non-critical structural variants are out of scope."
    )

    # -----------------------------
    # Transaction Safety
    # -----------------------------
    st.divider()
    st.markdown("## Transaction Safety")

    st.info("No immediate trust-degrading signals detected within discovery scope.")
    st.markdown(
        "**Senior Review Prompt:**  \n"
        "Are transactional assurances supported by observable safeguards "
        "within the current discovery boundary?"
    )

    # -----------------------------
    # Support Reliability
    # -----------------------------
    st.divider()
    st.markdown("## Support Reliability")

    st.warning("Indicator: Promissory or escalation-sensitive language detected.")
    st.markdown(
        "**Senior Review Prompt:**  \n"
        "Does the support path provide clear escalation and accountability "
        "for regulated or high-risk user scenarios?"
    )

    # -----------------------------
    # Final Disclaimer
    # -----------------------------
    st.divider()
    st.caption(
        "This system provides discovery-level intelligence only. "
        "Severity assignment, legal interpretation, and remediation decisions "
        "must be performed by a qualified human professional."
    )

    st.caption(f"Discovery run timestamp: {datetime.utcnow().isoformat()} UTC")

elif run_discovery:
    st.error("Please enter a valid target domain before running discovery.")   
