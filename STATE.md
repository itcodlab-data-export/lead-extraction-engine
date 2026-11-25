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

## Production vs PR #4
- `main` TODAY (before PR #4 merge): workflow `run_leads2`, 4 runs/day (cron 30 0,6,12,18 UTC), old SMTP-counter bug => shared-server SMTP skipped every run, Hot=0. Sources: hiring, funding, shopify dork, batch1.
- PR #4 (branch `scraping-batch2-3-3h-schedule`, NOT merged; Faiz must click Merge): cron `17 */3 * * *` (8/day), Batch2/3 sources, SMTP counter fix, SMTP_RUN_CAP=8, skip-known-leads-before-verify, hiring query rotation, repo memory system (this file set) + CI gate. After merge, the STATE-CHECK block above is true on main.

## Workflows (.github/workflows)
- run2.yml `run_leads2` ACTIVE: tests gate -> `python main.py` -> keep-alive. timeout 30 min. dispatch input target_country BOTH|US|INDIA.
- ci.yml `ci` (new in PR #4): full pytest on PR/push + tools/check_pr_rules.py on PR.
- daily_leads.yml DISABLED (legacy, safe to delete later). unpack.yml active but obsolete (unzips code.zip into repo) - candidate for removal.

## Latest real metrics (GitHub Actions logs)
- main scheduled runs 2026-11-24..25: ~70-77 signals, 25-36 sites audited, leads 1/5/1/0/2, hot 0, errors 0, every run logged "smtp state unreadable (JSONDecodeError)".
- PR #4 branch run 2026-11-25 22:08 UTC (id 45710567259): hiring 73, funding 0, shopify dork 0, shopify_reviews 1, ats 0, batch1+2+3 combined 37 signals (0 errors), 110 signals total, 53 audited, 8 leads, hot 0, smtp-queue 8, shared-smtp used 0, errors 0, no SMTP-counter warning.
- Sheet row counts last read 2026-11-22 (v.8-era data, not live): Raw_Leads 2056 rows, Hot_Leads_Ready 76, Needs_SMTP_Check 1500.

## Verification limits (never exceed; enforced by core/safety_guard.py + smtp_gate.py + CI pins)
Shared server SMTP: 60/day UTC, 15/hr, 5 per Google/Microsoft MX per hr (ceiling 6), 8/run, jitter 30-60s, Lead_Score>=75 and priority 1 only, 72h lock on 554/Spamhaus/reputation 450. Warm-up ceiling ramp 50/100/200/300 per day, operational cap 60. A request for 200 shared-server checks/day was REFUSED (2026-11-26); volume must come from free APIs.

## Open blockers / known issues
1. PR #4 unmerged (Claude is blocked from merging) AND needs Faiz to add the line `APPROVED-BY-FAIZ` under the PR #4 entry in CHANGELOG.md (it changes protected files: safety test file, tools/, ci.yml). CI `ci` will fail until he does; this is by design.
2. Hot=0: unknown whether GitHub Secrets `API_KEYS` (Reoon/Verifalia/ZeroBounce/Abstract/Hunter) and `SHARED_VERIFIER_URL`/`SHARED_VERIFIER_KEY` exist (Claude cannot read secrets). `PRODUCTHUNT_TOKEN`, `YOUTUBE_API_KEY` not set (sources skip).
3. funding=0 and shopify dork=0 on every recent run (also on main); ats=0. Cause unknown (feeds empty at night / DDG blocking runner IP).
4. Intermittent `company failed (KeyError)` in one company worker per run (not yet traced).
5. Sheet `Domain_Cache` tab has a legacy header (Domain, Result, Checked_On) from v.8; code now writes Domain, Catch_All, Pattern, Updated_On. Needs header reset by owner or code fix.
6. `State` tab still holds legacy v.8 rows (Updated_IST...); code uses its own `smtp_state` row. Run_Log / Brain / Context_Notes tabs are no longer written.
7. Not wired: USPTO trademarks (needs key + verified endpoint), Meta Ad Library API (political ads only outside EU), dashboard.
8. Branch protection requiring the `ci` check is a GitHub setting only Faiz can enable (see Next step).

## Exact next step
Faiz: (1) add `APPROVED-BY-FAIZ` line to the PR #4 CHANGELOG entry (edit file on the PR branch in GitHub web editor) and merge PR #4; (2) GitHub Settings > Branches > Add rule for `main` > "Require status checks to pass" > select `gate` (job of workflow `ci`) so rules cannot be bypassed; (3) check Settings > Secrets and variables > Actions for `API_KEYS`, `SHARED_VERIFIER_URL`. Then Claude: trace KeyError, fix Domain_Cache header, investigate funding/shopify zeros.
