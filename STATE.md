# STATE

## PR #1 — Core website + tokens + workflow + .htaccess + migration + form worker
Status: built and verified locally. Not yet merged/deployed.

Done
- Monorepo scaffold, shared tokens/preset, Astro 5 site (home, about, contact, early-access, lab, privacy-policy, terms, 404).
- Content collections: services (3), products (2), blog (empty), case-studies (empty — no fabricated content).
- SEO/AEO/GEO: sitemap, robots (prod vs staging), llms.txt, one JSON-LD @graph per page, staging noindex.
- `.github/workflows/deploy-pages.yml`, `apps/web/public/.htaccess`, `apps/form-worker/worker.js`, `db/migrations/001_*.sql`.
- Verified: `astro check` 0 errors; build + audit pass for BASE_PATH=/ and /itcodlab-web/; 375px no horizontal overflow (9 pages).

Not verified
- Migration SQL has not been executed against Postgres. Run it on a Neon branch first.
- Worker not deployed/tested against live Turnstile, Neon, ntfy.
- .htaccess not tested on a live Apache/LiteSpeed host.

Owner TODOs
- Settings -> Pages -> Source: GitHub Actions. Set repo Variables PUBLIC_FORM_ENDPOINT, PUBLIC_TURNSTILE_SITE_KEY, PUBLIC_CAL_LINK.
- Worker: `wrangler secret put` TURNSTILE_SECRET, DATABASE_URL, NTFY_TOPIC; add the Pages origin to ALLOWED_ORIGINS.
- Fill SAME_AS in lib/site.ts with real profiles; set Cloudflare Analytics token.
- `suppression_list` is created `if not exists`; if it exists in Neon with another shape, adjust worker SQL.

Notes
- Shadow wrapper uses CSS `filter`, which makes the inner `backdrop-filter` blur only content inside the card (flat backgrounds: no visible difference).
- Empty-collection warnings (blog, case-studies) during build are expected.
- Next: PR #2 (more content), PR #3 (Next.js portal).
