"""Dual-lock gate for shared-server SMTP: atomic local counter + Sheet State + circuit breaker.
Stdlib-only core (dns optional) so the same file can be dropped on the shared verifier server."""
import os, json, time, random, threading, datetime
from core import safety_guard as sg

try: import fcntl
except ImportError: fcntl = None
BAD_450 = ("blocked", "spam", "blacklist", "reputation", "abuse")
LOCKED_429 = (429, {"error": "DAILY_SAFETY_LOCK_ACTIVE"})

def classify(code, text=""):
    """Circuit breaker: 554/Spamhaus -> lock 72h; 450 only when the text signals reputation."""
    t = (text or "").lower()
    if code == 554 or "spamhaus" in t: return True
    return code == 450 and any(w in t for w in BAD_450)

def mx_provider(domain, resolver=None):
    try:
        if resolver is None:
            import dns.resolver as resolver
        hosts = " ".join(str(r.exchange).lower() for r in resolver.resolve(domain, "MX", lifetime=5))
    except Exception:
        return "other"
    if "google" in hosts or "googlemail" in hosts: return "google"
    if "outlook" in hosts or "protection.outlook" in hosts or "microsoft" in hosts: return "microsoft"
    return "other"

class LocalStore:
    """Atomic JSON counter file (flock + tmp + os.replace)."""
    def __init__(self, path): self.path = path
    def update(self, fn):
        lock = open(self.path + ".lock", "a")
        try:
            if fcntl: fcntl.flock(lock, fcntl.LOCK_EX)
            try: st = json.load(open(self.path))
            except Exception: st = {}
            st = fn(st) or st
            tmp = f"{self.path}.{os.getpid()}.tmp"
            json.dump(st, open(tmp, "w")); os.replace(tmp, self.path)
            return st
        finally:
            lock.close()

def _roll(st, day, hour):
    if st.get("day") != day: st["day"], st["day_n"] = day, 0
    if st.get("hour") != hour: st["hour"], st["hour_n"], st["mx"] = hour, 0, {}
    return st

class SmtpGate:
    def __init__(self, cfg, state, store, on_flush=None, sleep=time.sleep, now=sg.utc_now):
        self.cfg, self.store, self.on_flush, self._sleep, self._now = cfg, store, on_flush, sleep, now
        self.lk, self.since_flush, self.used, self.blocked = threading.Lock(), 0, 0, False
        self.run_cap = cfg.SMTP_HOURLY_CAP
        # dual lock: take the larger of Sheet State and the local file
        def merge(loc):
            day, hour = self._day(), self._hour()
            for src in (state, loc):
                _roll(src, day, hour)
            for k in ("day_n", "hour_n"): loc[k] = max(loc.get(k, 0), state.get(k, 0))
            for p, n in state.get("mx", {}).items(): loc["mx"][p] = max(loc["mx"].get(p, 0), n)
            loc["lock_until"] = max(loc.get("lock_until", ""), state.get("lock_until", ""))
            if state.get("warmup_start"): loc.setdefault("warmup_start", state["warmup_start"])
            loc.setdefault("warmup_start", cfg.SMTP_WARMUP_START or day)
            return loc
        self.st = store.update(merge)

    def _day(self): return self._now().strftime("%Y-%m-%d")
    def _hour(self): return self._now().strftime("%Y-%m-%dT%H")

    def locked(self):
        return self.st.get("lock_until", "") > self._now().strftime("%Y-%m-%dT%H:%M:%S")

    def daily_cap(self):
        return sg.effective_daily_cap(self.cfg, self.st.get("warmup_start", ""))

    def check(self, provider="other"):
        """-> (allowed, reason). reason 'DAILY_SAFETY_LOCK_ACTIVE' maps to HTTP 429."""
        _roll(self.st, self._day(), self._hour())
        if self.blocked: return False, "DAILY_SAFETY_LOCK_ACTIVE"
        if self.locked(): return False, "CIRCUIT_BREAKER_LOCK"
        if self.st["day_n"] >= self.daily_cap(): return False, "DAILY_SAFETY_LOCK_ACTIVE"
        if self.st["hour_n"] >= min(self.cfg.SMTP_HOURLY_CAP, sg.CEILINGS["HOURLY"]): return False, "HOURLY_CAP"
        if provider in sg.PROVIDER_CAPPED and self.st["mx"].get(provider, 0) >= min(
                self.cfg.SMTP_MX_HOURLY_CAP, sg.CEILINGS["MX_HOURLY"]): return False, "MX_HOURLY_CAP"
        return True, ""

    def http_status(self):
        ok, why = self.check()
        return (200, {"ok": True}) if ok else (429, {"error": why})

    def acquire(self, provider, deadline=None):
        """Serialised: check, jitter, count. Returns True if the caller may do ONE SMTP check."""
        with self.lk:
            ok, _ = self.check(provider)
            if self.used >= getattr(self.cfg, "SMTP_RUN_CAP", 10 ** 9): ok = False   # per-run share of the daily cap
            wait = random.uniform(*self.cfg.SMTP_JITTER)
            if not ok or (deadline and time.time() + wait > deadline): return False
            self._sleep(wait)
            self.store.update(lambda s: self._count(s, provider))
            self._count(self.st, provider)
            self.used += 1; self.since_flush += 1
            if self.since_flush >= self.cfg.SMTP_FLUSH_EVERY: self.flush()
            return True

    def _count(self, st, provider):
        _roll(st, self._day(), self._hour())
        st["day_n"] += 1; st["hour_n"] += 1
        if provider in sg.PROVIDER_CAPPED: st["mx"][provider] = st["mx"].get(provider, 0) + 1

    def report(self, code, text=""):
        """Feed every SMTP reply back in; a reputation signal locks for 72h."""
        if not classify(code, text): return False
        until = (self._now() + datetime.timedelta(hours=sg.CEILINGS["LOCK_HOURS"])).strftime("%Y-%m-%dT%H:%M:%S")
        with self.lk:
            self.st["lock_until"] = until
            self.store.update(lambda s: s.update(lock_until=until))
            self.flush()
        return True

    def flush(self):
        self.since_flush = 0
        if self.on_flush:
            try: self.on_flush(self.st)
            except Exception: pass
