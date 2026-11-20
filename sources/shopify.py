"""Source 2: D2C / Shopify seed. Search dorks + cross-audit of companies from other sources."""
import re, config
from urllib.parse import unquote
from core import net, logger
log = logger.get()

DORKS = {"US": '"powered by shopify" "USD" store',
         "INDIA": '"powered by shopify" "INR" store'}

def fetch(prior=None):
    out = []
    for c in config.countries():
        html = net.text("https://html.duckduckgo.com/html/", params={"q": DORKS[c]})
        for m in re.finditer(r'uddg=([^&"]+)', html):
            url = unquote(m.group(1))
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
            if host and "duckduckgo" not in host:
                out.append({"company": host.split(".")[0].title(), "country": c,
                            "source_platform": "Shopify_Dork", "signal": "D2C_Shopify",
                            "source_url": url, "evidence": "Shopify store found via search",
                            "domain_hint": host, "people": []})
        if len(out) > 25:
            break
    # cross-audit: every company from Source 1 & 3 is also checked for Shopify by the auditor
    log.info("shopify: %d seeds", len(out))
    return out[:30]
