"""Single unified daily run: sources -> audit -> stakeholders -> dedup -> verify -> QC -> Sheets."""
import sys, config
from core import logger, alert, dedup, safety_guard, smtp_gate, apiverify
from core.pipeline import build_leads
from sources import hiring, funding, shopify, batch1
log = logger.get()

def _gate(sh):
    """Fail-closed: if today's counter cannot be read, shared-server SMTP is skipped (never assumed 0)."""
    try:
        state = sh.read_state()
        return smtp_gate.SmtpGate(config, state, smtp_gate.LocalStore(config.SMTP_STATE_FILE), sh.write_state)
    except Exception as e:
        log.warning("smtp state unreadable (%s) - shared-server SMTP skipped this run", type(e).__name__)
        return None

def main():
    try: safety_guard.preflight(config)
    except safety_guard.SafetyBlock: return 2
    errors, signals = 0, []
    for name, fn in (("hiring", hiring.fetch), ("funding", funding.fetch)):
        try: signals += fn()
        except Exception as e:
            errors += 1; log.error("source %s failed (%s)", name, type(e).__name__)
    try: signals += shopify.fetch(signals)
    except Exception as e:
        errors += 1; log.error("source shopify failed (%s)", type(e).__name__)
    try: b1 = batch1.fetch()
    except Exception as e:
        errors += 1; b1 = []; log.error("source batch1 failed (%s)", type(e).__name__)
    cap = config.MAX_COMPANIES_PER_RUN * 2
    signals = signals[:cap - len(b1)] + b1   # Batch-1 keeps its reserved slots
    from core.sheets_sync import Sheet
    sh = Sheet()
    dd = dedup.Dedup(sh.records("Master_Dedup_Index"), sh.records("Do_Not_Contact"))
    gate, cache = _gate(sh), apiverify.DomainCache(sh.read_domain_cache())
    leads, st = build_leads(signals, dd, gate, cache)
    if gate: gate.flush()
    try: sh.write_domain_cache(cache.new)
    except Exception as e: log.warning("domain cache write failed (%s)", type(e).__name__)
    hot = smtp = 0
    if leads: hot, smtp = sh.sync(leads)
    if sh.row_count("Raw_Leads") > config.ROTATION_ALERT_ROWS:
        alert.send("Raw_Leads crossed 15K rows - rotate the sheet")
    passed = sum(l["QC_Passed_And_Status"].startswith("YES") for l in leads)
    alert.send(f"{len(signals)} signals | {st['audited']} sites audited | {len(leads)} leads | "
               f"{passed} passed QC (hot {hot}, smtp {smtp}) | {errors} errors | "
               f"shared-smtp {gate.used if gate else 'skipped'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
