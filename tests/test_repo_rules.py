"""Repo memory + rule enforcement. Fails CI if the memory files drift from the code or protected rules are weakened."""
import sys, re, glob, os, subprocess
sys.path.insert(0, "."); sys.path.insert(0, "tools")
import config
from core import safety_guard as sg
import check_pr_rules as rules

def read(p): return open(p, encoding="utf-8").read()

def test_four_memory_files_exist_and_are_structured():
    for f, heads in {"CLAUDE.md": ["## Boot", "## Hard rules", "## Workflow"], "STATE.md": ["Last verified:", "## Open blockers", "## Exact next step"],
                     "ARCHITECTURE.md": ["## core/", "## sources/", "## Tests and enforcement"], "CHANGELOG.md": ["APPEND-ONLY"]}.items():
        t = read(f); assert len(t) > 400, f
        for h in heads: assert h in t, (f, h)
    assert len(read("CLAUDE.md").splitlines()) <= 60                       # concise by contract
    assert re.search(r"Last verified: \d{4}-\d\d-\d\d", read("STATE.md"))

def test_state_check_block_matches_code():
    blk = re.search(r"<!-- STATE-CHECK.*?-->", read("STATE.md"), re.S).group(0)
    ceil = dict(kv.split("=") for kv in re.search(r"ceilings: (.*)", blk).group(1).split())
    assert {k: int(v) for k, v in ceil.items()} == dict(sg.CEILINGS)
    wf = read(".github/workflows/run2.yml")
    assert re.findall(r'- cron: "([^"]+)"', wf) == [re.search(r"cron: (.*)", blk).group(1).strip()]
    assert int(re.search(r"run_cap: (\d+)", blk).group(1)) == config.SMTP_RUN_CAP

def test_architecture_names_every_module_and_workflow():
    arch = read("ARCHITECTURE.md")
    mods = [f.replace("\\", "/") for f in glob.glob("core/*.py") + glob.glob("sources/*.py") + glob.glob("tools/*.py") + glob.glob("tests/*.py")]
    mods += ["main.py", "config.py"] + sorted(glob.glob(".github/workflows/*.yml"))
    missing = [m for m in mods if os.path.basename(m) not in arch and not m.endswith("__init__.py")]
    assert not missing, f"document in ARCHITECTURE.md: {missing}"

def test_changelog_format_and_instructions():
    t = read("CHANGELOG.md"); entries = re.findall(r"^## (\d{4}-\d\d-\d\d) .+", t, re.M)
    assert len(entries) >= 5 and entries == sorted(entries)               # chronological, append at bottom

def test_claude_md_names_the_enforced_rules():
    t = read("CLAUDE.md")
    for k in ("safety_guard.py", "STATE.md", "CHANGELOG.md", "APPROVED-BY-FAIZ", "append-only", "check_pr_rules"): assert k in t, k

def test_ci_workflow_runs_tests_and_pr_rules():
    ci = read(".github/workflows/ci.yml")
    assert "pytest" in ci and "tools/check_pr_rules.py" in ci and "pull_request" in ci
    assert "tests/test_safety_locks.py" in read(".github/workflows/run2.yml")  # production gate must keep the safety tests

def test_no_secret_like_strings_in_repo():
    pat = re.compile(r"AIza[0-9A-Za-z_-]{30,}|ghp_[0-9A-Za-z]{30,}|github_pat_\w{30,}|sk-[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY|\"private_key\"\s*:")
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
    for f in files:
        if f.endswith((".py", ".md", ".yml", ".txt", ".json")) and os.path.isfile(f):
            assert not pat.search(read(f)), f

# ---- PR rule function ----
def test_rules_code_change_needs_state_and_changelog():
    assert rules.violations({"core/qc.py"}, {}, {})
    assert not rules.violations({"core/qc.py", "STATE.md", "CHANGELOG.md"}, {"CHANGELOG.md": ["x"]}, {"CHANGELOG.md": []})
    assert not rules.violations({"STATE.md"}, {}, {})                      # doc-only change is fine

def test_rules_changelog_append_only():
    assert any("append-only" in v for v in rules.violations({"CHANGELOG.md"}, {"CHANGELOG.md": ["a"]}, {"CHANGELOG.md": ["old line"]}))

def test_rules_protected_files_need_faiz_tag():
    ch = {"core/safety_guard.py", "STATE.md", "CHANGELOG.md"}
    assert any("APPROVED-BY-FAIZ" in v for v in rules.violations(ch, {"CHANGELOG.md": ["bump ceiling"]}, {"CHANGELOG.md": []}))
    assert any("APPROVED-BY-FAIZ" in v for v in rules.violations(ch, {"CHANGELOG.md": ["mentions APPROVED-BY-FAIZ in prose"]}, {"CHANGELOG.md": []}))
    assert not rules.violations(ch, {"CHANGELOG.md": ["APPROVED-BY-FAIZ: 2026-11-26 raise nothing, test fix"]}, {"CHANGELOG.md": []})
