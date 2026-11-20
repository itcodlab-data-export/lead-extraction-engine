# Data Extraction Engine (separate system)
Extraction-only. No sending, no copywriting. Daily autopilot = GitHub Actions, zero Claude tokens.
- Entry: main.py -> core/pipeline.py. Sources in sources/. Tunables only in config.py.
- Keep every file < 150 lines. One source failing must never stop the run (try/except in main).
- Never log emails/phones (core/logger.py masks them). No CSV artifacts. Secrets only in GitHub Secrets.
- Sheet: 5 tabs x 24 columns (core/models.py). Master_Dedup_Index is written first.
- Errors: logs print exception type only; 3-line diagnosis = which source, which step, exception name.
- Secrets: GOOGLE_SA_JSON, SHEET_ID, SEC_CONTACT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
