"""Generate job-title pages + titles index, inject job-title tables into static employer pages,
and keep nav/script tags consistent across every page. Idempotent: rerunning changes nothing.
Usage: build_pages.py SITE"""
import json, os, re, sys, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
from chrome import page, esc, money, NOTE, STAMP, BASE
SITE = sys.argv[1]
STATIC_T = 200
FYS = ['2023', '2024', '2025', '2026']

def load_dir(d):
    out = {}
    for f in sorted(glob.glob(f'{SITE}/data/{d}/*.json')):
        out.update(json.load(open(f)))
    return out

# Cache-busting: every reference to a shared asset carries ?v=<content hash>, so browsers
# can cache CSS/JS for a week yet pick up a new release on the very next page view.
import hashlib
# Data version: one hash over every data file the scripts fetch, written into each script as
# var DV='...'; fetches append ?v=DV, so a data refresh is never hidden behind a browser cache.
_h = hashlib.sha1()
for _f in sorted(glob.glob(SITE + '/data/**/*.json', recursive=True)):
    if _f.startswith(SITE + '/data/news/'):
        continue  # build-time input only (rendered into news.html); never fetched by a script, so a news refresh must not bump DV
    _h.update(_f[len(SITE):].encode()); _h.update(str(os.path.getsize(_f)).encode())
    _h.update(hashlib.sha1(open(_f, 'rb').read()).digest())
DV = _h.hexdigest()[:10]
for _a in ['filings.js', 'jt.js', 'title-view.js', 'search.js', 'levels.js', 'employer/view.html']:
    _p = f'{SITE}/{_a}'
    _t = open(_p).read()
    _t2 = re.sub(r"var DV='[0-9a-f]*';", f"var DV='{DV}';", _t)
    if _t2 != _t:
        open(_p, 'w').write(_t2)
ASSETS = ['style.css', 'search.js', 'filings.js', 'jt.js', 'table.js', 'title-view.js', 'levels.js']
VER = {a: hashlib.sha1(open(f'{SITE}/{a}', 'rb').read()).hexdigest()[:10] for a in ASSETS if os.path.exists(f'{SITE}/{a}')}
ASSET_RE = re.compile(r'(["\'])/(' + '|'.join(re.escape(a) for a in VER) + r')(?:\?v=[0-9a-f]+)?\1')
def ver(html):
    return ASSET_RE.sub(lambda m: f'{m.group(1)}/{m.group(2)}?v={VER[m.group(2)]}{m.group(1)}', html)

def write(path, text):
    text = ver(text)
    full = SITE + path
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full) and open(full).read() == text:
        return 0
    open(full, 'w').write(text)
    return 1

def mini(h):
    # light, safe minification: collapse whitespace between tags only
    return re.sub(r'>\s+<', '><', h).strip() + '\n'

TD = load_dir('title-shards')
ED = load_dir('emp-titles')
emp_static = {os.path.basename(f)[:-5] for f in glob.glob(SITE + '/employer/*.html')} - {'view'}

def emp_href(s, static):
    return f'/employer/{s}.html' if static else '/employer/view.html?e=' + s

def title_href(sl):
    t = TD.get(sl)
    if t and t['c'] >= STATIC_T:
        return f'/title/{sl}.html'
    return '/title/view.html?t=' + sl

def dist(p):
    lo, hi = p[0], p[4]
    span = max(hi - lo, 1)
    pc = lambda v: (v - lo) / span * 100
    ticks = ''.join(f'<span class="tick" style="left:{pc(p[i]):.1f}%" title="{money(p[i])}"></span>' for i in (1, 2, 3))
    return (f'<div class="dist"><div class="bar" style="left:0%;width:100%">{ticks}</div></div>'
            f'<div class="dist-labels"><span>{money(p[0])}</span><span class="med">{money(p[2])} median</span>'
            f'<span>{money(p[4])}</span></div>')

