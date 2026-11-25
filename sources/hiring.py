"""Source 1: hiring signals via python-jobspy (Meta Ads / Performance / Shopify jobs)."""
import config
from sources.dork import pick as dork_pick
from core import logger
log = logger.get()

def fetch():
    try:
        from jobspy import scrape_jobs
    except Exception as e:
        log.warning("hiring: jobspy missing (%s)", type(e).__name__); return []
    out = []
    for c in config.countries():
        city = dork_pick(config.JOB_CITIES[c], 1)[0]
        for q in dork_pick(config.JOB_QUERIES, config.JOB_QUERIES_PER_RUN):
            try:
                df = scrape_jobs(site_name=["indeed"], search_term=q,
                                 location=city, results_wanted=15,
                                 hours_old=72, country_indeed="USA" if c == "US" else "India")
            except Exception as e:
                log.warning("hiring: %s/%s failed (%s)", c, q, type(e).__name__); continue
            for _, r in df.iterrows():
                name = str(r.get("company") or "").strip()
                if not name or name == "nan":
                    continue
                out.append({
                    "company": name, "country": c, "source_platform": str(r.get("site", "jobspy")),
                    "signal": "Hiring", "source_url": str(r.get("job_url", "")),
                    "evidence": f"Hiring: {str(r.get('title',''))[:120]} ({q})",
                    "domain_hint": _host(r.get("company_url")), "people": [],
                })
    log.info("hiring: %d signals", len(out))
    return out

def _host(u):
    from urllib.parse import urlparse
    try:
        return urlparse(str(u)).netloc.replace("www.", "") if u and str(u) != "nan" else ""
    except Exception:
        return ""
