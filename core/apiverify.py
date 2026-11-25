"""Free-tier verification waterfall (Reoon > Verifalia > ZeroBounce > AbstractAPI > Hunter).
Providers without a key are skipped. Result: valid | invalid | catch_all | unknown.
The shared-server SMTP is only a last resort for top P1 leads (see smtp_last_resort)."""
import os, re, threading
import config
from core import net, logger
log = logger.get()

def _j(r):
    try: return r.json() if r is not None and r.status_code == 200 else None
    except Exception: return None

def _map(s):
    s = (s or "").lower().replace("-", "_")
    if s in ("valid", "safe", "deliverable"): return "valid"
    if s in ("invalid", "undeliverable", "disposable", "spamtrap", "abuse", "do_not_mail"): return "invalid"
    if s in ("catch_all", "accept_all", "risky"): return "catch_all"
    return "unknown"

def reoon(e, k):
    d = _j(net.get("https://emailverifier.reoon.com/api/v1/verify", params={"email": e, "key": k, "mode": "quick"}, timeout=15))
    return _map(d.get("status")) if d else "unknown"

def verifalia(e, k):  # k = "user:pass" (sid:token)
    import requests
    try:
        u, _, p = k.partition(":")
        r = requests.post("https://api.verifalia.com/v2.4/email-validations?waitTime=20000", json={"entries": [{"inputData": e}]},
                          auth=(u, p), timeout=30)
        d = r.json() if r.status_code in (200, 202) else {}
        return _map(((d.get("entries") or {}).get("data") or [{}])[0].get("classification"))
    except Exception: return "unknown"

def zerobounce(e, k):
    d = _j(net.get("https://api.zerobounce.net/v2/validate", params={"api_key": k, "email": e}, timeout=15))
    return _map(d.get("status")) if d else "unknown"

def abstract(e, k):
    d = _j(net.get("https://emailvalidation.abstractapi.com/v1/", params={"api_key": k, "email": e}, timeout=15))
    if not d: return "unknown"
    if (d.get("is_catchall_email") or {}).get("value") is True: return "catch_all"
    return _map(d.get("deliverability"))

def hunter(e, k):
    d = _j(net.get("https://api.hunter.io/v2/email-verifier", params={"email": e, "api_key": k}, timeout=15))
    return _map(((d or {}).get("data") or {}).get("status")) if d else "unknown"

def _verifalia_key():
    u, p = os.getenv("VERIFALIA_USER"), os.getenv("VERIFALIA_PASS")
    return f"{u}:{p}" if u and p else ""

PROVIDERS = [("reoon", reoon, lambda: os.getenv("REOON_API_KEY")), ("verifalia", verifalia, _verifalia_key),
             ("zerobounce", zerobounce, lambda: os.getenv("ZEROBOUNCE_API_KEY")),
             ("abstract", abstract, lambda: os.getenv("ABSTRACT_API_KEY")), ("hunter", hunter, lambda: os.getenv("HUNTER_API_KEY"))]

_DATE = re.compile(r"^\d{4}-\d\d-\d\d$")

def row_from_values(v):
    """Sheet row [Domain, B, C, D] -> cache dict. Handles legacy v.8 rows (Domain, 'catch_all', date) and current rows (Domain, yes|no, pattern, date)."""
    v = list(v) + [""] * (4 - len(v))
    flag = {"catch_all": "yes", "yes": "yes", "no": "no"}.get(str(v[1]).strip().lower(), "")
    pat, on = (("", v[2]) if _DATE.match(str(v[2]).strip()) else (v[2], v[3]))
    return {"Domain": v[0], "Catch_All": flag, "Pattern": pat, "Updated_On": on}

class DomainCache:
    """Catch-all flag + verified pattern per domain, backed by the Domain_Cache tab."""
    def __init__(self, rows=None):
        self.d, self.new, self.lk = dict(rows or {}), [], threading.Lock()
    def get(self, dom): return self.d.get(dom, {})
    def put(self, dom, catch_all=None, pattern=None):
        from core.safety_guard import utc_today
        with self.lk:
            cur = {"Domain": dom, "Catch_All": "", "Pattern": "", "Updated_On": "", **self.d.get(dom, {})}   # missing keys never raise
            old = dict(cur)
            if catch_all is not None: cur["Catch_All"] = "yes" if catch_all else "no"
            if pattern: cur["Pattern"] = pattern
            if cur != old or dom not in self.d:
                cur["Updated_On"] = utc_today(); self.d[dom] = cur
                self.new.append([cur["Domain"], cur["Catch_All"], cur["Pattern"], cur["Updated_On"]])

def waterfall(email):
    """First definitive answer wins; providers without a key are skipped."""
    for name, fn, key in PROVIDERS:
        k = key()
        if not k: continue
        try: res = fn(email, k)
        except Exception as e:
            log.warning("verify %s failed (%s)", name, type(e).__name__); res = "unknown"
        if res != "unknown": return res
    return "unknown"

def check(email, domain, cache):
    """Cache-aware waterfall. Catch-all domains are never trusted as 'valid'."""
    if cache.get(domain).get("Catch_All") == "yes": return "catch_all"
    res = waterfall(email)
    if res == "catch_all": cache.put(domain, catch_all=True)
    elif res in ("valid", "invalid"): cache.put(domain, catch_all=False)
    return res

def smtp_last_resort(lead, gate, provider, deadline=None):
    """Shared-server SMTP: P1 decision-makers with Lead_Score >= SMTP_MIN_SCORE only, gated + fail-closed."""
    if gate is None or not config.SHARED_VERIFIER_URL: return "skipped"
    if int(lead["Lead_Score"] or 0) < config.SMTP_MIN_SCORE: return "skipped"
    if int(lead["Outreach_Priority"] or 99) > config.SMTP_MAX_PRIORITY: return "skipped"
    if not gate.acquire(provider, deadline): return "skipped"
    r = net.get(config.SHARED_VERIFIER_URL, params={"email": lead["Email"]},
                headers={"Authorization": "Bearer " + os.getenv("SHARED_VERIFIER_KEY", "")}, timeout=30)
    if r is None: return "unknown"
    if r.status_code == 429: gate.blocked = True; return "skipped"   # server says DAILY_SAFETY_LOCK_ACTIVE
    d = _j(r) or {}
    gate.report(int(d.get("code") or 0), str(d.get("message", "")))
    return "valid" if int(d.get("code") or 0) == 250 else "unknown"
