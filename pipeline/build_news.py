"""Build the H-1B & PERM news tab (/news.html) from Federal Register data.

Reads data/news/rules.json + data/news/news.json (copied from the
immigration-news project's fetch: DHS + DOL documents filtered to H-1B/PERM
topics) and renders one page with the site's shared chrome, so the tab
matches the rest of the site and survives pipeline runs.

Refresh flow (see pipeline/README.md):
  cd ~/workspace/immigration-news && python3 scripts/fetch.py
  cp data/rules.json data/news.json ~/workspace/h1b-site-repo/data/news/
  python3 pipeline/build_news.py ~/workspace/h1b-site-repo
Usage: build_news.py SITE"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from chrome import page, esc

SITE = sys.argv[1]

ASSETS = ['style.css', 'search.js', 'filings.js', 'jt.js', 'table.js', 'title-view.js', 'levels.js']
VER = {a: hashlib.sha1(open(f'{SITE}/{a}', 'rb').read()).hexdigest()[:10] for a in ASSETS if os.path.exists(f'{SITE}/{a}')}
ASSET_RE = re.compile(r'(["\'])/(' + '|'.join(re.escape(a) for a in VER) + r')(?:\?v=[0-9a-f]+)?\1')


def ver(html):
    return ASSET_RE.sub(lambda m: f'{m.group(1)}/{m.group(2)}?v={VER[m.group(2)]}{m.group(1)}', html)


def mini(h):
    return re.sub(r'>\s+<', '><', h).strip() + '\n'


def fmt_date(s):
    if not s:
        return 'Date not listed'
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').strftime('%b %d, %Y')
    except Exception:
        return s[:10]


def trunc(s, n=320):
    s = (s or '').strip()
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '…'


def load(name):
    with open(f'{SITE}/data/news/{name}') as f:
        return json.load(f)


def main():
    rules = load('rules.json')
    news = load('news.json')
    fetched_at = rules.get('fetched_at') or news.get('fetched_at') or ''
    feed = []
    for r in rules.get('items', []):
        feed.append({
            'date': r.get('publication_date', ''),
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'summary': r.get('abstract', ''),
            'source': 'Federal Register',
            'kind': r.get('type', ''),
            'comments_close_on': r.get('comments_close_on'),
            'sample': r.get('sample', False),
        })
    for n in news.get('items', []):
        feed.append({
            'date': n.get('pub_date', ''),
            'title': n.get('title', ''),
            'url': n.get('url', ''),
            'summary': n.get('description', ''),
            'source': n.get('source', 'Federal Register'),
            'kind': '',
            'comments_close_on': None,
            'sample': n.get('sample', False),
        })
    # Real items first (newest), sample placeholders last so they never lead.
    feed.sort(key=lambda x: (x['sample'], x['date'][:10]), reverse=True)
    feed = [i for i in feed if not i['sample']] + [i for i in feed if i['sample']]
    feed = feed[:60]

    cards = []
    for item in feed:
        meta = 'SAMPLE · ' if item['sample'] else ''
        meta += esc(item['source'])
        if item['kind']:
            meta += f' · {esc(item["kind"])}'
        meta += f' · {esc(fmt_date(item["date"]))}'
        comments = ''
        if item['comments_close_on']:
            comments = f'<p class="sub">Comments close {esc(fmt_date(item["comments_close_on"]))}</p>'
        summary = esc(trunc(item['summary'])) if item['summary'].strip() else (
            'Summary not published in the Federal Register record &mdash; '
            'see the official document for details.')
        cards.append(
            f'<div class="card"><div class="sub">{meta}</div>'
            f'<h3><a href="{esc(item["url"])}" rel="noopener">{esc(item["title"])}</a></h3>'
            f'<p>{summary}</p>{comments}</div>'
        )
    updated = fetched_at[:16].replace('T', ' ') if fetched_at else 'unknown'
    body = (
        '<h1>H-1B &amp; PERM News</h1>'
        '<p class="lede">The latest H-1B and PERM rules, proposed rules, and notices from the '
        'Federal Register (Department of Homeland Security and Department of Labor), newest first. '
        'Each headline links to the official document.</p>'
        f'<p class="sub">Last updated: {esc(updated)} UTC &middot; {len(feed)} items</p>'
        '<div class="note">Informational only &mdash; not legal advice. '
        'Items link to the official Federal Register document.</div>'
        + ''.join(cards)
    )
    h = page('/news.html', 'H-1B & PERM News — Latest Rules and Notices',
             'Latest H-1B and PERM news: rules, proposed rules, and notices from the Federal Register (DHS and DOL).',
             [('Home', '/'), ('News', '/news.html')], body)
    out = SITE + '/news.html'
    text = mini(ver(h))
    if os.path.exists(out) and open(out).read() == text:
        print('news.html unchanged')
        return
    open(out, 'w').write(text)
    print(f'news.html written ({len(feed)} items)')


if __name__ == '__main__':
    main()
