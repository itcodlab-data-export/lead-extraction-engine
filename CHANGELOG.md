# CHANGELOG (APPEND-ONLY: add new entries at the bottom; CI fails if any existing line is edited or removed)
Entry format: `## YYYY-MM-DD <title>` then bullet lines. Changes to protected files need the literal tag APPROVED-BY-FAIZ (written only by Faiz) in the entry.

## 2026-11-20 Initial engine (commits abdfe60, f95be82, ce113fb)
- Extraction engine uploaded: sources (hiring, funding, shopify), pipeline, Sheet sync.

## 2026-11-21 Workflows (commits ee94563, 2748670, 137a5ab)
- run.yml then run2.yml (`run_leads2`) created and tuned.

## 2026-11-22 PR #1 SMTP safety + deep contacts + Batch1 (3a14518)
- core/safety_guard.py hard ceilings, core/smtp_gate.py dual-lock counter + circuit breaker, tests/test_safety_locks.py CI gate.
- Deep contact scraping (core/contacts.py), 5-API verify waterfall (core/apiverify.py), Batch1 sources (ats, shopify_reviews, producthunt).

## 2026-11-22 PR #2 Remove old run.yml (ba51292)
- run2.yml is the single production workflow.

## 2026-11-24 PR #3 website files merged by mistake, then removed (72934ab, f978b55)
- Website lives in repo itcodlab-web, not here.

## 2026-11-26 PR #4 scraping Batch2/3, 3-hour schedule, SMTP fix, repo memory system
- New sources: sources/dork.py (helper), social_dorks, launches, marketplaces, competitor_reviews, youtube (key-gated), registry sources/batch2.py; main.py runs batch1+batch2 sources in parallel under one cap; BATCH1_MAX_SIGNALS 30->60.
- Hiring: 12 queries rotating 3 per 3-hour slot (city rotation tried and reverted: returned 0 signals).
- run2.yml: cron 17 */3 * * * (8 runs/day), YOUTUBE_API_KEY env.
- SMTP: SMTP_RUN_CAP=8 per run (ceilings in safety_guard.py UNCHANGED); pipeline skips leads already in the Sheet before any verification; core/sheets_sync.py uses its own `smtp_state` key row in State tab (old row broke JSON parse and skipped SMTP every run).
- tests/test_safety_locks.py edited only to add run-cap and State-row tests and pass SMTP_RUN_CAP=99 inside the existing hourly/MX test; pinned ceilings untouched. tests/test_offline.py extended for new sources.
- Repo memory system added: CLAUDE.md, STATE.md, ARCHITECTURE.md, CHANGELOG.md, tests/test_repo_rules.py, tools/check_pr_rules.py, .github/workflows/ci.yml, .githooks/pre-commit, .claude/settings.json (SessionStart prints STATE.md).
- AWAITING FAIZ: approval tag line for protected-file changes (see STATE.md blocker 1).