def stats_block(c, p, unit='certified filings'):
    cells = [(f'{c:,}', unit), (money(p[2]), 'Median base salary'), (money(p[1]), '25th pct'),
             (money(p[3]), '75th pct'), (money(p[4]), '90th pct'), (money(p[0]), '10th pct')]
    return '<div class="stats">' + ''.join(f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>'
                                           for v, l in cells) + '</div>'

# ---------------- related titles (internal links) ----------------
words_of = {sl: set(re.findall(r'[a-z0-9+#]+', t['n'].lower())) for sl, t in TD.items()}
by_word = collections.defaultdict(list)
for sl, t in TD.items():
    if t['c'] >= 50:
        for w in words_of[sl]:
            by_word[w].append(sl)

def related(sl, k=10):
    me = words_of[sl]
    cand = collections.Counter()
    for w in me:
        if len(by_word[w]) < 4000:
            for o in by_word[w]:
                if o != sl:
                    cand[o] += 1
    scored = sorted(cand, key=lambda o: (-(cand[o] / max(len(words_of[o] | me), 1)), -TD[o]['c'], o))
    return scored[:k]

# ---------------- title pages ----------------
def title_body(sl, t):
    n, c, p = t['n'], t['c'], t['p']
    yrows = ''.join(f'<tr><td>FY{fy}</td><td>{v[0]:,}</td><td>{money(v[1])}</td></tr>' for fy, v in sorted(t['y'].items(), reverse=True))
    erows = ''.join(f'<tr><td><a href="{emp_href(s, st)}">{esc(en)}</a></td><td>{ec:,}</td><td>{money(em)}</td></tr>'
                    for s, en, ec, em, st in t['e'])
    lrows = ''.join(f'<tr><td>{esc(ci)}, {esc(stt)}</td><td>{lc:,}</td><td>{money(lm)}</td></tr>' for ci, stt, lc, lm in t['l'])
    rel = related(sl)
    rel_html = ''.join(f'<a class="chip" href="{title_href(o)}">{esc(TD[o]["n"])} <span>{money(TD[o]["p"][2])}</span></a>' for o in rel)
    top = t['e'][0] if t['e'] else None
    intro = (f'<p class="lede">{c:,} certified H-1B filings list the job title <strong>{esc(n)}</strong> '
             f'(FY2023–FY2026). The median offered base salary is <strong>{money(p[2])}</strong>; '
             f'the middle half of filings fall between {money(p[1])} and {money(p[3])}.'
             + (f' The largest sponsor for this title is {esc(top[1])} ({top[2]:,} filings).' if top else '') + '</p>')
    return (f'<nav class="crumbs"><a href="/">Home</a> › <a href="/titles/">Job titles</a> › {esc(n)}</nav>'
            f'<h1>{esc(n)} H-1B Salary</h1>{intro}{stats_block(c, p)}{NOTE}<div class="note">{STAMP}</div>{dist(p)}'
            f'<div class="grid2"><div class="card"><h2>Salary by fiscal year</h2><table class="dt"><thead><tr><th>Year</th><th>Filings</th><th>Median</th></tr></thead><tbody>{yrows}</tbody></table></div>'
            f'<div class="card"><h2>Top cities</h2><table class="dt"><thead><tr><th>City</th><th>Filings</th><th>Median</th></tr></thead><tbody>{lrows}</tbody></table></div></div>'
            f'<div class="card"><h2>{esc(n)} salary by employer</h2><p class="sub">Top {len(t["e"])} sponsors by number of filings. Click a column to sort.</p>'
            f'<table class="dt sortable"><thead><tr><th>Employer</th><th>Filings</th><th>Median salary</th></tr></thead><tbody>{erows}</tbody></table></div>'
            + (f'<div class="card"><h2>Related job titles</h2><div class="chips">{rel_html}</div></div>' if rel else ''))

