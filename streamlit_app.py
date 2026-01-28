import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
import json

# -------------------------
# QA RADAR DOCTRINE (ENFORCED)
# -------------------------
DOCTRINE_SUMMARY = {
    "evidence_bar": [
        "Direct Observation (visible in UI/copy/flow/behavior)",
        "Pattern Consistency (repeats across pages/states/domains)",
        "Clear User Impact Path (plain-language trust/money/clarity risk)",
        "Grounded Professional Inference (industry norms / comparable cases)"
    ],
    "severity_discipline": [
        "Severity is based on credible consequence, not possibility.",
        "If confidence is low, severity is capped.",
        "No alarmist phrasing; measured, defensible language only."
    ],
    "scope_control_exclusions": [
        "Internal CSS naming conventions",
        "Minor layout preferences",
        "Non-user-impacting technical purity",
        "Hypothetical future risks without evidence"
    ],
    "human_in_loop": [
        "Tool supports senior judgment; it does not issue final severity or directives unless evidence allows.",
        "Senior review prompts are mandatory."
    ]
}

# -------------------------
# CONFIG
# -------------------------
DEFAULT_MAX_PAGES = 10
REQUEST_TIMEOUT = 12
HEADERS = {
    "User-Agent": "QA-Radar-TrustRiskDiscovery/2.0 (+Human-in-the-loop)"
}

# -------------------------
# HELPERS
# -------------------------
def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if not raw.startswith("http"):
        raw = "https://" + raw
    return raw

def same_origin(a: str, b: str) -> bool:
    try:
        pa, pb = urlparse(a), urlparse(b)
        return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)
    except Exception:
        return False

