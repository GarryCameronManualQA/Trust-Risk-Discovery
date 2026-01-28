import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time

# -------------------------
# CONFIG
# -------------------------
MAX_PAGES = 10
REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "QA-Radar-Discovery/1.0 (+Trust Risk Audit)"
}

# -------------------------
# HELPERS
# -------------------------

def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url

def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.text
    except Exception:
        return None
    return None

def extract_internal_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urlparse(base_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain:
            links.add(parsed.scheme + "://" + parsed.netloc + parsed.path)

    return list(links)

def classify_domain(url):
    path = url.lower()
    if any(x in path for x in ["checkout", "cart", "pay", "pricing", "subscribe"]):
        return "Transaction Safety"
    if any(x in path for x in ["help", "support", "contact", "faq", "returns"]):
        return "Support Reliability"
    return "Brand Credibility"

def detect_trust_signals(html):
    signals = []

    if re.search(r"\b(beta|early access)\b", html, re.IGNORECASE):
        signals.append("Beta / early-access language detected")

    if re.search(r"\bguarantee|risk-free|best\b", html, re.IGNORECASE):
        signals.append("Strong marketing claims present")

    if "<h1" in html.lower():
        h1_count = html.lower().count("<h1")
        if h1_count > 1:
            signals.append("Multiple H1 headings detected")

    if re.search(r"\bsubscribe|pricing|buy\b", html, re.IGNORECASE):
        signals.append("Commercial intent signals present")

    return signals

# -------------------------
# STREAMLIT UI
# -------------------------

st.set_page_config(page_title="QA Radar – Trust Risk Discovery", layout="wide")
st.title("QA Radar – Trust Risk Discovery")
st.caption("Discovery-level intelligence to support senior QA judgment. Human authority required.")

target_url = st.text_input("Enter a website domain or URL", placeholder="https://example.com")

if st.button("Run Discovery"):
    if not target_url:
        st.warning("Please enter a valid URL.")
        st.stop()

    start_time = time.time()
    base_url = normalize_url(target_url)
    st.info(f"Starting discovery on {base_url}")

    homepage_html = fetch_html(base_url)

    if not homepage_html:
        st.error("Discovery failed: Unable to retrieve homepage.")
        st.stop()

    links = extract_internal_links(homepage_html, base_url)
    links = links[:MAX_PAGES]

    discovered_pages = [(base_url, homepage_html)] + [
        (link, fetch_html(link)) for link in links if fetch_html(link)
    ]

    st.success(f"Discovery completed. Pages analyzed: {len(discovered_pages)}")

    st.subheader("Discovery Health")
    if len(discovered_pages) >= 5:
        st.write("**High** – Multiple publicly accessible endpoints detected.")
    elif len(discovered_pages) >= 2:
        st.write("**Medium** – Limited visibility, indicative signals only.")
    else:
        st.write("**Limited** – Crawl visibility constrained.")

    st.subheader("Findings")

    for url, html in discovered_pages:
        domain = classify_domain(url)
        signals = detect_trust_signals(html)

        with st.expander(url):
            st.write(f"**Trust Domain:** {domain}")

            if signals:
                st.write("**Observed Signals:**")
                for s in signals:
                    st.write(f"- {s}")
            else:
                st.write("No immediate trust-degrading signals observed.")

            st.write("**Senior Review Prompt:**")
            if domain == "Transaction Safety":
                st.write("Does the commercial intent align with functional readiness and clarity?")
            elif domain == "Support Reliability":
                st.write("Are escalation paths clear if a user encounters friction?")
            else:
                st.write("Does the presentation reinforce credibility without over-claiming?")

    elapsed = round(time.time() - start_time, 2)
    st.caption(f"Discovery completed in {elapsed} seconds.")

    st.markdown("---")
    st.caption(
        "This system provides discovery-level intelligence only. "
        "It does not issue severity ratings or remediation directives. "
        "Final judgment rests with the human auditor."
    )
