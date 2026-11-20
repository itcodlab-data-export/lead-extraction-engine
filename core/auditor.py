"""Domain resolver + live site auditor."""
import re
from urllib.parse import urlparse
import tldextract
_TLD = tldextract.TLDExtract(suffix_list_urls=())  # bundled snapshot, no network
from core import net, logger
log = logger.get()

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\d{5}[\s.-]?\d{5})")
_SOC = {"LinkedIn": "linkedin.com/company", "Instagram": "instagram.com/", "Facebook": "facebook.com/",
        "Twitter": "twitter.com/", "YouTube": "youtube.com/"}
CONTACT_PATHS = ["/contact", "/pages/contact", "/policies/contact-information", "/privacy-policy"]
INDUSTRY = [("Ecommerce_D2C", r"shopify|add to cart|checkout"), ("SaaS_Tech", r"saas|software|platform|api"),
            ("Agency_Marketing", r"agency|marketing services"), ("Fintech", r"fintech|payments|loan"),
            ("Healthcare", r"health|clinic|wellness"), ("Education", r"course|learning|school"),
            ("RealEstate", r"real estate|property|homes"), ("Travel_Hospitality", r"travel|hotel|tour"),
            ("Food_Beverage", r"restaurant|food|beverage|coffee"), ("Manufacturing", r"manufactur|industrial")]

def canonical(url):
    e = _TLD(urlparse(url if "//" in url else "//" + url).netloc or url)
    return f"{e.domain}.{e.suffix}".lower() if e.domain and e.suffix else ""

def _brand_match(company, html):
    tok = re.sub(r"\b(inc|llc|ltd|pvt|corp|co|limited|technologies|labs)\b\.?", "", company.lower())
    tok = re.sub(r"[^a-z0-9 ]", "", tok).split()
    return bool(tok) and tok[0] in html.lower()

def resolve(company, hint=""):
    cands = [hint] if hint else []
    slug = re.sub(r"[^a-z0-9]", "", company.lower())
    cands += [f"{slug}.com", f"{slug}.in", f"{slug}.co"]
    for c in cands:
        if not c:
            continue
        r = net.get(c if c.startswith("http") else f"https://{c}")
        if r is not None and r.status_code == 200 and (c == hint or _brand_match(company, r.text)):
            return canonical(r.url), r.text, r.url
    return "", "", ""

def audit(company, hint=""):
    dom, html, final = resolve(company, hint)
    if not dom:
        return None
    pages = [html]
    base = final.rstrip("/").split("?")[0]
    root = f"{urlparse(final).scheme}://{urlparse(final).netloc}"
    for p in CONTACT_PATHS:
        pages.append(net.text(root + p))
    blob = "\n".join(pages)
    emails = {e.lower() for e in _EMAIL.findall(blob) if e.lower().endswith(dom) or dom in e.lower()}
    phones = list(dict.fromkeys(m.strip() for m in _PHONE.findall(blob)))[:2]
    socials = {k: v for k, v in _soc(blob).items()}
    low = html.lower()
    pixel = bool(re.search(r"fbq\(|connect\.facebook\.net/.*fbevents|facebook pixel", low))
    capi = bool(re.search(r"capi|conversions api|server-side tagging", low))
    gtm = "googletagmanager.com/gtm.js" in low or "gtm-" in low
    shop = "cdn.shopify.com" in low or "shopify" in low
    facts = []
    if not pixel: facts.append("No Meta Pixel detected on homepage")
    if pixel and not capi: facts.append("Meta Pixel present, no CAPI signal")
    if not gtm: facts.append("No GTM container found")
    if shop: facts.append("Runs on Shopify")
    tag = next((t for t, rx in INDUSTRY if re.search(rx, low)), "Other")
    return {"domain": dom, "emails": sorted(emails)[:6], "phones": phones, "socials": socials,
            "industry": tag, "audit_facts": facts, "html": html, "root": root,
            "meta": f"Pixel: {pixel} | CAPI: {capi} | GTM: {gtm} | Shopify: {shop}"}

def _soc(blob):
    out = {}
    for k, frag in _SOC.items():
        m = re.search(r"https?://(?:www\.)?" + re.escape(frag) + r"[^\s\"'<>)]+", blob)
        if m: out[k] = m.group(0)
    return out
