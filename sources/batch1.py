"""Run the 3 Batch-1 sources in parallel under ONE combined time cap; each is isolated (try/except)."""
import time, threading
import config
from core import logger
from sources import ats, shopify_reviews, producthunt
log = logger.get()

SOURCES = (("ats", ats.fetch), ("shopify_reviews", shopify_reviews.fetch), ("producthunt", producthunt.fetch))

def fetch(budget=None, sources=SOURCES):
    budget = config.BATCH1_BUDGET_SEC if budget is None else budget
    deadline = time.time() + budget
    results, errors = {}, [0]
    def run(name, fn):
        try: results[name] = fn(deadline=deadline)
        except Exception as e:
            errors[0] += 1; log.error("source %s failed (%s)", name, type(e).__name__)
    threads = [threading.Thread(target=run, args=s, daemon=True) for s in sources]   # daemon: never blocks exit
    for t in threads: t.start()
    for t in threads: t.join(max(0, deadline - time.time()))
    for (name, _), t in zip(sources, threads):
        if t.is_alive(): log.warning("source %s hit the combined time cap, abandoned", name)
    out = [s for name, _ in sources for s in list(results.get(name, []))]
    log.info("batch1: %d signals (%d errors)", len(out), errors[0])
    return out[:config.BATCH1_MAX_SIGNALS]