def safe_get(url: str):
    """
    One fetch per URL. Returns (final_url, status_code, html_text, error_str).
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        ct = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "text/html" in ct:
            return resp.url, resp.status_code, resp.text, ""
        # Still return page text if it's HTML-ish but content-type missing
        if resp.status_code == 200 and resp.text and "<html" in resp.text.lower():
            return resp.url, resp.status_code, resp.text, ""
        return resp.url, resp.status_code, "", f"Non-HTML or non-200 response (status={resp.status_code}, content-type={ct})"
    except Exception as e:
        return url, None, "", str(e)

def extract_internal_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base = urlparse(base_url)
    base_origin = f"{base.scheme}://{base.netloc}"

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        full = urljoin(base_origin, href)
        p = urlparse(full)

        # Only same-origin links, drop query/fragment noise
        if p.netloc == base.netloc:
            clean = f"{p.scheme}://{p.netloc}{p.path}"
            if clean.endswith("/"):
                clean = clean[:-1]
            links.add(clean)

    # Keep homepage first if present
    links_list = sorted(list(links))
    return links_list

def classify_trust_domain(url: str) -> str:
    p = urlparse(url)
    path = (p.path or "").lower()

    # Support / Trust-critical
    if any(x in path for x in ["help", "support", "contact", "faq", "returns", "refund", "shipping", "privacy", "terms"]):
        return "Support Reliability"

    # Transaction
    if any(x in path for x in ["checkout", "cart", "pay", "pricing", "subscribe", "billing", "plans", "order"]):
        return "Transaction Safety"

    return "Brand Credibility"

def detect_observable_signals(html: str):
    """
    Evidence-only signals. We do not claim issues; we flag observable indicators.
    Returns list of signal dicts.
    """
    signals = []
    lower = html.lower()

    # Beta / early access language
    if re.search(r"\b(beta|early access|preview)\b", html, re.IGNORECASE):
        signals.append({
            "signal": "Beta / preview language detected",
            "evidence_type": "Direct Observation",
            "why_it_can_matter": "Users may interpret 'beta' as reduced reliability unless expectations are clearly set.",
            "confidence": "Moderate"
        })

    # Strong claim language (note: NOT saying it's false)
    if re.search(r"\b(world'?s first|best|guarantee|risk[- ]free|perfect)\b", html, re.IGNORECASE):
        signals.append({
            "signal": "Strong marketing claim language present",
            "evidence_type": "Direct Observation",
            "why_it_can_matter": "Claim density can raise the evidence bar for trust (proof, policies, support clarity).",
            "confidence": "Low"
        })

    # Heading structure indicator (not a defect by default)
    h1_count = lower.count("<h1")
    if h1_count > 1:
        signals.append({
            "signal": f"Multiple H1 headings detected (count={h1_count})",
            "evidence_type": "Direct Observation",
            "why_it_can_matter": "Could be brand-led design or accessibility/SEO trade-off; only matters if it harms clarity or navigation.",
            "confidence": "Low"
        })

    # Trust policy hints
    if "privacy" in lower or "terms" in lower:
        signals.append({
            "signal": "Policy/Legal references detected (privacy/terms)",
            "evidence_type": "Direct Observation",
            "why_it_can_matter": "Good trust signal; verify discoverability and clarity in key user journeys.",
            "confidence": "Moderate"
        })

    # Support discoverability hints
    if re.search(r"\b(help|support|contact)\b", html, re.IGNORECASE):
        signals.append({
            "signal": "Support/help language detected",
            "evidence_type": "Direct Observation",
            "why_it_can_matter": "Trust improves when escalation routes are visible at the point of friction.",
            "confidence": "Moderate"
        })

    return signals

def cap_severity_by_confidence(severity: str, confidence: str) -> str:
    """
    Doctrine rule: if confidence is low, cap severity.
    """
    sev_rank = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    conf_cap = {"Low": 2, "Moderate": 3, "High": 4}  # low confidence caps at Medium
    max_allowed = conf_cap.get(confidence, 2)
    # If proposed severity exceeds cap, reduce it
    if sev_rank.get(severity, 1) > max_allowed:
        # find highest severity within cap
        for s, r in sorted(sev_rank.items(), key=lambda x: x[1], reverse=True):
            if r <= max_allowed:
                return s
    return severity

def propose_discovery_severity(signals, judgment_mode: bool):
    """
    Discovery-only = we avoid hard severities; we use "Indicative" bands.
    In Judgment Mode we can suggest a band, still gated by confidence.
    """
    if not signals:
        return ("Low", "High")  # severity, confidence

    # Basic heuristic: more signals => higher attention
    # Still conservative: never jump to Critical without clear user-impact path (which we don't have from HTML alone).
    count = len(signals)
    conf_levels = {"Low": 0, "Moderate": 1, "High": 2}

    # overall confidence is the max of individual confidences (still cautious)
    conf_score = max(conf_levels.get(s["confidence"], 0) for s in signals)
    overall_conf = "Low" if conf_score == 0 else ("Moderate" if conf_score == 1 else "High")

    if not judgment_mode:
        # Discovery mode: keep severity low/medium only
        if count >= 3:
            return ("Medium", overall_conf)
        return ("Low", overall_conf)

    # Judgment mode: still capped
    if count >= 4:
        sev = "High"
    elif count >= 2:
        sev = "Medium"
    else:
        sev = "Low"

    sev = cap_severity_by_confidence(sev, overall_conf)
    return (sev, overall_conf)

def senior_review_prompt(domain: str) -> str:
    if domain == "Transaction Safety":
        return "Does the commercial intent align with functional readiness, pricing clarity, and refund/chargeback reassurance at the point of purchase?"
    if domain == "Support Reliability":
        return "If a user hits friction, are escalation routes obvious, fast, and reassuring (not buried or circular)?"
    return "Does the page’s claim density match visible proof (policies, trust signals, clear positioning), without over-promising?"

def archetype_guess(base_html: str) -> str:
    """
    Light archetype guess based on visible language. Non-assertive.
    """
    l = base_html.lower()
    if any(x in l for x in ["hipaa", "medical", "clinic", "patient", "compliance"]):
        return "Claim-Heavy / Regulated"
    if any(x in l for x in ["pricing", "subscribe", "checkout", "cart"]):
        return "Commercial / Conversion-Heavy"
    if any(x in l for x in ["enterprise", "security", "soc2", "gdpr"]):
        return "B2B Trust-Critical"
    return "General Product / Brand-led"

def build_brief(base_url: str, pages):
    """
    Build a structured, client-safe discovery brief.
    """
    domains = {"Brand Credibility": [], "Transaction Safety": [], "Support Reliability": []}
    for p in pages:
        domains[p["trust_domain"]].append(p)

    # Count endpoints and domains
    total = len(pages)
    domains_present = sum(1 for k, v in domains.items() if v)

    return total, domains_present, domains

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="QA Radar – Trust Risk Discovery", layout="wide")

st.title("QA Radar – Trust Risk Discovery")
st.caption("Evidence-led discovery to support senior QA judgment. No manufactured concern. Human authority remains final.")

with st.expander("Internal Doctrine (enforced)"):
    st.write("**Evidence Bar** (required to escalate beyond indicative):")
    for x in DOCTRINE_SUMMARY["evidence_bar"]:
        st.write(f"• {x}")
    st.write("**Severity Discipline**:")
    for x in DOCTRINE_SUMMARY["severity_discipline"]:
        st.write(f"• {x}")
    st.write("**Scope Control (excluded by default)**:")
    for x in DOCTRINE_SUMMARY["scope_control_exclusions"]:
        st.write(f"• {x}")

colA, colB, colC = st.columns([2, 1, 1])
with colA:
    raw_url = st.text_input("Target domain or URL", placeholder="https://www.nike.com")
with colB:
    max_pages = st.number_input("Max pages", min_value=1, max_value=25, value=DEFAULT_MAX_PAGES, step=1)
with colC:
    judgment_mode = st.toggle("Judgment Mode", value=True, help="Adds interpretive reasoning, still evidence-gated.")

run = st.button("Run Discovery", type="primary")

if run:
    base_url = normalize_url(raw_url)
    if not base_url:
        st.error("Please enter a valid URL.")
        st.stop()

    st.info(f"Discovery starting: {base_url}")
    t0 = time.time()

    final_home, status, home_html, err = safe_get(base_url)
    if not home_html:
        st.error("Discovery failed: unable to retrieve homepage HTML.")
        st.code(f"URL: {final_home}\nStatus: {status}\nError: {err}")
        st.stop()

    # Canonical base origin
    base_origin = f"{urlparse(final_home).scheme}://{urlparse(final_home).netloc}"

    # Extract internal links from homepage
    candidate_links = extract_internal_links(home_html, final_home)

    # Ensure homepage included, then bound
    all_targets = [base_origin] + candidate_links
    # De-dupe preserving order
    seen = set()
    bounded = []
    for u in all_targets:
        if u not in seen:
            seen.add(u)
            bounded.append(u)
        if len(bounded) >= int(max_pages):
            break

    st.write(f"**Bounded targets:** {len(bounded)} within origin `{base_origin}`")

    pages = []
    fetch_errors = []

    # Fetch each once
    for u in bounded:
        fu, stc, html, e = safe_get(u)
        if html:
            td = classify_trust_domain(fu)
            signals = detect_observable_signals(html)
            sev, conf = propose_discovery_severity(signals, judgment_mode)

            pages.append({
                "url": fu,
                "trust_domain": td,
                "signals": signals,
                "proposed_attention_band": sev,          # not a defect severity
                "confidence": conf,
                "senior_review_prompt": senior_review_prompt(td)
            })
        else:
            fetch_errors.append({"url": u, "status": stc, "error": e})

    # Discovery Health
    elapsed = round(time.time() - t0, 2)
    st.success(f"Discovery completed in {elapsed}s. Pages analyzed: {len(pages)}")

    if len(pages) >= 6:
        discovery_health = "High"
        health_note = "Multiple publicly accessible endpoints detected; signal set is indicative and useful."
    elif len(pages) >= 2:
        discovery_health = "Medium"
        health_note = "Limited visibility; findings are indicative and should be validated manually."
    else:
        discovery_health = "Limited"
        health_note = "Crawl visibility constrained; treat findings as minimal signal only."

    archetype = archetype_guess(home_html)

    st.subheader("Discovery Brief (PRE-AUDIT)")
    st.write(f"**Discovery Health:** {discovery_health}")
    st.write(f"**Confidence Level:** {'High' if discovery_health=='High' else ('Moderate' if discovery_health=='Medium' else 'Low')}")
    st.write(f"**Audit Scope:** Publicly accessible endpoints within origin: `{base_origin}` (Trust Domain Analysis)")
    st.write(f"**Archetype (indicative):** {archetype}")
    st.write(f"**Health Note:** {health_note}")

    total, domains_present, by_domain = build_brief(base_origin, pages)
    st.write(f"**Site Summary:** {total} endpoints analyzed across {domains_present} trust domains (bounded discovery).")

    # Display findings grouped by domain
    st.subheader("Findings by Trust Domain")

    def domain_block(domain_name: str, items):
        st.markdown(f"### {domain_name}")
        if not items:
            st.write("No endpoints surfaced for this trust domain within bounded discovery.")
            return

        for p in items:
            with st.expander(p["url"]):
                st.write(f"**Attention Band (indicative):** {p['proposed_attention_band']}")
                st.write(f"**Confidence:** {p['confidence']}")

                if p["signals"]:
                    st.write("**Observed Signals (evidence-led):**")
                    for s in p["signals"]:
                        st.write(f"• **{s['signal']}**")
                        st.caption(f"Evidence: {s['evidence_type']} | Why it can matter: {s['why_it_can_matter']} | Signal confidence: {s['confidence']}")
                else:
                    st.write("No immediate trust-degrading signals observed within discovery scope.")

                st.write("**Senior Review Prompt:**")
                st.write(p["senior_review_prompt"])

                st.write("**Scope Control (What Not To Fix):**")
                st.write("Exclude non-user-impacting structural preferences, internal CSS naming, and cosmetic layout debates unless linked to a real user impact path.")

                # Client-ready justification is kept honest and short
                st.write("**Client-safe justification:**")
                if p["signals"]:
                    st.write("Indicative signals surfaced that may warrant targeted manual validation to protect user trust and prevent misalignment between claims and user expectations.")
                else:
                    st.write("No risk indicators surfaced in this bounded scope; manual validation can confirm coverage and ensure trust-critical paths remain friction-free.")

    domain_block("Brand Credibility", by_domain["Brand Credibility"])
    domain_block("Transaction Safety", by_domain["Transaction Safety"])
    domain_block("Support Reliability", by_domain["Support Reliability"])

    # Errors (transparent)
    if fetch_errors:
        st.subheader("Discovery Constraints (Transparency)")
        st.write("Some endpoints could not be analyzed (non-HTML responses, blocks, timeouts). This is not treated as a defect; it constrains visibility.")
        st.dataframe(fetch_errors, use_container_width=True)

    # Export bundle
    export_payload = {
        "tool": "QA Radar – Trust Risk Discovery",
        "version": "2.0",
        "timestamp_unix": int(time.time()),
        "base_origin": base_origin,
        "discovery_health": discovery_health,
        "archetype_indicative": archetype,
        "pages": pages,
        "fetch_errors": fetch_errors,
        "doctrine": DOCTRINE_SUMMARY
    }

    st.subheader("Export / Copy")
    st.write("Use this for your paper trail or to paste into a report builder.")
    st.download_button(
        "Download JSON (evidence bundle)",
        data=json.dumps(export_payload, indent=2).encode("utf-8"),
        file_name="qa_radar_discovery_bundle.json",
        mime="application/json"
    )

    st.caption(
        "Disclaimer: This system provides discovery-level intelligence to support senior QA judgment. "
        "It does not issue final defect confirmation, severity, or remediation directives without sufficient evidence. "
        "Final authority rests with the human auditor."
    )
