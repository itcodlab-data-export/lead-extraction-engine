#!/usr/bin/env bash
# Builds + audits both hosting targets. Run from apps/web.
set -euo pipefail
echo "== Shared Server (root)"; BASE_PATH=/ SITE_URL=https://itcodlab.com npm run build --silent && BASE_PATH=/ SITE_URL=https://itcodlab.com npm run audit --silent
echo "== GitHub Pages (subpath)"; BASE_PATH=/itcodlab-web/ SITE_URL=https://example.github.io npm run build --silent && BASE_PATH=/itcodlab-web/ SITE_URL=https://example.github.io npm run audit --silent
