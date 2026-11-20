"""Single unified daily run: sources -> audit -> stakeholders -> dedup -> verify -> QC -> Sheets."""
import sys, config
from core import logger, alert, dedup
from core.pipeline import build_leads
from sources import hiring, funding, shopify
log = logger.get()

def main():
    errors, signals = 0, []
    for name, fn in (("hiring", hiring.fetch), ("funding", funding.fetch)):
        try: signals += fn()
        except Exception as e:
            errors += 1; log.error("source %s failed (%s)", name, type(e).__name__)
    try: signals += shopify.fetch(signals)
    except Exception as e:
        errors += 1; log.error("source shopify failed (%s)", type(e).__name__)
    signals = signals[:config.MAX_COMPANIES_PER_RUN * 2]
    from core.sheets_sync import Sheet
    sh = Sheet()
    dd = dedup.Dedup(sh.records("Master_Dedup_Index"), sh.records("Do_Not_Contact"))
    leads, st = build_leads(signals[:config.MAX_COMPANIES_PER_RUN * 2], dd)
    hot = smtp = 0
    if leads: hot, smtp = sh.sync(leads)
    if sh.row_count("Raw_Leads") > config.ROTATION_ALERT_ROWS:
        alert.send("Raw_Leads crossed 15K rows - rotate the sheet")
    passed = sum(l["QC_Passed_And_Status"].startswith("YES") for l in leads)
    alert.send(f"{len(signals)} signals | {st['audited']} sites audited | {len(leads)} leads | "
               f"{passed} passed QC (hot {hot}, smtp {smtp}) | {errors} errors")
    return 0

if __name__ == "__main__":
    sys.exit(main())
