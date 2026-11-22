"""Batch 1b: Shopify App Store 1-2 star reviews of Meta Pixel / CAPI apps (merchants with broken tracking)."""
import re, time
from urllib.parse import unquote
from bs4 import BeautifulSoup
import config
from core import net, logger
log = logger.get()

SEED_APPS = ["facebook"]   # Meta's own "Facebook & Instagram" channel; more are discovered by dork
RESERVED = {"search", "categories", "partners", "stories", "sitemap", "login", "collections", "built-for-shopify"}
COUNTRY = {"US": {"united states"}, "INDIA": {"india"}}
BROKEN = re.compile(r"pixel|capi|conversions? api|tracking|track|event|attribution|purchase|sync|not working|broken|disconnect|duplicate", re.I)
URL = "https://apps.shopify.com/{h}/reviews?ratings%5B%5D=1&ratings%5B%5D=2&page={p}"

def discover():
    html = net.text("https://html.duckduckgo.com/html/", params={"q": "site:apps.shopify.com meta pixel conversions api facebook"})
    hs = [h for h in re.findall(r"apps\.shopify\.com%2F([a-z0-9-]+)", html) + re.findall(r"apps\.shopify\.com/([a-z0-9-]+)", unquote(html))
          if h not in RESERVED]
    return list(dict.fromkeys(SEED_APPS + hs))[:6]

def parse(html, handle):
    """Reviews rated 1-2 stars -> list of dicts (store, country, text)."""
    out = []
    for b in BeautifulSoup(html, "html.parser").find_all(attrs={"data-merchant-review": True}):
        star = b.find(attrs={"aria-label": re.compile(r"\d out of 5")})
        rating = int(re.match(r"\d", star["aria-label"]).group(0)) if star else 0
        name = b.find(class_=re.compile(r"tw-text-heading-xs"))
        body = b.find(class_=re.compile(r"tw-mb-xs"))
        if not name or not body or rating not in (1, 2): continue
        nxt = name.find_next("div")
        out.append({"store": name.get_text(" ", strip=True), "country": nxt.get_text(" ", strip=True) if nxt else "",
                    "text": body.get_text(" ", strip=True), "app": handle, "rating": rating})
    return out

def fetch(deadline=None):
    out, want = [], {c: COUNTRY[c] for c in config.countries()}
    for h in discover():
        for page in (1, 2):
            if deadline and time.time() > deadline: return out
            for r in parse(net.text(URL.format(h=h, p=page)), h):
                c = next((k for k, v in want.items() if r["country"].lower() in v), None)
                if not c or not BROKEN.search(r["text"]): continue
                out.append({"company": r["store"], "country": c, "source_platform": "Shopify_AppStore",
                            "signal": "Broken_Tracking_Review", "source_url": URL.format(h=h, p=page),
                            "evidence": f"{r['rating']}★ review of {h}: {r['text'][:140]}",
                            "domain_hint": "", "people": []})
            time.sleep(1)
    log.info("shopify_reviews: %d signals", len(out))
    return out
