"""Batch 1c: Product Hunt API v2 launches (US & India). Skips cleanly when PRODUCTHUNT_TOKEN is unset."""
import os, re, time
from urllib.parse import urlparse
import requests, config
from core import logger
log = logger.get()

API = "https://api.producthunt.com/v2/api/graphql"
QUERY = "{ posts(order: NEWEST, first: 30) { edges { node { name tagline url website } } } }"
_IN = re.compile(r"\b(india|indian|bengaluru|bangalore|mumbai|delhi|hyderabad|pune|chennai)\b", re.I)

def country_of(node):
    """PH exposes no location field: India if .in domain or India mentioned, else US."""
    host = urlparse(node.get("website") or "").netloc
    return "INDIA" if host.endswith(".in") or _IN.search(f"{node.get('name','')} {node.get('tagline','')}") else "US"

def _resolve(url):
    try:   # PH 'website' is a redirect; follow it once to learn the real host
        r = requests.get(url, timeout=config.HTTP_TIMEOUT, allow_redirects=True, headers={"User-Agent": config.BROWSER_UA})
        host = urlparse(r.url).netloc.replace("www.", "")
        return "" if "producthunt.com" in host else host
    except Exception:
        return ""

def fetch(deadline=None):
    tok = os.getenv("PRODUCTHUNT_TOKEN")
    if not tok:
        log.info("producthunt: PRODUCTHUNT_TOKEN not set, skipped"); return []
    r = requests.post(API, json={"query": QUERY}, headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    edges = (((r.json().get("data") or {}).get("posts") or {}).get("edges")) if r.status_code == 200 else None
    if not edges:
        log.warning("producthunt: no data (HTTP %s)", r.status_code); return []
    out = []
    for e in edges:
        n = e["node"]; c = country_of(n)
        if c not in config.countries(): continue
        if deadline and time.time() > deadline: break
        out.append({"company": n["name"], "country": c, "source_platform": "ProductHunt", "signal": "Launch",
                    "source_url": n.get("url", ""), "evidence": f"Product Hunt launch: {n.get('tagline','')[:120]}",
                    "domain_hint": _resolve(n.get("website") or ""), "people": []})
    log.info("producthunt: %d signals", len(out))
    return out
