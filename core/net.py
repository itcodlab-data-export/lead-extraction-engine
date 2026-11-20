"""Tiny HTTP helper: one session, timeouts, never raises."""
import requests, time, random
import config

_S = requests.Session()
_S.headers.update({"User-Agent": config.BROWSER_UA, "Accept-Language": "en"})

def get(url, headers=None, timeout=None, **kw):
    try:
        return _S.get(url, headers=headers, timeout=timeout or config.HTTP_TIMEOUT,
                      allow_redirects=True, **kw)
    except Exception:
        return None

def text(url, **kw):
    r = get(url, **kw)
    return r.text if r is not None and r.status_code == 200 else ""

def jitter(lo_hi):
    time.sleep(random.uniform(*lo_hi))
