"""Batch 2a: YouTube 'help me' videos about Meta Ads/Pixel; channel description site -> company. Skips cleanly without YOUTUBE_API_KEY."""
import os, time
import requests, config
from core import logger
from sources import dork
log = logger.get()

API = "https://www.googleapis.com/youtube/v3"
QUERIES = ["meta pixel not working shopify help", "facebook ads not converting my store help", "conversions api setup shopify problem",
           "iOS tracking facebook ads broken ecommerce", "meta ads account disabled help store owner"]
REGION = {"US": "US", "INDIA": "IN"}

def fetch(deadline=None):
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        log.info("youtube: YOUTUBE_API_KEY not set, skipped"); return []
    out, seen = [], set()
    for c in config.countries():
        for q in dork.pick(QUERIES, 2):
            if deadline and time.time() > deadline: return out
            r = requests.get(f"{API}/search", params={"part": "snippet", "type": "video", "q": q, "maxResults": 10, "regionCode": REGION[c],
                             "order": "date", "key": key}, timeout=config.HTTP_TIMEOUT)
            items = r.json().get("items", []) if r.status_code == 200 else []
            ids = list({i["snippet"]["channelId"] for i in items})
            if not ids: continue
            ch = requests.get(f"{API}/channels", params={"part": "snippet", "id": ",".join(ids), "key": key}, timeout=config.HTTP_TIMEOUT)
            for it in (ch.json().get("items", []) if ch.status_code == 200 else []):
                sn = it["snippet"]; d = dork.site_in(sn.get("description", ""))
                if d and sn["title"].lower() not in seen:
                    seen.add(sn["title"].lower())
                    out.append(dork.signal(sn["title"], c, "YouTube", "Help_Request", f"https://www.youtube.com/channel/{it['id']}",
                                           f"Posts about Meta Ads/tracking: {q}", d))
    log.info("youtube: %d signals", len(out))
    return out
