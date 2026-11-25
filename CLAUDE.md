# Data Extraction Engine (separate system)
Extraction-only. No sending, no copywriting. Daily autopilot = GitHub Actions, zero Claude tokens.
- Entry: main.py -> core/pipeline.py. Sources in sources/. Tunables only in config.py.
- Keep every file < 150 lines. One source failing must never stop the run (try/except in main).
- Never log emails/phones (core/logger.py masks them). No CSV artifacts. Secrets only in GitHub Secrets.
- Sheet: 5 tabs x 24 columns (core/models.py). Master_Dedup_Index is written first.
- Errors: logs print exception type only; 3-line diagnosis = which source, which step, exception name.
- Secrets: GOOGLE_SA_JSON, SHEET_ID, SEC_CONTACT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
- Safety: core/safety_guard.py holds immutable SMTP ceilings (config may be stricter, never looser); CI gate = tests/test_safety_locks.py. Counter unreadable => SMTP skipped (fail-closed). UTC dates only.
- Optional secrets (missing = skipped): PRODUCTHUNT_TOKEN, API_KEYS (NAME=value lines: REOON_API_KEY, VERIFALIA_USER/PASS, ZEROBOUNCE_API_KEY, ABSTRACT_API_KEY, HUNTER_API_KEY, SHARED_VERIFIER_URL/KEY).
- Schedule: run2.yml every 3 hours (cron 17 */3, 8 runs/day). Shared-server SMTP stays <= 60/day, 15/hr, 5-6/hr per MX provider, 8 per run (SMTP_RUN_CAP); leads already in the Sheet are skipped BEFORE any verification.
- Sources: Batch1 (ats, shopify_reviews, producthunt) + Batch2/3 (youtube[key], social_dorks, launches, marketplaces, competitor_reviews) all run in parallel via batch1.fetch under one time cap, each isolated. Hiring rotates queries/cities per 3-hour slot (sources/dork.py slot/pick).
- Not wired: USPTO trademarks (needs API key + verified endpoint), Meta Ad Library API (political ads only outside EU).
