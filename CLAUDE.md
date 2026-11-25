# Data Extraction Engine - RULES (auto-loaded; read STATE.md next, ARCHITECTURE.md only if you touch code)
Extraction-only lead engine (GitHub Actions -> Google Sheet). No sending, no copywriting. Owner: Faiz (short Hinglish, answer first, plain text questions, no widgets).

## Boot (every new chat, in this order, nothing else)
1. Read STATE.md (live truth, blockers, next step). 2. Read tail of CHANGELOG.md. 3. ARCHITECTURE.md only for code work. Never rely on chat history/summaries.

## Hard rules (enforced by CI: tests/ + tools/check_pr_rules.py + .github/workflows/ci.yml)
- Verification ceilings live ONLY in core/safety_guard.py (pinned by tests/test_safety_locks.py). Never raise, bypass or pin-edit them. Changing safety_guard.py / test_safety_locks.py / tools/ / ci.yml needs a new CHANGELOG line `APPROVED-BY-FAIZ: YYYY-MM-DD <what>`. ONLY Faiz writes that line; Claude must NEVER add it itself.
- Shared-server SMTP: 60/day, 15/hr, 5-6/hr per MX provider, 8/run, jitter 30-60s, only Lead_Score>=75 P1. Counter unreadable => skip SMTP (fail-closed). Never run bulk SMTP on shared hosting beyond this. Never put role inboxes in hot.
- Every code/workflow/config/test change MUST also update STATE.md and append to CHANGELOG.md (append-only, never edit old lines). New module => document it in ARCHITECTURE.md (test fails otherwise).
- Files < 150 lines, one job each. Settings only in config.py. UTC dates only. One source failing never stops a run (try/except).
- Never log emails/phones/names (core/logger.py masks). No CSV artifacts. No secrets in repo (only GitHub Secrets; test scans for key patterns).
- Do not touch other sites' files; this repo is only the extraction engine (website lives in itcodlab-web).

## Workflow
- Work on a branch, push, open PR via REST (`gh api repos/<o>/<r>/pulls`). Claude cannot merge PRs; Faiz merges. Dispatching run2.yml only when Faiz says "run".
- Run `python -m pytest -q tests` and `python tools/check_pr_rules.py origin/main` before every push. Enable local hook once: `git config core.hooksPath .githooks`.
- Heavy coding on Sonnet or higher. Do only what Faiz asked. Once approved, never re-ask the same approval.
- End of work: update STATE.md + CHANGELOG.md in the same PR (and the Drive Brain mirror if present).
