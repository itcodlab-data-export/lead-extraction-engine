"""Crash-safe Google Sheets sync."""
import os, json, time, datetime
import gspread
import config
from core import models, logger
log = logger.get()

def _client():
    info = json.loads(os.environ["GOOGLE_SA_JSON"])
    return gspread.service_account_from_dict(info)

def _retry(fn, *a, **kw):
    for wait in (1, 2, 4, 8, 16):
        try: return fn(*a, **kw)
        except gspread.exceptions.APIError as e:
            if "429" in str(e) or "5" == str(getattr(e.response, "status_code", ""))[:1]:
                time.sleep(wait); continue
            raise
    return fn(*a, **kw)

def _trim(v):
    return str(v)[:config.CELL_MAX_CHARS]

class Sheet:
    def __init__(self):
        self.sh = _retry(_client().open_by_key, config.SHEET_ID)
        self.ensure_tabs_exist()

    def ensure_tabs_exist(self):
        have = {w.title: w for w in self.sh.worksheets()}
        heads = {"Master_Dedup_Index": models.DEDUP_COLS, "Do_Not_Contact": models.DNC_COLS}
        for t in models.TABS:
            if t not in have:
                have[t] = _retry(self.sh.add_worksheet, title=t, rows=1000, cols=26)
            ws = have[t]
            h = heads.get(t, models.COLUMNS)
            if not _retry(ws.row_values, 1):
                _retry(ws.update, values=[h], range_name="A1", value_input_option="RAW")
        self.ws = have

    def records(self, tab):
        return _retry(self.ws[tab].get_all_records)

    def row_count(self, tab):
        return len(_retry(self.ws[tab].col_values, 1))

    def append(self, tab, rows):
        rows = [[_trim(c) for c in r] for r in rows]
        for i in range(0, len(rows), config.SHEET_CHUNK):
            _retry(self.ws[tab].append_rows, rows[i:i + config.SHEET_CHUNK],
                   value_input_option="RAW")

    def sync(self, leads):
        """Master_Dedup_Index first, so a crash never causes duplicates next run."""
        today = datetime.date.today().isoformat()
        from core import dedup
        self.append("Master_Dedup_Index", [[l["Person_Fingerprint"], dedup.norm_email(l["Email"]),
                    dedup.li_slug(l["LinkedIn_URL"]), l["Website_Domain"], today] for l in leads])
        self.append("Raw_Leads", [models.row(l) for l in leads])
        hot = [models.row(l) for l in leads if l["QC_Passed_And_Status"].startswith("YES") and l["Email_Status"] != "Permutated_Unverified"]
        smtp = [models.row(l) for l in leads if l["QC_Passed_And_Status"].startswith("YES") and l["Email_Status"] == "Permutated_Unverified"]
        self.append("Hot_Leads_Ready", hot)
        self.append("Needs_SMTP_Check", smtp)
        return len(hot), len(smtp)
