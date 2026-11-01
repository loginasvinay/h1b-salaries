# Pipeline

Rebuilds the generated parts of the site from the data shards in `data/`.

    pipeline/build.sh                                   # full, deterministic rebuild
    python3 -m http.server 8765 &
    python3 pipeline/test_site.py http://localhost:8765 # end-to-end checks (also run against the live URL)

| Script | Output |
| --- | --- |
| build_db.py | SQLite from `data/emp-shards` + `data/cases` (temp file, not committed) |
| build_search.py | `data/sx/` search index, `data/title-shards/`, `data/emp-titles/`, `data/titles-top.json` |
| build_places.py | `data/places.json` (cities + states for search) |
| build_pages.py | `/title/*.html`, `/titles/`, job-title tables on employer pages, nav, sitemap block |
| build_cases.py | `data/cases/` compact filings (run only when case data changes) |

Rules
- No `_redirects`, ever, without a live test on Pages. Tail employers/titles use `view.html?e=` / `?t=`.
- Output must be byte-identical when inputs are unchanged (sorted keys, tie-broken sorts) so each push only
  uploads changed files. One push = one Cloudflare Pages build (free plan: 500/month shared across sites).
- Budget: < 15,000 files, every file < 10 MB (`test_site.py` enforces both).
- Data is still bootstrapped from the shards. When raw DOL OFLC files are available, add an ETL that writes
  the same SQLite schema (`emp`, `cases`) and everything downstream works unchanged.
