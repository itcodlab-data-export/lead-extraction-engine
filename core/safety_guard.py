"""Immutable hard ceilings for the shared-server SMTP verifier (protects the shared IP).

config.py may be stricter than these values, never looser. Changing a ceiling here
also breaks tests/test_safety_locks.py, which pins them (CI gate)."""
import datetime
from types import MappingProxyType

CEILINGS = MappingProxyType({
    "HOURLY": 15,             # total SMTP checks per UTC hour
    "MX_HOURLY": 6,           # per Google / Microsoft MX provider per UTC hour
    "JITTER_MIN_SEC": 30,     # config jitter may not go below this
    "DAILY_ABSOLUTE": 300,    # week-4 ceiling, never exceeded
    "OPERATIONAL_DAILY": 60,  # current safe cap across 4 runs/day
    "MIN_SCORE": 75,          # shared server = top P1 only
    "LOCK_HOURS": 72,
})
WARMUP = MappingProxyType({1: 50, 2: 100, 3: 200, 4: 300})  # week -> per-day cap
BLOCK_MSG = ("🛑 BLOCKED BY SAFETY GUARD: Shared IP cap exceeded — protects shared "
             "hosting IP from Spamhaus/421 blacklist.")
FAIL_CLOSED = True        # unreadable counter => skip SMTP, never assume 0
PROVIDER_CAPPED = ("google", "microsoft")

class SafetyBlock(Exception):
    pass

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

def utc_today():
    return utc_now().strftime("%Y-%m-%d")

def utc_hour():
    return utc_now().strftime("%Y-%m-%dT%H")

def warmup_cap(start, today=None):
    """Per-day ceiling for the warm-up week (week 4+ = 300). Bad/future start = week 1."""
    try:
        d0 = datetime.date.fromisoformat(start)
        d1 = datetime.date.fromisoformat(today or utc_today())
        week = max(1, (d1 - d0).days // 7 + 1)
    except Exception:
        week = 1
    return WARMUP[min(week, 4)]

def effective_daily_cap(cfg, start=""):
    return min(cfg.SMTP_DAILY_CAP, CEILINGS["OPERATIONAL_DAILY"],
               CEILINGS["DAILY_ABSOLUTE"], warmup_cap(start or cfg.SMTP_WARMUP_START))

def violations(cfg):
    c, v = CEILINGS, []
    chk = [(cfg.SMTP_HOURLY_CAP <= c["HOURLY"], "SMTP_HOURLY_CAP"),
           (cfg.SMTP_MX_HOURLY_CAP <= c["MX_HOURLY"], "SMTP_MX_HOURLY_CAP"),
           (cfg.SMTP_DAILY_CAP <= c["OPERATIONAL_DAILY"], "SMTP_DAILY_CAP"),
           (min(cfg.SMTP_JITTER) >= c["JITTER_MIN_SEC"], "SMTP_JITTER"),
           (cfg.SMTP_MIN_SCORE >= c["MIN_SCORE"], "SMTP_MIN_SCORE"),
           (cfg.SMTP_FLUSH_EVERY <= 5, "SMTP_FLUSH_EVERY")]
    for ok, name in chk:
        if not ok:
            v.append(name)
    return v

def preflight(cfg, log=print):
    """Call before any work. Raises SafetyBlock (after printing the reason) on a violation."""
    bad = violations(cfg)
    if bad:
        log(BLOCK_MSG)
        log("Violated settings: " + ", ".join(bad))
        raise SafetyBlock(BLOCK_MSG)
    return True

def may_run_smtp(day_count):
    """Fail-closed: an unreadable counter (None) is never treated as 0."""
    return day_count is not None
