"""Source 3: funding & launches. US = SEC EDGAR Form D (+Product Hunt), India = funding RSS."""
import re, time, xml.etree.ElementTree as ET
import config
from core import net, logger
log = logger.get()

SEC_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=D&count=40&output=atom"
RSS = ["https://inc42.com/feed/", "https://entrackr.com/feed", "https://yourstory.com/feed"]
_FUND = re.compile(r"(raises|raised|secures|bags|funding|seed|series [a-c])", re.I)
_NAME = re.compile(r"^(.{2,40}?)\s+(raises|raised|secures|bags|closes|gets|lands)\b", re.I)

def _sec():
    out = []
    xml = net.text(SEC_FEED, headers={"User-Agent": config.SEC_USER_AGENT})
    if not xml:
        return out
    try:
        root = ET.fromstring(xml)
    except Exception:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for e in root.findall("a:entry", ns)[:30]:
        title = (e.findtext("a:title", "", ns) or "")
        m = re.match(r"D\s*-\s*(.+?)\s*\(", title)
        link = e.find("a:link", ns)
        if m:
            out.append({"company": m.group(1).strip().title(), "country": "US",
                        "source_platform": "SEC_EDGAR_FormD", "signal": "Funding",
                        "source_url": link.get("href") if link is not None else "",
                        "evidence": "SEC Form D filed: " + title[:100],
                        "domain_hint": "", "people": []})
        time.sleep(0.25)
    return out

def _rss():
    out = []
    for url in RSS:
        xml = net.text(url)
        if not xml:
            continue
        try:
            items = ET.fromstring(xml).findall(".//item")[:25]
        except Exception:
            continue
        for it in items:
            t = (it.findtext("title") or "").strip()
            m = _NAME.match(t)
            if m and _FUND.search(t):
                out.append({"company": m.group(1).strip(), "country": "INDIA",
                            "source_platform": url.split("/")[2], "signal": "Funding",
                            "source_url": it.findtext("link") or "",
                            "evidence": t[:160], "domain_hint": "", "people": []})
    return out

def fetch():
    out = []
    if "US" in config.countries():
        out += _sec()
    if "INDIA" in config.countries():
        out += _rss()
    log.info("funding: %d signals", len(out))
    return out
