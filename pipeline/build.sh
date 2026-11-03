#!/usr/bin/env bash
# Full rebuild of the generated data + pages. Deterministic: unchanged inputs -> unchanged files,
# so a push only uploads what actually changed (one Cloudflare Pages build per push).
set -euo pipefail
SITE="$(cd "$(dirname "$0")/.." && pwd)"
DB="${DB:-/tmp/h1b-lca.db}"
python3 "$SITE/pipeline/build_db.py"     "$SITE" "$DB"        # data/emp-shards + data/cases -> SQLite
python3 "$SITE/pipeline/build_search.py" "$DB" "$SITE"        # sx/, title-shards/, emp-titles/
python3 "$SITE/pipeline/build_places.py" "$SITE"              # places.json
python3 "$SITE/pipeline/build_pages.py"  "$SITE"              # title pages, employer job-title tables, nav, sitemap
python3 "$SITE/pipeline/build_news.py"   "$SITE"              # H-1B & PERM news tab (data/news/*.json)
echo "Build done. Test with: python3 -m http.server 8765 & python3 pipeline/test_site.py http://localhost:8765"
