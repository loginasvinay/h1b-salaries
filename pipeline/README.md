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
| build_news.py | `/news.html` news tab from `data/news/*.json` (H-1B/PERM Federal Register items) |
| build_visa.py | `/visa-bulletin.html` Visa Bulletin tab (snapshot content, update monthly) |
| build_cases.py | `data/cases/` compact filings (run only when case data changes) |

News tab refresh: the Federal Register fetch lives in the immigration-news
project (`scripts/fetch.py`, DHS + DOL, H-1B/PERM relevance filter). To refresh
the tab, run that fetch, copy `data/rules.json` + `data/news.json` into
`data/news/`, then run `build_news.py` and push. The nav link lives in
`chrome.NAV` and is backfilled to every page by `build_pages.py`'s every-page
loop, so a fresh tab survives pipeline runs.

Rules
- No `_redirects`, ever, without a live test on Pages. Tail employers/titles use `view.html?e=` / `?t=`.
- Output must be byte-identical when inputs are unchanged (sorted keys, tie-broken sorts) so each push only
  uploads changed files. One push = one Cloudflare Pages build (free plan: 500/month shared across sites).
- Budget: < 15,000 files, every file < 10 MB (`test_site.py` enforces both).
- Data is still bootstrapped from the shards. When raw DOL OFLC files are available, add an ETL that writes
  the same SQLite schema (`emp`, `cases`) and everything downstream works unchanged.
