"""Batch 3d: businesses complaining in public reviews of competitor ad agencies/tools (AdKrity, Grexa AI, Clutch, Trustpilot) who name a site."""
import config
from sources import dork

COMPETITORS = ["AdKrity", "Grexa AI", "Grexa", "Clutch ads agency", "performance marketing agency"]

def _build(r):
    d = dork.site_in(r["snippet"])
    if not d: return None
    return d.split(".")[0].title(), d, "Unhappy with agency/tool: " + r["title"][:120]

def fetch(deadline=None):
    qs = [f'site:trustpilot.com "{c}" "1 star" my website' for c in dork.pick(COMPETITORS, 2)]
    out = []
    for c in config.countries():
        out += dork.run([f"{q} {'USA' if c == 'US' else 'India'}" for q in qs], "Competitor_Review", "Competitor_Complaint", c, deadline, _build)
    return out