def faq(sl, t):
    n, p = t['n'], t['p']
    top = ', '.join(e[1] for e in t['e'][:3])
    qa = [(f'What is the H-1B salary for a {n}?',
           f'The median offered base salary across {t["c"]:,} certified H-1B filings for {n} (FY2023–FY2026) is {money(p[2])}. The middle 50% range from {money(p[1])} to {money(p[3])}.'),
          (f'Which companies sponsor H-1B visas for {n} roles?',
           f'The largest sponsors by filings are {top}.' if top else f'See the employer table for {n} sponsors.')]
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}

changed = 0
static_titles = sorted((sl for sl, t in TD.items() if t['c'] >= STATIC_T), key=lambda s: -TD[s]['c'])
for sl in static_titles:
    t = TD[sl]
    path = f'/title/{sl}.html'
    h = page(path, f'{t["n"]} H-1B Salary {FYS[-1]} — Median Pay by Employer & City',
             f'{t["n"]} H-1B salary: median {money(t["p"][2])} across {t["c"]:,} certified filings. Pay by employer, city and year.',
             [('Home', '/'), ('Job titles', '/titles/'), (t['n'], path)], title_body(sl, t),
             extra_ld=(faq(sl, t),), scripts='<script src="/table.js" defer></script>')
    changed += write(path, mini(h))
# stale static title pages
for f in glob.glob(SITE + '/title/*.html'):
    s = os.path.basename(f)[:-5]
    if s != 'view' and s not in set(static_titles):
        os.remove(f); changed += 1

# dynamic view for the long tail (titles with 5–199 filings)
view_body = ('<div id="t-view"><p>Loading job title…</p></div>'
             '<noscript><p>This page needs JavaScript. Browse <a href="/titles/">all job titles</a>.</p></noscript>')
changed += write('/title/view.html', mini(page('/title/view.html', 'Job Title H-1B Salary — Median Pay by Employer & City',
                 'H-1B salary for a job title: median pay, employers and cities from DOL filings.',
                 [('Home', '/'), ('Job titles', '/titles/'), ('Job title', '/title/view.html')], view_body,
                 scripts='<script src="/table.js" defer></script><script src="/title-view.js" defer></script>')))

# titles index: top 1,000
rows = ''.join(f'<tr><td><a href="{title_href(sl)}">{esc(TD[sl]["n"])}</a></td><td>{TD[sl]["c"]:,}</td><td>{money(TD[sl]["p"][2])}</td><td>{money(TD[sl]["p"][1])} – {money(TD[sl]["p"][3])}</td></tr>'
               for sl in sorted(TD, key=lambda s: -TD[s]['c'])[:1000])
idx = ('<h1>H-1B Salaries by Job Title</h1><p class="lede">The 1,000 most common job titles on certified H-1B filings, FY2023–FY2026. '
       'Search for any of 24,000+ titles from the <a href="/">homepage search</a>.</p>'
       f'{NOTE}<div class="card"><input class="search" id="tfilter" placeholder="Filter job titles…" aria-label="Filter job titles" data-filter="#tlist">'
       f'<table class="dt sortable" id="tlist"><thead><tr><th>Job title</th><th>Filings</th><th>Median salary</th><th>Middle 50%</th></tr></thead><tbody>{rows}</tbody></table></div>')
changed += write('/titles/index.html', mini(page('/titles/', 'H-1B Salary by Job Title 2026 — 1,000 Most Common Titles',
                 'H-1B salaries for the 1,000 most common job titles: filings, median pay and pay range from DOL data.',
                 [('Home', '/'), ('Job titles', '/titles/')], idx, scripts='<script src="/table.js" defer></script>')))

