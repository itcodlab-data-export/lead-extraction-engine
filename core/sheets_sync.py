"""Crash-safe Google Sheets sync."""
import os, json, time
import gspread
import config
from core import models, logger, apiverify
from core.safety_guard import utc_today
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

DC_COLS = ["Domain", "Catch_All", "Pattern", "Updated_On"]

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
        today = utc_today()
        from core import dedup
        self.append("Master_Dedup_Index", [[l["Person_Fingerprint"], dedup.norm_email(l["Email"]),
                    dedup.li_slug(l["LinkedIn_URL"]), l["Website_Domain"], today] for l in leads])
        self.append("Raw_Leads", [models.row(l) for l in leads])
        hot = [models.row(l) for l in leads if l["QC_Passed_And_Status"].startswith("YES") and l["Email_Status"] != "Permutated_Unverified"]
        smtp = [models.row(l) for l in leads if l["QC_Passed_And_Status"].startswith("YES") and l["Email_Status"] == "Permutated_Unverified"]
        self.append("Hot_Leads_Ready", hot)
        self.append("Needs_SMTP_Check", smtp)
        return len(hot), len(smtp)

    # --- auxiliary tabs (not part of the 5 lead tabs): State + Domain_Cache ---
    def _aux(self, name, head):
        try: ws = self.sh.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            ws = _retry(self.sh.add_worksheet, title=name, rows=1000, cols=len(head))
            _retry(ws.update, values=[head], range_name="A1", value_input_option="RAW")
        return ws

    def _state_row(self, ws):
        """(row number, value) of the 'smtp_state' key in State!A:B; other keys (old Updated_IST etc.) are never touched."""
        for i, r in enumerate(_retry(ws.get, "A1:B200"), 1):
            if r and r[0] == "smtp_state": return i, (r[1] if len(r) > 1 else "")
        return 0, ""

    def read_state(self):
        """SMTP counter dict ({} = never used). RAISES on any read/parse failure -> caller fails closed."""
        _, val = self._state_row(self._aux("State", ["Key", "Value"]))
        return json.loads(val) if val else {}

    def write_state(self, st):
        ws = self._aux("State", ["Key", "Value"])
        i, _ = self._state_row(ws)
        if i: _retry(ws.update, values=[["smtp_state", json.dumps(st)]], range_name=f"A{i}", value_input_option="RAW")
        else: _retry(ws.append_rows, [["smtp_state", json.dumps(st)]], value_input_option="RAW")

    def read_domain_cache(self):
        """Positional read (legacy v.8 header Domain/Result/Checked_On is tolerated): {domain: row dict}."""
        try:
            rows = _retry(self._aux("Domain_Cache", DC_COLS).get_all_values)[1:]
            return {r[0]: apiverify.row_from_values(r) for r in rows if r and r[0]}
        except Exception as e:
            log.warning("domain cache unavailable (%s)", type(e).__name__); return {}

    def append_aux(self, tab, head, rows):
        _retry(self._aux(tab, head).append_rows, [[_trim(c) for c in r] for r in rows], value_input_option="RAW")

    def last_aux_row(self, tab, head):
        vals = _retry(self._aux(tab, head).get_all_values)
        return vals[-1] if len(vals) > 1 else None

    def write_domain_cache(self, rows):
        if rows: _retry(self._aux("Domain_Cache", DC_COLS).append_rows, rows, value_input_option="RAW")
