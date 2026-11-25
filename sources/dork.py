"""Shared dork helper for Batch 2/3: search DDG (Bing fallback) -> [{url,title,snippet}]; rotation slot; domain finder."""
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
import config
from core import net
from core.safety_guard import utc_now
from sources import ats

DOMAIN = re.compile(r"\b((?:[a-z0-9-]{2,}\.)+(?:com|co|in|io|shop|store|co\.in|net|org|ai|app))\b", re.I)
SKIP = ("reddit.", "twitter.", "x.com", "linkedin.", "youtube.", "google.", "facebook.", "instagram.", "shopify.com", "myshopify.com",
        "kickstarter.", "indiegogo.", "flippa.", "acquire.com", "amazon.", "github.", "medium.", "duckduckgo.", "bing.", "t.co", "trustpilot.")

def slot(n):
    """3-hour slot of the UTC day, folded to 0..n-1, so every run rotates to a different query set."""
    return (utc_now().hour // 3 + utc_now().timetuple().tm_yday * 8) % max(1, n)

def pick(items, k):
    s = slot(len(items))
    return [items[(s * k + i) % len(items)] for i in range(min(k, len(items)))]

def search(q):
    out = []
    soup = BeautifulSoup(net.text("https://html.duckduckgo.com/html/", params={"q": q}), "html.parser")
    for a in soup.select("a.result__a"):
        m = re.search(r"uddg=([^&]+)", a.get("href", ""))
        sn = a.find_parent(class_="result")
        sn = sn.select_one(".result__snippet") if sn else None
        out.append({"url": unquote(m.group(1)) if m else a.get("href", ""), "title": a.get_text(" ", strip=True),
                    "snippet": sn.get_text(" ", strip=True) if sn else ""})
    if out: return out
    soup = BeautifulSoup(net.text("https://www.bing.com/search", params={"q": q}), "html.parser")
    for li in soup.select("li.b_algo"):
        a = li.find("a", href=True)
        p = li.select_one(".b_caption p")
        if a: out.append({"url": ats._bing_url(a["href"]), "title": a.get_text(" ", strip=True), "snippet": p.get_text(" ", strip=True) if p else ""})
    return out

def site_in(text):
    """First business domain mentioned in text (platforms excluded) or ''."""
    for m in DOMAIN.findall(text or ""):
        d = m.lower()
        if not any(s in d for s in SKIP): return d
    return ""

def signal(company, country, platform, sig, url, ev, domain=""):
    return {"company": company, "country": country, "source_platform": platform, "signal": sig,
            "source_url": url, "evidence": ev[:160], "domain_hint": domain, "people": []}

def run(queries, platform, sig, country, deadline, build):
    """queries -> signals via build(result)->(company, domain, evidence) or None."""
    import time
    out, seen = [], set()
    for q in queries:
        if deadline and time.time() > deadline: break
        for r in search(q):
            b = build(r)
            if not b or b[0].lower() in seen: continue
            seen.add(b[0].lower()); out.append(signal(b[0], country, platform, sig, r["url"], b[2], b[1]))
        net.jitter(config.DORK_JITTER)
    return out
