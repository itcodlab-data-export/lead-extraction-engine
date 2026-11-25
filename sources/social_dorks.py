"""Batch 3a: people asking for Meta Ads / Pixel help on Reddit, X and LinkedIn (via dorks) who name their own store domain."""
import re, config
from sources import dork

SITES = {"reddit.com": "Reddit", "x.com": "X", "linkedin.com/posts": "LinkedIn"}
ASKS = ['"meta pixel" "not working" shopify', '"conversions api" help store', '"facebook ads" "no sales" my store',
        '"need a meta ads" manager store', '"iOS 14" tracking broken store', '"capi" "events manager" error', '"ROAS dropped" facebook ads store',
        '"hire" "performance marketer" shopify store', '"looking for" "ads agency" ecommerce']
GEO = {"US": "USA", "INDIA": "India"}

def _build(r):
    d = dork.site_in(r["snippet"] + " " + r["title"])
    if not d: return None
    return d.split(".")[0].title(), d, "Asked for ad/tracking help: " + r["title"][:120]

def fetch(deadline=None):
    out = []
    for c in config.countries():
        qs = [f'site:{s} {a} {GEO[c]}' for s in SITES for a in dork.pick(ASKS, 2)]
        out += dork.run(qs, "Social_Dork", "Help_Request", c, deadline, _build)
    return out
