"""Batch 1a: ATS direct career pages (Greenhouse / Lever / Ashby / Workable) found via DDG + Bing dorks."""
import re, time, base64
from urllib.parse import unquote, urlparse, parse_qs
import config
from core import net, logger
log = logger.get()

ATS = {"boards.greenhouse.io": 1, "job-boards.greenhouse.io": 1, "jobs.lever.co": 1,
       "jobs.ashbyhq.com": 1, "apply.workable.com": 1}   # host -> path segment holding the company slug
ROLES = ["Meta Ads", "Performance Marketing", "Shopify"]
LOC = {"US": "United States", "INDIA": "India"}

def _bing_url(u):
    """Bing wraps results as bing.com/ck/a?...&u=a1<base64url>."""
    if "bing.com/ck/a" not in u: return u
    v = (parse_qs(urlparse(u).query).get("u") or [""])[0]
    try: return base64.urlsafe_b64decode(v[2:] + "=" * (-len(v[2:]) % 4)).decode()
    except Exception: return ""

def parse_results(html):
    urls = [unquote(m) for m in re.findall(r'uddg=([^&"]+)', html)]
    urls += [_bing_url(m.replace("&amp;", "&")) for m in re.findall(r'<h2><a href="(https?://[^"]+)"', html)]
    return [u for u in urls if u]

def company_of(url):
    p = urlparse(url)
    host = (p.netloc or "").lower()
    if host not in ATS: return ""
    seg = [x for x in p.path.split("/") if x]
    if len(seg) < 1 or seg[0] in ("embed", "jobs", "j"): return ""
    return re.sub(r"[-_]+", " ", seg[0]).title()

def fetch(deadline=None):
    out, seen = [], set()
    for c in config.countries():
        for host in ("boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "apply.workable.com"):
            for role in ROLES:
                if deadline and time.time() > deadline: return out
                q = f'site:{host} "{role}" "{LOC[c]}"'
                html = net.text("https://html.duckduckgo.com/html/", params={"q": q}) \
                    or net.text("https://www.bing.com/search", params={"q": q})
                for url in parse_results(html):
                    name = company_of(url)
                    if name and (name.lower(), c) not in seen:
                        seen.add((name.lower(), c))
                        out.append({"company": name, "country": c, "source_platform": "ATS_" + host.split(".")[1],
                                    "signal": "Hiring", "source_url": url,
                                    "evidence": f"Open {role} role on {host}", "domain_hint": "", "people": []})
                net.jitter(config.DORK_JITTER)
    log.info("ats: %d signals", len(out))
    return out
