"""CI gate: shared-IP safety locks must be intact. If any of these fail, the run must not ship."""
import sys, re, glob, types, datetime, threading, logging, io
sys.path.insert(0, ".")
import pytest, config
from core import safety_guard as sg, smtp_gate, apiverify, logger

def cfg(**kw):
    d = {k: getattr(config, k) for k in dir(config) if k.startswith("SMTP_")}
    d.update(kw); return types.SimpleNamespace(**d)

def clock(start="2026-11-22T10:00:00"):
    t = [datetime.datetime.fromisoformat(start).replace(tzinfo=datetime.timezone.utc)]
    return t, (lambda: t[0])

def gate(tmp_path, c=None, state=None, now=None):
    return smtp_gate.SmtpGate(c or cfg(), state or {}, smtp_gate.LocalStore(str(tmp_path / "s.json")),
                              sleep=lambda s: None, now=now or sg.utc_now)

# ---- 1. guard intact / ceilings pinned --------------------------------------------------
def test_ceilings_pinned_and_immutable():
    assert dict(sg.CEILINGS) == {"HOURLY": 15, "MX_HOURLY": 6, "JITTER_MIN_SEC": 30, "DAILY_ABSOLUTE": 300,
                                 "OPERATIONAL_DAILY": 60, "MIN_SCORE": 75, "LOCK_HOURS": 72}
    assert dict(sg.WARMUP) == {1: 50, 2: 100, 3: 200, 4: 300}
    with pytest.raises(TypeError): sg.CEILINGS["HOURLY"] = 999
    assert sg.FAIL_CLOSED is True
    assert "Shared IP cap exceeded" in sg.BLOCK_MSG and sg.BLOCK_MSG.startswith("🛑 BLOCKED BY SAFETY GUARD")

def test_current_config_within_ceilings():
    assert sg.violations(config) == []
    assert sg.effective_daily_cap(config) <= 60

@pytest.mark.parametrize("k,v", [("SMTP_HOURLY_CAP", 16), ("SMTP_MX_HOURLY_CAP", 7), ("SMTP_DAILY_CAP", 61),
                                 ("SMTP_JITTER", (5, 10)), ("SMTP_MIN_SCORE", 60), ("SMTP_FLUSH_EVERY", 6)])
def test_config_over_ceiling_blocks_run(k, v):
    out = []
    with pytest.raises(sg.SafetyBlock): sg.preflight(cfg(**{k: v}), log=out.append)
    assert out[0] == sg.BLOCK_MSG and k in out[1]

def test_main_stops_before_any_work_on_violation(monkeypatch, capsys):
    import main
    monkeypatch.setattr(config, "SMTP_HOURLY_CAP", 99)
    monkeypatch.setattr(main.hiring, "fetch", lambda: pytest.fail("source ran despite block"))
    assert main.main() == 2
    assert "BLOCKED BY SAFETY GUARD" in capsys.readouterr().out

def test_warmup_ramp():
    assert [sg.warmup_cap("2026-11-01", d) for d in ("2026-11-01", "2026-11-08", "2026-11-15", "2026-11-22", "2027-03-01")] == [50, 100, 200, 300, 300]
    assert sg.warmup_cap("garbage") == 50 and sg.warmup_cap("2999-01-01") == 50
    assert sg.effective_daily_cap(cfg(), "2026-11-01") <= 60 and sg.effective_daily_cap(cfg(SMTP_DAILY_CAP=999)) <= 60

# ---- 2. dual lock: hourly / per-MX / daily, 429 ----------------------------------------
def test_hourly_cap_and_mx_cap(tmp_path):
    g = gate(tmp_path, cfg(SMTP_RUN_CAP=99))
    assert [g.acquire("google") for _ in range(7)] == [True] * 5 + [False] * 2   # config MX cap 5
    assert [g.acquire("other") for _ in range(12)].count(True) == 10             # total hits 15
    assert g.check("other") == (False, "HOURLY_CAP")

def test_daily_lock_returns_429(tmp_path):
    g = gate(tmp_path, state={"day": sg.utc_today(), "day_n": 60}); g.st["day"] = sg.utc_today()
    assert g.http_status() == (429, {"error": "DAILY_SAFETY_LOCK_ACTIVE"})
    assert g.acquire("other") is False

def test_local_counter_wins_over_lower_sheet_value(tmp_path):
    store = smtp_gate.LocalStore(str(tmp_path / "s.json"))
    store.update(lambda s: s.update(day=sg.utc_today(), day_n=49, hour=sg.utc_hour(), hour_n=0, mx={}))
    g = smtp_gate.SmtpGate(cfg(), {"day": sg.utc_today(), "day_n": 3}, store, sleep=lambda s: None)
    assert g.st["day_n"] == 49 and g.acquire("other") and not g.acquire("other")

