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

# Web monorepo (itcodlab.com) — separate from the extraction engine above
- Layout: packages/design-tokens (Tailwind preset + CSS vars) · apps/web (Astro 5 static) · apps/form-worker (Cloudflare Worker) · apps/portal (scaffold, PR #3) · db/migrations.
- Not in scope yet: Lead Sending Engine build (paused), full Next.js portal (PR #3).
- Palette: 85% white/frosted glass · 10% #0071E3 · 5% #E11D48 (live dots, chamfer notches, high-signal badges only).
- Rules: files < 150 lines, 1 file = 1 job. Tunables only in lib/site.ts. No secrets in repo.
- Zero fabrication: no fake logos, testimonials, ROI numbers. Schema fields must match visible HTML.
- Links/assets: ALWAYS `withBase()` (apps/web/src/lib/withBase.ts). Hosting = GitHub Pages subpath (staging) or root (public_html).
- Env: SITE_URL, BASE_PATH (build); PUBLIC_FORM_ENDPOINT, PUBLIC_TURNSTILE_SITE_KEY, PUBLIC_CAL_LINK, PUBLIC_CF_ANALYTICS_TOKEN.
- New page = 1 `.mdx` in apps/web/src/content/{services,products,blog,case-studies}/ (route, sitemap, llms.txt automatic).
- Verify: `cd apps/web && npx astro check && bash scripts/verify-all.sh` (builds + audits both base paths).
- Errors: print `[FAIL] module | error | line` only.
- Staging (non-itcodlab.com SITE_URL) auto-adds noindex and Disallow-all robots.
