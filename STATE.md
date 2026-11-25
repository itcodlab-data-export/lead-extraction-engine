# STATE - live truth (update in EVERY PR; CI blocks code changes without this file)
Last verified: 2026-11-26
<!-- STATE-CHECK (machine-compared to code by tests/test_repo_rules.py; edit only together with the code)
ceilings: HOURLY=15 MX_HOURLY=6 JITTER_MIN_SEC=30 DAILY_ABSOLUTE=300 OPERATIONAL_DAILY=60 MIN_SCORE=75 LOCK_HOURS=72
cron: 17 */3 * * *
run_cap: 8
-->

## Where truth lives
- Code: GitHub `itcodlab-data-export/lead-extraction-engine`, branch `main`. Drive `code.zip` is OLD (v.8) - ignore.
- Data: Google Sheet "Lead Extraction Master" id `1xmng34DW_b-TqH5nG8bktCDo0f-yFoMdKWccGjohRy4` (Service Account `GOOGLE_SA_JSON`).
- Brain mirror (human-readable copy, written from chat only): Drive > Data Extraction > Brain/ (current_state.md, decisions.md, assets_map.md, README_LOAD_BRAIN.md). This repo's STATE.md wins on conflict.

## Production
- `main` = PR #4 merged 2026-11-26: workflow `run_leads2` every 3 hours (cron 17 */3 * * *, 8 runs/day), Batch1+2+3 sources, SMTP counter fix, SMTP_RUN_CAP=8, skip-known-leads-before-verify, hiring query rotation, repo memory + CI gate (`ci` job `gate`).
- PR "ops fixes" (this branch `ops-fixes-runlog-cleanup`): Domain_Cache legacy-row KeyError fix, Run_Log + Brain tab writing restored (core/report.py), unpack.yml + daily_leads.yml deleted, config.VERSION/BRAIN_NOTE. Supersedes docs-only PR #5 (close it).

## Workflows (.github/workflows)
- run2.yml `run_leads2` ACTIVE: tests gate -> `python main.py` -> keep-alive. timeout 30 min. dispatch input target_country BOTH|US|INDIA.
- ci.yml `ci` (job `gate`): full pytest on PR/push + tools/check_pr_rules.py on PR.
- Removed 2026-11-26: unpack.yml, daily_leads.yml.

## Latest real metrics (GitHub Actions logs)
- main scheduled runs 2026-11-24..25: ~70-77 signals, 25-36 sites audited, leads 1/5/1/0/2, hot 0, errors 0, every run logged "smtp state unreadable (JSONDecodeError)".
- PR #4 branch run 2026-11-25 22:08 UTC (id 45710567259): hiring 73, funding 0, shopify dork 0, shopify_reviews 1, ats 0, batch1+2+3 combined 37 signals (0 errors), 110 signals total, 53 audited, 8 leads, hot 0, smtp-queue 8, shared-smtp used 0, errors 0, no SMTP-counter warning.
- Sheet row counts last read 2026-11-22 (v.8-era data, not live): Raw_Leads 2056 rows, Hot_Leads_Ready 76, Needs_SMTP_Check 1500.

## Verification limits (never exceed; enforced by core/safety_guard.py + smtp_gate.py + CI pins)
Shared server SMTP: 60/day UTC, 15/hr, 5 per Google/Microsoft MX per hr (ceiling 6), 8/run, jitter 30-60s, Lead_Score>=75 and priority 1 only, 72h lock on 554/Spamhaus/reputation 450. Warm-up ceiling ramp 50/100/200/300 per day, operational cap 60. A request for 200 shared-server checks/day was REFUSED (2026-11-26); volume must come from free APIs.

## GitHub Secrets (evidence: env block of run logs; blank = missing)
- SET: `GOOGLE_SA_JSON`, `SHEET_ID`.
- MISSING (blank in the Extract step env): `SEC_CONTACT` (=> SEC requests carry "contact-not-set", very likely why funding=0), `API_KEYS`, `PRODUCTHUNT_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. `YOUTUBE_API_KEY` not set (youtube skipped in logs). `SHARED_VERIFIER_URL`/`SHARED_VERIFIER_KEY` are lines inside `API_KEYS` (also missing).
- `API_KEYS` format (one secret, multi-line NAME=value): REOON_API_KEY, VERIFALIA_USER, VERIFALIA_PASS, ZEROBOUNCE_API_KEY, ABSTRACT_API_KEY, HUNTER_API_KEY, SHARED_VERIFIER_URL, SHARED_VERIFIER_KEY.

## Open blockers / known issues
1. Branch protection on `main` (require check `gate`) NOT set: API proxy blocks Claude. Faiz: GitHub Settings > Branches.
2. Hot=0 until `API_KEYS` (+ shared verifier lines) are added; shared SMTP only runs when SHARED_VERIFIER_URL is set.
3. funding=0 (SEC_CONTACT missing), shopify dork=0 (DDG likely blocking runner), ats=0 on recent runs.
4. Not wired: USPTO trademarks (needs key + verified endpoint), Meta Ad Library API (political ads only outside EU), dashboard.
5. Legacy v.8 rows remain in `State` and `Domain_Cache` tabs on purpose (code ignores/tolerates them; never deleted automatically).
6. Fixed in the ops PR (verify after merge on the first scheduled run: Run_Log row appears, no `company failed (KeyError)`): KeyError root cause = DomainCache.put on legacy Domain_Cache rows without Catch_All/Pattern.

## Exact next step
Faiz: (1) merge the ops PR, close PR #5; (2) add GitHub secrets above (Settings > Secrets and variables > Actions > New repository secret); (3) Settings > Branches > rule for `main` requiring `gate`. Then Claude: read first scheduled Run_Log rows, confirm hot leads once `API_KEYS` exist.
