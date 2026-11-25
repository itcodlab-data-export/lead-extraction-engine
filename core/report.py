"""Run health in the Sheet: one Run_Log row per run + one Brain note per new code VERSION. Never raises (reporting must not break a run)."""
import datetime, time, collections
import config
from core import logger
from core.safety_guard import utc_now
log = logger.get()

RUN_COLS = ["Run_Time_IST", "Version", "Country", "Trigger", "Hiring_Signals", "Funding_Signals", "Shopify_Seeds", "Companies",
            "Sites_Audited", "People_Found", "Leads", "Hot", "Needs_SMTP", "Verified_Checks", "Verifier_Use", "Lead_Sources",
            "Errors", "Error_Detail", "Duration_Min", "Health", "Person_Leads", "Inbox_Leads", "Skipped_Seen"]
BRAIN_COLS = ["Date_IST", "Version", "Type", "Note"]

def ist_now():
    return (utc_now() + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M")

def health(errors, leads, hot):
    if errors: return "ERRORS - check logs"
    if not leads: return "OK - no new leads"
    return "GOOD" if hot else "OK - leads but none hot"

def run_row(m):
    """m: dict of run metrics -> list aligned to RUN_COLS."""
    srcs = " ".join(f"{k}={v}" for k, v in sorted(collections.Counter(m.get("signal_cats", [])).items()))
    vals = {"Run_Time_IST": ist_now(), "Version": config.VERSION, "Country": config.TARGET_COUNTRY, "Trigger": m.get("trigger", ""),
            "Hiring_Signals": m.get("hiring", 0), "Funding_Signals": m.get("funding", 0), "Shopify_Seeds": m.get("shopify", 0),
            "Companies": m.get("companies", 0), "Sites_Audited": m.get("audited", 0), "People_Found": m.get("people", 0),
            "Leads": m.get("leads", 0), "Hot": m.get("hot", 0), "Needs_SMTP": m.get("smtp", 0), "Verified_Checks": m.get("shared_smtp", 0),
            "Verifier_Use": "shared-smtp=" + str(m.get("shared_smtp", "skipped")) + f" batch_signals={m.get('batch', 0)}",
            "Lead_Sources": srcs, "Errors": m.get("errors", 0), "Error_Detail": m.get("error_detail", ""),
            "Duration_Min": round((time.time() - m.get("started", time.time())) / 60, 1),
            "Health": health(m.get("errors", 0), m.get("leads", 0), m.get("hot", 0)),
            "Person_Leads": "", "Inbox_Leads": "", "Skipped_Seen": m.get("rejected", 0)}
    return [vals[c] for c in RUN_COLS]

def write_run_log(sh, m):
    try: sh.append_aux("Run_Log", RUN_COLS, [run_row(m)])
    except Exception as e: log.warning("run_log write failed (%s)", type(e).__name__)

def brain_note(sh):
    """One line per new config.VERSION (code/rule update). Skipped when the last Brain row already has this version."""
    try:
        last = sh.last_aux_row("Brain", BRAIN_COLS)
        if last and len(last) > 1 and last[1] == config.VERSION: return
        sh.append_aux("Brain", BRAIN_COLS, [[ist_now(), config.VERSION, "Code update", config.BRAIN_NOTE]])
    except Exception as e: log.warning("brain note failed (%s)", type(e).__name__)
