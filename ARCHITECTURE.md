# ARCHITECTURE - full technical detail (every module must be named here; tests/test_repo_rules.py enforces it)

## Purpose and flow
Extraction-only lead engine. One run = `python main.py` (GitHub Actions workflow run2.yml): collect company signals -> audit each company's site -> find people -> build emails -> verify -> score/QC -> dedup -> append to Google Sheet -> one summary line (log + optional Telegram).

config.VERSION/BRAIN_NOTE must be bumped on every code/rule change (test: VERSION date appears in CHANGELOG.md).

main.py order: `safety_guard.preflight(config)` (violation => print BLOCK_MSG, return 2, no work) -> sources hiring, funding (each try/except) -> shopify.fetch(signals) -> batch1.fetch(sources=batch1.SOURCES + batch2.SOURCES) in parallel (cap BATCH1_BUDGET_SEC=300, max BATCH1_MAX_SIGNALS=60, reserved slots after the first MAX_COMPANIES_PER_RUN*2 signals) -> `Sheet()` -> Dedup from Master_Dedup_Index + Do_Not_Contact -> `_gate(sh)` builds the SmtpGate from State (None on any read/parse error = fail-closed) and DomainCache from the Domain_Cache tab -> `pipeline.build_leads` -> gate.flush -> write_domain_cache -> `sh.sync(leads)` -> rotation alert if Raw_Leads > ROTATION_ALERT_ROWS -> `alert.send` summary. Return 0.

Signal dict (every source): `company, country (US|INDIA), source_platform, signal, source_url, evidence, domain_hint, people[]`.

## config.py (only place for tunables)
TARGET_COUNTRY (env, BOTH|US|INDIA), SHEET_ID, SEC_USER_AGENT (needs SEC_CONTACT), `_load_api_keys()` (env API_KEYS secret, NAME=value lines -> os.environ via setdefault), MAX_COMPANIES_PER_RUN=60, MAX_CONTACTS_PER_COMPANY=8, MAX_PER_DEPARTMENT=2, MIN_LEAD_SCORE=65, SHEET_CHUNK=500, CELL_MAX_CHARS=1500, ROTATION_ALERT_ROWS=15000, HTTP_TIMEOUT=8, DORK_JITTER=(4,8). SMTP block: SMTP_HOURLY_CAP=15, SMTP_MX_HOURLY_CAP=5, SMTP_DAILY_CAP=60, SMTP_JITTER=(30,60), SMTP_MIN_SCORE=75, SMTP_MAX_PRIORITY=1, SMTP_RUN_CAP=8, SMTP_FLUSH_EVERY=5, SMTP_WARMUP_START, SMTP_STATE_FILE=.smtp_state.json, SHARED_VERIFIER_URL. BATCH1_BUDGET_SEC=300, BATCH1_MAX_SIGNALS=60. JOB_QUERIES (12), JOB_QUERIES_PER_RUN=3, JOB_CITIES (unused after revert), JOB_LOCATIONS, `countries()`.

## sources/
- sources/hiring.py: python-jobspy, Indeed only; `dork.pick(JOB_QUERIES, 3)` per country per run; results_wanted 15, hours_old 72; signal `Hiring`.
- sources/funding.py: SEC EDGAR Form D atom feed (US, 0.25s delay, UA with SEC_CONTACT) + RSS Inc42/Entrackr/YourStory (INDIA); signal `Funding`.
- sources/shopify.py: DDG dork "powered by shopify" with USD/INR; signal `D2C_Shopify`; max 30.
- sources/batch1.py: runs a tuple of (name, fn) sources in daemon threads under one deadline, isolated try/except, returns first BATCH1_MAX_SIGNALS. Exposes SOURCES (ats, shopify_reviews, producthunt).
- sources/batch2.py: registry SOURCES = youtube, social_dorks, launches, marketplaces, competitor_reviews (docstring lists unwired USPTO / Meta Ad Library).
- sources/ats.py: dorks site:boards.greenhouse.io / jobs.lever.co / jobs.ashbyhq.com / apply.workable.com for Meta Ads, Performance Marketing, Shopify roles; company from URL slug; also exports `_bing_url`, `parse_results`.
- sources/shopify_reviews.py: apps.shopify.com 1-2 star reviews of Meta/Facebook pixel/CAPI apps mentioning tracking problems; country from reviewer location; signal `Broken_Tracking_Review`.
- sources/producthunt.py: Product Hunt GraphQL v2 newest 30 posts; needs PRODUCTHUNT_TOKEN else skip; India if .in domain or India keywords.
- sources/dork.py: shared helper: `search(q)` DDG html (Bing fallback) -> [{url,title,snippet}], `site_in(text)` first business domain excluding platforms, `slot(n)`/`pick(items,k)` 3-hour-slot rotation, `signal(...)`, `run(queries, ...)`.
- sources/social_dorks.py (Reddit/X/LinkedIn help requests that name a store domain, signal `Help_Request`), sources/launches.py (Kickstarter/Indiegogo, `Launch`), sources/marketplaces.py (Flippa/Acquire, `Store_Listing`), sources/competitor_reviews.py (Trustpilot complaints about AdKrity/Grexa/agencies, `Competitor_Complaint`), sources/youtube.py (YouTube Data API v3 search + channel description site; needs YOUTUBE_API_KEY).

