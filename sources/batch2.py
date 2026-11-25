"""Batch 2 + 3 registry (run by batch1.fetch under one combined time cap, each source isolated).
USPTO trademarks: not wired (needs a USPTO API key + verified endpoint). Meta Ad Library API: not usable (returns political ads only outside the EU);
the Meta Pixel/CAPI gap is already measured by core/auditor on every company."""
from sources import youtube, social_dorks, launches, marketplaces, competitor_reviews

SOURCES = (("youtube", youtube.fetch), ("social_dorks", social_dorks.fetch), ("launches", launches.fetch),
           ("marketplaces", marketplaces.fetch), ("competitor_reviews", competitor_reviews.fetch))