# ---------------- employer pages: job-title table ----------------
def jt_section(slug, rows):
    trs = ''.join(f'<tr><td>{"<a href=" + chr(34) + title_href(r[1]) + chr(34) + ">" + esc(r[0]) + "</a>" if r[1] else esc(r[0])}</td>'
                  f'<td>{r[2]:,}</td><td>{money(r[3])}</td><td>{money(r[4])} – {money(r[5])}</td></tr>' for r in rows[:25])
    more = f'<p class="sub">Showing the top 25 of {len(rows)} job titles.</p>' if len(rows) > 25 else ''
    return (f'<!--jt:start--><div class="card" id="job-titles" data-slug="{esc(slug)}"><h2>Salaries by job title</h2>'
            f'<div id="jt-box"><div class="tscroll"><table class="dt"><thead><tr><th>Job title</th><th>Filings</th><th>Median salary</th><th>Typical range</th></tr></thead><tbody>{trs}</tbody></table></div>{more}<p class="sub">Typical range = 10th to 90th percentile of offered salaries.</p></div></div><!--jt:end-->')

JT_RE = re.compile(r'<!--jt:start-->.*?<!--jt:end-->', re.S)
for s in sorted(emp_static):
    f = f'{SITE}/employer/{s}.html'
    t = open(f).read()
    sec = jt_section(s, ED.get(s, []))
    if '<!--jt:start-->' in t:
        t2 = JT_RE.sub(lambda m: sec, t)
    else:
        # place it right after the data-stamp note, ahead of the score card
        i = t.find(STAMP.split(' · ')[0])
        j = t.find('</div>', i) + 6 if i > 0 else -1
        if j <= 5:
            raise SystemExit('anchor not found in ' + f)
        t2 = t[:j] + sec + t[j:]
    if '/jt.js' not in t2:
        t2 = t2.replace('<script src="/filings.js"></script>', '<script src="/filings.js"></script><script src="/jt.js" defer></script>')
    if t2 != t:
        open(f, 'w').write(t2); changed += 1

# ---------------- employer pages: wage-level breakdown (all years server-rendered; levels.js adds year tabs) ----------------
LV = load_dir('emp-levels')
LNAMES = ['Not stated', 'Level I · Entry', 'Level II · Qualified', 'Level III · Experienced', 'Level IV · Fully competent']
LCOL = ['var(--hairline)', 'var(--l1)', 'var(--l2)', 'var(--l3)', 'var(--l4)']
def wl_section(slug):
    row = (LV.get(slug) or {}).get('ALL') or [0] * 5
    known = sum(x[0] for i, x in enumerate(row) if i and x)
    bar = ''.join(f'<div style="width:{x[0] / known * 100:.1f}%;background:{LCOL[i]}" title="{LNAMES[i]}: {x[0]:,}"></div>'
                  for i, x in enumerate(row) if i and x and known)
    trs = ''.join(f'<tr><td><i class="lvl-dot" style="background:{LCOL[i]}"></i>{LNAMES[i]}</td><td>{x[0]:,}</td>'
                  f'<td>{(f"{x[0] / known * 100:.0f}%" if i and known else "—")}</td><td>{money(x[1])}</td></tr>'
                  for i in (1, 2, 3, 4, 0) for x in [row[i]] if x)
    return (f'<!--wl:start--><div id="wage-levels" data-slug="{esc(slug)}"><h3>Wage-level mix</h3><div class="wl-body">'
            f'<div class="lvlbar">{bar}</div><div class="tscroll"><table class="dt"><thead><tr><th>Wage level</th><th>Filings</th>'
            f'<th>Share</th><th>Median offered</th></tr></thead><tbody>{trs}</tbody></table></div>'
            '<p class="sub">DOL prevailing-wage levels the employer selected for each filing (Level I = entry, Level IV = fully competent). '
            'Share excludes filings that state no level.</p></div></div><!--wl:end-->')
