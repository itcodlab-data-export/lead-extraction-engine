# apps/portal — scaffold (built in PR #3)

Next.js portal for `app.itcodlab.com`. Not implemented yet; this folder fixes the contract so PR #3 plugs in.

- Roles: `SUPER_ADMIN` | `SUBSCRIBER` | `COMMUNITY_FREE` (see `db/migrations/001_*.sql`).
- Styling: `tailwind.config` uses `presets: [require("@itcodlab/design-tokens/preset")]` and imports `@itcodlab/design-tokens/tokens.css`.
- Data: Neon Postgres with RLS. Each request runs `SET LOCAL app.tenant_id` and `SET LOCAL app.role`.
- Sign-up is gated: `PUBLIC_SIGNUP_ENABLED=false` until launch.

See `.env.example` for the env contract.
