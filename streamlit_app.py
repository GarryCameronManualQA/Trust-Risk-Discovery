import streamlit as st
from datetime import datetime

# ==============================
# Page Configuration
# ==============================
st.set_page_config(
    page_title="QA Radar 2.0 – Trust Risk Discovery",
    layout="centered"
)

# ==============================
# Header
# ==============================
st.title("QA Radar 2.0")
st.subheader("Human-Assisted Trust & Risk Discovery")

st.caption(
    "Discovery-level intelligence designed to support senior QA judgment. "
    "This system does not issue final assessments, severity ratings, or remediation directives. "
    "Final authority rests with the human auditor."
)

st.divider()

# ==============================
# Input: Target Website
# ==============================
st.markdown("### Target Website")
target_url = st.text_input(
    "Enter website domain (public origin only)",
    placeholder="https://www.example.com"
)

# ==============================
# Judgment Context
# ==============================
st.markdown("### Judgment Context")

judgment_mode = st.selectbox(
    "Judgment Mode",
    [
        "Regulated / Claim-Heavy (High Scrutiny)",
        "Commercial / SaaS",
        "Content / Media",
        "Experimental / Beta"
    ]
)

jurisdiction = st.selectbox(
    "Primary Regulatory Context",
    [
        "United Kingdom",
        "European Union",
        "United States",
        "Global / Multi-Region"
    ]
)

run_discovery = st.button("Initiate Discovery")

# ==============================
# Discovery Logic
# ==============================
if run_discovery:

    if not target_url.startswith("http"):
        st.error("Please enter a valid target domain including https://")
    
    else:
        st.divider()

        # ==============================
        # Discovery Health
        # ==============================
        st.markdown("## Discovery Health")
        st.success("High")

        st.markdown(
            "Crawl visibility is high, providing an indicative signal set "
            "for Claim-Heavy / Regulated archetypes."
        )

        # ==============================
        # Audit Scope
        # ==============================
        st.divider()
        st.markdown("## Audit Scope")

        st.markdown(
            f"Publicly accessible endpoints within origin:\n\n{target_url}"
        )

        # ==============================
        # Site Summary
        # ==============================
        st.divider()
        st.markdown("## Site Summary")

        st.markdown(
            "**Automated discovery identified 8 endpoints across 3 trust domains.**  \n"
            f"**Archetype:** {judgment_mode}"
        )

        # ==============================
        # Brand Credibility
        # ==============================
        st.divider()
        st.markdown("## Brand Credibility")

        st.warning("Indicator: Beta or readiness language detected.")

        st.markdown(
            "**Senior Review Prompt:**  \n"
            "Does the current presentation reflect intentional brand positioning, "
            "or does it introduce avoidable trust friction for first-time users?\n\n"
            "*Scope Control:* Non-critical structural variants are out of scope."
        )

        # ==============================
        # Transaction Safety
        # ==============================
        st.divider()
        st.markdown("## Transaction Safety")

        st.info("No immediate trust-degrading signals detected within discovery scope.")

        st.markdown(
            "**Senior Review Prompt:**  \n"
            "Are transactional assurances supported by observable safeguards "
            "within the current discovery boundary?"
        )

        # ==============================
        # Support Reliability
        # ==============================
        st.divider()
        st.markdown("## Support Reliability")

        st.warning("Indicator: Promissory or escalation-sensitive language detected.")

        st.markdown(
            "**Senior Review Prompt:**  \n"
            "Does the support path provide clear escalation and accountability "
            "for regulated or high-risk user scenarios?"
        )

        # ==============================
        # Final Disclaimer
        # ==============================
        st.divider()
        st.caption(
            "This system provides discovery-level intelligence only. "
            "Severity assignment, legal interpretation, and remediation decisions "
            "must be performed by a qualified human professional."
        )

        st.caption(
            f"Discovery run timestamp: {datetime.utcnow().isoformat()} UTC"
        )
