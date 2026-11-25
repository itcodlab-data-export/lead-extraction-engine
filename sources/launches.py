"""Batch 3b: Kickstarter / Indiegogo campaigns of physical D2C brands that name their own website (new brand = needs ads)."""
import config
from sources import dork

QUERIES = ['site:kickstarter.com/projects "our website"', 'site:indiegogo.com/projects "our website"',
           'site:kickstarter.com/projects "pre-launch" brand store', 'site:indiegogo.com/projects "shop" brand launch']
GEO = {"US": "United States", "INDIA": "India"}

def _build(r):
    d = dork.site_in(r["snippet"])
    t = r["title"].split(" by ")[0].split("|")[0].strip()
    if not d or not t: return None
    return t[:50], d, "Crowdfunding launch: " + r["title"][:120]

def fetch(deadline=None):
    out = []
    for c in config.countries():
        out += dork.run([f"{q} {GEO[c]}" for q in dork.pick(QUERIES, 2)], "Crowdfunding", "Launch", c, deadline, _build)
    return out