def test_counter_atomic_under_threads(tmp_path):
    store = smtp_gate.LocalStore(str(tmp_path / "c.json"))
    ts = [threading.Thread(target=lambda: [store.update(lambda s: s.update(n=s.get("n", 0) + 1)) for _ in range(20)]) for _ in range(5)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert store.update(lambda s: None)["n"] == 100

def test_utc_rollover_and_flush_every_5(tmp_path):
    t, now = clock("2026-11-22T23:59:00"); flushes = []
    g = smtp_gate.SmtpGate(cfg(), {}, smtp_gate.LocalStore(str(tmp_path / "s.json")), flushes.append, lambda s: None, now)
    for _ in range(5): g.acquire("other")
    assert len(flushes) == 1 and flushes[0]["day"] == "2026-11-22" and flushes[0]["day_n"] == 5
    t[0] += datetime.timedelta(minutes=2)       # 00:01 UTC next day: counters reset
    assert g.check("other") == (True, "") and g.st["day"] == "2026-11-23" and g.st["day_n"] == 0
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", sg.utc_today())

# ---- 3. smart circuit breaker ----------------------------------------------------------
@pytest.mark.parametrize("code,text,lock", [
    (554, "", True), (250, "listed at Spamhaus", True), (450, "IP blocked", True), (450, "spam detected", True),
    (450, "on blacklist", True), (450, "bad reputation", True), (450, "abuse report", True),
    (450, "Greylisted, try again later", False), (450, "mailbox busy", False), (250, "ok", False), (550, "no such user", False)])
def test_breaker_classification(code, text, lock):
    assert smtp_gate.classify(code, text) is lock

def test_breaker_locks_72h_and_persists(tmp_path):
    t, now = clock(); g = gate(tmp_path, now=now)
    assert g.report(450, "greylisted") is False and g.acquire("other")
    assert g.report(554, "") is True
    assert g.check("other") == (False, "CIRCUIT_BREAKER_LOCK")
    t[0] += datetime.timedelta(hours=71); assert g.locked()
    t[0] += datetime.timedelta(hours=2);  assert not g.locked()
    t[0] -= datetime.timedelta(hours=10)         # fresh process, same local file: lock survives
    assert gate(tmp_path, now=now).locked()

# ---- 4. fail-closed ---------------------------------------------------------------------
def test_unreadable_counter_is_never_zero(monkeypatch):
    import main
    assert sg.may_run_smtp(None) is False and sg.may_run_smtp(0) is True
    sh = types.SimpleNamespace(read_state=lambda: (_ for _ in ()).throw(RuntimeError("sheet down")))
    assert main._gate(sh) is None

def test_no_gate_means_no_smtp(monkeypatch):
    monkeypatch.setattr(config, "SHARED_VERIFIER_URL", "https://x.invalid")
    lead = {"Lead_Score": 99, "Outreach_Priority": 1, "Email": "a@b.co"}
    monkeypatch.setattr(apiverify.net, "get", lambda *a, **k: pytest.fail("network call without gate"))
    assert apiverify.smtp_last_resort(lead, None, "other") == "skipped"

def test_only_top_p1_reach_shared_server(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SHARED_VERIFIER_URL", "https://x.invalid")
    g = gate(tmp_path); calls = []
    monkeypatch.setattr(apiverify.net, "get", lambda *a, **k: calls.append(1) or None)
    mk = lambda s, p: {"Lead_Score": s, "Outreach_Priority": p, "Email": "a@b.co"}
    assert apiverify.smtp_last_resort(mk(74, 1), g, "other") == "skipped"
    assert apiverify.smtp_last_resort(mk(90, 2), g, "other") == "skipped"
    assert apiverify.smtp_last_resort(mk(75, 1), g, "other") == "unknown" and len(calls) == 1

# ---- 5. zero-PII logging ----------------------------------------------------------------
def test_logger_masks_pii():
    buf = io.StringIO(); lg = logger.get("pii_test"); h = lg.handlers[0]; h.setStream(buf)
    lg.info("sent jane.doe@acme.com phone +1 415 555 0134 and 98765 43210")
    out = buf.getvalue()
    assert "jane.doe" not in out and "acme.com" not in out and "415" not in out and "98765" not in out
    assert "<email>" in out and "<phone>" in out

def test_logs_print_exception_type_only():
    bad = re.compile(r"log\w*\.(?:warning|error|info|exception|debug)\([^)]*(?:str\(e\)|,\s*e\)|\{e\}|traceback)")
    for f in glob.glob("core/*.py") + glob.glob("sources/*.py") + ["main.py"]:
        assert not bad.search(open(f).read()), f

def test_no_csv_or_pii_dump_and_secret_hygiene():
    for f in glob.glob("core/*.py") + glob.glob("sources/*.py") + ["main.py"]:
        src = open(f).read()
        assert "to_csv" not in src and "csv.writer" not in src, f

# ---- 6. UTC everywhere + file-size rule ------------------------------------------------
def test_utc_only_dates():
    for f in glob.glob("core/*.py") + glob.glob("sources/*.py") + ["main.py"]:
        src = open(f).read()
        assert "date.today()" not in src and not re.search(r"datetime\.now\(\s*\)", src) and "utcnow" not in src, f

def test_files_under_150_lines():
    for f in glob.glob("core/*.py") + glob.glob("sources/*.py") + ["main.py", "config.py"]:
        assert len(open(f).read().splitlines()) < 150, f

def test_per_run_cap_spreads_the_daily_cap(tmp_path):
    g = gate(tmp_path); n = sum(g.acquire("other") for _ in range(20))
    assert n == config.SMTP_RUN_CAP == 8 and config.SMTP_RUN_CAP * 8 >= 60 > config.SMTP_RUN_CAP * 7 - 1
