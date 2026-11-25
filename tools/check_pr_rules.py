"""Non-bypassable PR gate (runs in CI and in the pre-commit hook). Pure rule function + thin git wrapper."""
import re, subprocess, sys

DOCS = {"STATE.md", "CHANGELOG.md"}
PROTECTED = ("core/safety_guard.py", "tests/test_safety_locks.py", "tests/test_repo_rules.py", "tools/check_pr_rules.py",
             ".github/workflows/ci.yml", ".githooks/pre-commit")
APPROVAL = "APPROVED-BY-FAIZ"
APPROVAL_LINE = re.compile(r"^APPROVED-BY-FAIZ: \d{4}-\d\d-\d\d \S.*")   # a whole line of its own, written by Faiz

def violations(changed, added, removed):
    """changed: set of paths; added/removed: {path: [lines]} for CHANGELOG.md. Returns a list of rule breaks."""
    out, work = [], {f for f in changed if f not in DOCS}
    if work:
        for d in sorted(DOCS - set(changed)):
            out.append(f"{d} must be updated in the same change (changed: {', '.join(sorted(work)[:5])})")
    if removed.get("CHANGELOG.md"):
        out.append("CHANGELOG.md is append-only: existing lines were edited or removed")
    hit = [f for f in changed if f in PROTECTED]
    if hit and not any(APPROVAL_LINE.match(l) for l in added.get("CHANGELOG.md", [])):
        out.append(f"protected files changed ({', '.join(hit)}) without a new CHANGELOG line `{APPROVAL}: YYYY-MM-DD <what was approved>`")
    return out

def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout

def collect(base=None):
    spec = ["--cached"] if base is None else [base + "...HEAD"]
    changed = set(_git("diff", "--name-only", *spec).split())
    added, removed = [], []
    for l in _git("diff", "-U0", *spec, "--", "CHANGELOG.md").splitlines():
        if l.startswith("+") and not l.startswith("+++"): added.append(l[1:])
        if l.startswith("-") and not l.startswith("---"): removed.append(l[1:])
    return changed, {"CHANGELOG.md": added}, {"CHANGELOG.md": removed}

def main(argv):
    base = None if "--staged" in argv else (argv[1] if len(argv) > 1 else "origin/main")
    bad = violations(*collect(base))
    for b in bad: print("RULE BREAK:", b)
    if bad: print("See CLAUDE.md. Commit/PR blocked."); return 1
    print("check_pr_rules: OK"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
