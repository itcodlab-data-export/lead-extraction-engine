"""Batch 3c: Flippa / Acquire.com / Amazon-seller listings that show a store domain (owners selling or scaling a store)."""
import config
from sources import dork

QUERIES = ['site:flippa.com "shopify" store for sale', 'site:acquire.com "ecommerce" "Facebook ads"',
           'site:flippa.com "dropshipping" "Meta ads"', 'site:acquire.com "D2C" brand', '"amazon seller" "own website" brand ads help']
GEO = {"US": "USA", "INDIA": "India"}

def _build(r):
    d = dork.site_in(r["snippet"] + " " + r["title"])
    if not d: return None
    return d.split(".")[0].title(), d, "Store listed/selling: " + r["title"][:120]

def fetch(deadline=None):
    out = []
    for c in config.countries():
        out += dork.run([f"{q} {GEO[c]}" for q in dork.pick(QUERIES, 2)], "Marketplace", "Store_Listing", c, deadline, _build)
    return out