## core/
- core/pipeline.py: `build_leads(signals, dd, gate, cache)`: dedupe companies by name, ThreadPool(8), 12-minute deadline. Per company `_one`: auditor.audit -> emails = scraped + contacts.deep_emails -> stakeholders.extract -> verifier.detect_pattern / cache pattern -> per person build lead: email via scraped match / domain pattern / permutation (`_email`), SKIP if fingerprint already in dd.fp (before any verification), `verifier.verify` (route hot|smtp|drop), if route smtp then `apiverify.check` (valid->hot "API_Verified", invalid->drop), `qc.score`, if still Permutated_Unverified then `apiverify.smtp_last_resort` (shared server, gated) -> "SMTP_Verified", qc.qc -> "YES / Ready_To_Export" else "NO", dedup.reject_reason, dd.add.
- core/auditor.py: resolve domain (hint, then slug.com/.in/.co with brand match), fetch contact paths, regexes for emails/tel:/socials, Meta Pixel / CAPI / GTM / Shopify detection, industry tag, audit facts.
- core/stakeholders.py: team/about page scraping (PATHS), 5 tracks (Executive, Marketing, Sales, Tech_IT, HR_Ops), junior filter, name regex, cap 8 per company / 2 per dept, priority order, size_tier.
- core/contacts.py: deep email scrape of /contact, /contact-us, /about, /team, /policies/contact-information, /privacy-policy; text, mailto:, JSON-LD, Cloudflare data-cfemail; only on-domain emails.
- core/verifier.py: layer1 syntax/disposable/role filter, DNS MX/SPF/DMARC (cached), Gravatar probe, permutations (first.last, first, flast, firstlast, first_l), `verify` -> (status, route), `detect_pattern`.
- core/apiverify.py: provider waterfall Reoon > Verifalia > ZeroBounce > Abstract > Hunter (env keys; missing key = skipped); DomainCache (Catch_All, Pattern per domain, backed by Domain_Cache tab; tolerates missing keys and legacy v.8 rows via `row_from_values`); `check` (catch-all domains never trusted valid); `smtp_last_resort` (only SHARED_VERIFIER_URL set, gate present, Lead_Score>=75, priority 1, gate.acquire ok; HTTP 429 sets gate.blocked; replies feed gate.report).
- core/safety_guard.py: IMMUTABLE ceilings (MappingProxyType) HOURLY 15, MX_HOURLY 6, JITTER_MIN_SEC 30, DAILY_ABSOLUTE 300, OPERATIONAL_DAILY 60, MIN_SCORE 75, LOCK_HOURS 72; WARMUP {1:50,2:100,3:200,4:300}; BLOCK_MSG; FAIL_CLOSED; `violations/preflight/effective_daily_cap/warmup_cap/may_run_smtp`; UTC helpers.
- core/smtp_gate.py: SmtpGate: merges Sheet State + local flock/atomic JSON file (larger count wins), per-hour/per-day/per-MX-provider counters (UTC rollover), per-run cap SMTP_RUN_CAP, jitter sleep inside `acquire`, circuit breaker `classify/report` (554/Spamhaus, 450 with blocked|spam|blacklist|reputation|abuse => lock 72h), flush to State every 5, `mx_provider()` (google/microsoft/other).
- core/sheets_sync.py: gspread via service account; `Sheet.sync` writes Master_Dedup_Index FIRST then Raw_Leads, Hot_Leads_Ready (YES and not Permutated_Unverified), Needs_SMTP_Check (YES and Permutated_Unverified); State tab: own `smtp_state` key row (read raises on bad JSON => fail-closed); Domain_Cache positional read (legacy header tolerated) / write; `append_aux`/`last_aux_row` helpers for Run_Log and Brain; retry/backoff.
- core/dedup.py: 3-key fingerprint (name+domain sha1[:16]), email (gmail dots/plus normalised), LinkedIn slug; generic inbox, competitor-agency name and Do_Not_Contact rejects.
- core/qc.py: score (status, evidence, audit fact, track, phone, LinkedIn, industry, priority) and 7-point QC (MIN_LEAD_SCORE 65).
- core/report.py: `write_run_log(sh, metrics)` appends one row to Run_Log (23 columns RUN_COLS, aligned to the legacy v.8 header) after every run; `brain_note(sh)` appends one Brain line when config.VERSION is new; both swallow all errors (reporting never breaks a run). `health()` = GOOD / OK - leads but none hot / OK - no new leads / ERRORS.
- core/models.py: 24 columns, TABS, dedup/DNC column lists. core/net.py: requests session helpers (get/text/jitter). core/logger.py: PII-masking logger. core/alert.py: log + optional Telegram. core/__init__.py, sources/__init__.py: package markers.

