"""Deep direct-email scraping: contact/about/team/policy pages, mailto:, JSON-LD, CF-obfuscated.
Pure page fetches from the company's own site: 0 SMTP, 0 credits, 0 IP risk."""
import re, json
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from core import net

PATHS = ["/contact", "/contact-us", "/about", "/team", "/policies/contact-information", "/privacy-policy"]
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_JUNK_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")

def _cf_decode(h):
    try:
        k = int(h[:2], 16)
        return "".join(chr(int(h[i:i + 2], 16) ^ k) for i in range(2, len(h), 2))
    except Exception:
        return ""

def _jsonld_emails(soup):
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.lower() == "email" and isinstance(v, str): out.append(v.replace("mailto:", ""))
                else: walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    for tag in soup.find_all("script", type="application/ld+json"):
        try: walk(json.loads(tag.string or tag.get_text() or ""))
        except Exception: continue
    return out

def extract_emails(html):
    """All emails found in one HTML page (text, mailto:, JSON-LD, Cloudflare data-cfemail)."""
    if not html: return set()
    soup = BeautifulSoup(html, "html.parser")
    found = set(_EMAIL.findall(soup.get_text(" ")))
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            found.update(_EMAIL.findall(a["href"][7:].split("?")[0]))
    found.update(e for raw in _jsonld_emails(soup) for e in _EMAIL.findall(raw))
    for el in soup.find_all(attrs={"data-cfemail": True}):
        found.update(_EMAIL.findall(_cf_decode(el["data-cfemail"])))
    return {e.lower().strip(".") for e in found if not e.lower().endswith(_JUNK_EXT)}

def deep_emails(root, domain, homepage_html=""):
    """Emails on the company's own domain from the home page + the standard contact paths."""
    with ThreadPoolExecutor(max_workers=4) as ex:
        pages = list(ex.map(lambda p: net.text(root + p), PATHS))
    found = set(extract_emails(homepage_html))
    for html in pages:
        found |= extract_emails(html)
    return sorted(e for e in found if e.split("@")[1] == domain or e.endswith("." + domain))