WL_RE = re.compile(r'<!--wl:start-->.*?<!--wl:end-->', re.S)
OLD_WL = re.compile(r'<h3>Wage-level mix.*?<div class="lvl-legend">.*?</div>', re.S)
for s in sorted(emp_static):
    f = f'{SITE}/employer/{s}.html'
    t0 = t = open(f).read()
    sec = wl_section(s)
    if '<!--wl:start-->' in t:
        t = WL_RE.sub(lambda m: sec, t)
    elif OLD_WL.search(t):
        t = OLD_WL.sub(lambda m: sec, t, count=1)
    else:
        t = t.replace('<!--jt:end-->', '<!--jt:end-->' + sec, 1)
    if '/levels.js' not in t:
        t = re.sub(r'(<script src="/jt\.js[^"]*" defer></script>)', r'\1<script src="/levels.js" defer></script>', t, count=1)
    if t != t0:
        open(f, 'w').write(t); changed += 1

# ---------------- every page: nav, theme colors, font preload ----------------
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6389116228399687" crossorigin="anonymous"></script>'
PRELOAD = '<link rel="preload" href="/fonts/instrument-sans.woff" as="font" type="font/woff" crossorigin>'
SWAP = [('The table below lists every case — job title, base salary, location, submit date and start date.', 'The table below lists every case — case number, job title, wage level, base salary, prevailing wage, location, submit date and start date.'),
        ('color:#8a93b8', 'color:var(--text2)'), ('background:#67e8f9', 'background:var(--l1)'),
        ('background:#22d3ee', 'background:var(--l2)'), ('background:#818cf8', 'background:var(--l3)'),
        ('background:#c084fc', 'background:var(--l4)'),
        ('<meta name="theme-color" content="#f5f5f7" media="(prefers-color-scheme: light)">', '<meta name="theme-color" content="#f5f6f8" media="(prefers-color-scheme: light)">'),
        ('<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">', '<meta name="color-scheme" content="only light">'),
        ('<meta name="theme-color" content="#0f141c" media="(prefers-color-scheme: dark)">', '<meta name="color-scheme" content="only light">')]
for f in sorted(glob.glob(SITE + '/**/*.html', recursive=True)):
    if '/.git/' in f:
        continue
    t0 = t = open(f).read()
    if '<a href="/employers/">Employers</a>' in t and 'href="/titles/">Job titles' not in t:
        t = t.replace('<a href="/employers/">Employers</a>', '<a href="/employers/">Employers</a><a href="/titles/">Job titles</a>', 1)
    if '<a href="/perm.html">PERM</a>' in t and 'href="/news.html"' not in t:
        t = t.replace('<a href="/perm.html">PERM</a>', '<a href="/perm.html">PERM</a><a href="/news.html">News</a>', 1)
    if '<a href="/news.html">News</a>' in t and 'href="/visa-bulletin.html"' not in t:
        t = t.replace('<a href="/news.html">News</a>', '<a href="/news.html">News</a><a href="/visa-bulletin.html">Visa Bulletin</a>', 1)
    for a, b in SWAP:
        t = t.replace(a, b)
    t = ver(t)
    if ADSENSE not in t and '</head>' in t:
        t = t.replace('</head>', ADSENSE + '</head>', 1)
    if 'href="/style.css"' in t and PRELOAD not in t:
        t = t.replace('<link rel="stylesheet" href="/style.css">', PRELOAD + '<link rel="stylesheet" href="/style.css">', 1)
    if t != t0:
        open(f, 'w').write(t); changed += 1
print('title pages', len(static_titles), '| files changed', changed)

# ---------------- sitemap: job-title pages (idempotent block) ----------------
sm_path = SITE + '/sitemap.xml'
sm = open(sm_path).read()
sm = re.sub(r'<!--titles:start-->.*?<!--titles:end-->\n?', '', sm, flags=re.S)
block = '<!--titles:start-->\n' + ''.join(f'<url><loc>{BASE}{p}</loc></url>\n' for p in ['/titles/'] + [f'/title/{s}.html' for s in static_titles]) + '<!--titles:end-->\n'
sm2 = sm.replace('</urlset>', block + '</urlset>')
if sm2 != open(sm_path).read():
    open(sm_path, 'w').write(sm2); print('sitemap updated')