## Google Sheet (id in STATE.md)
Written: Raw_Leads, Hot_Leads_Ready, Needs_SMTP_Check, Master_Dedup_Index, Do_Not_Contact (headers auto-created), State (smtp_state row; legacy rows untouched), Domain_Cache, Run_Log (one row per run), Brain (one line per new config.VERSION). Hot = Email_Status not Permutated_Unverified and QC YES (scraped/pattern MX, Gravatar, API-verified or shared-server verified).

## Auth and secrets (names only)
GOOGLE_SA_JSON (Service Account JSON, Sheets scope), SHEET_ID, SEC_CONTACT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PRODUCTHUNT_TOKEN, YOUTUBE_API_KEY, API_KEYS (multi-line NAME=value: REOON_API_KEY, VERIFALIA_USER, VERIFALIA_PASS, ZEROBOUNCE_API_KEY, ABSTRACT_API_KEY, HUNTER_API_KEY, SHARED_VERIFIER_URL, SHARED_VERIFIER_KEY). All in GitHub Secrets; none in repo.

## Workflows
.github/workflows/run2.yml (production, see STATE.md), .github/workflows/ci.yml (tests + PR rules).
(unpack.yml and daily_leads.yml were removed 2026-11-26.)

## Tests and enforcement
- tests/test_offline.py: unit tests of dedup/verifier/qc/stakeholders/contacts/apiverify/sources/batch runner/dork helpers (no network).
- tests/test_safety_locks.py: pins ceilings, config within ceilings, warm-up ramp, hourly/MX/daily caps, 429 lock, dual-lock counter, breaker, fail-closed, PII-free logs, no CSV, UTC-only, files < 150 lines, per-run cap, State row.
- tests/test_repo_rules.py: four memory files exist and are structured; STATE-CHECK block equals code (ceilings, cron, run cap); ARCHITECTURE names every module and workflow; CHANGELOG format; no secret-looking strings; PR-rule function behaviour.
- tools/check_pr_rules.py: any non-doc change needs STATE.md + CHANGELOG.md in the same change; CHANGELOG append-only; protected files (safety_guard.py, test_safety_locks.py, test_repo_rules.py, tools/check_pr_rules.py, ci.yml, .githooks/pre-commit) need `APPROVED-BY-FAIZ` in the added CHANGELOG lines. Runs in ci.yml (PRs) and .githooks/pre-commit (`git config core.hooksPath .githooks`).
- .claude/settings.json: SessionStart hook prints STATE.md into every Claude Code session.
- GitHub setting needed from owner: branch protection on main requiring check `gate`.
