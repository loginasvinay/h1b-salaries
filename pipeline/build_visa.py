"""Build the Visa Bulletin tab (/visa-bulletin.html) with the site's chrome.

Content mirrors the immigration-news project's visa page: explainer, the
current month's key movements (snapshot — update when each new bulletin
drops), and a rolling archive linking to the official State Department page.
The official bulletin is always the source of truth; this tab summarizes it.

Usage: build_visa.py SITE"""
import hashlib
import os
import re
import sys
from datetime import datetime, timezone

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


DOS = 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html'


def last_six_bulletins():
    now = datetime.now(timezone.utc)
    months, y, m = [], now.year, now.month
    for _ in range(6):
        months.append(datetime(y, m, 1))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return months


def main():
    items = ''.join(
        f'<li>{d.strftime("%B %Y")} &mdash; <a href="{DOS}" rel="noopener">view on travel.state.gov</a></li>'
        for d in last_six_bulletins()
    )
    body = f"""<h1>Visa Bulletin</h1>
<p class="sub">Published monthly by the U.S. Department of State, usually around the middle of the month for the following month.</p>
<div class="card highlight">
  <h2>Current bulletin</h2>
  <p>Read the current Visa Bulletin on the official State Department page:</p>
  <p><a class="btn" href="{DOS}" rel="noopener">Open the official Visa Bulletin</a></p>
</div>
<div class="card highlight">
  <h2>November 2026 &mdash; key movements</h2>
  <p><strong>Employment-based (Final Action Dates):</strong></p>
  <ul>
    <li><strong>EB-1:</strong> China advances to Aug 1, 2023; India holds at Feb 1, 2023; all others current.</li>
    <li><strong>EB-2:</strong> India holds at Nov 1, 2013; China holds at Oct 1, 2021; rest of world advances 3 months to Apr 1, 2025.</li>
    <li><strong>EB-3:</strong> India advances 3 weeks to Jan 22, 2014; China advances 2 weeks to Jan 22, 2022; rest of world advances to Jun 15, 2024.</li>
    <li><strong>EB-5 Unreserved:</strong> India holds at Dec 1, 2023; China at Dec 1, 2016.</li>
  </ul>
  <p><strong>Family-based (Final Action Dates):</strong> F2A inches 1 month to Oct 22, 2026; F1, F2B, F3, and F4 jump 12 months each (F1 to Jan 22, 2021; F2B to Aug 22, 2020; F3 to Oct 22, 2015; F4 to Oct 22, 2012). No retrogressions anywhere.</p>
  <p><strong>Filing chart:</strong> USCIS confirms applicants use the <em>Dates for Filing</em> chart for November 2026. For India, Dates for Filing are far more generous: EB-1 Jul 1, 2024; EB-2 Jan 15, 2015; EB-3 Jan 15, 2015.</p>
  <p class="note">Source: U.S. Department of State, November 2026 Visa Bulletin (released Oct 22, 2026).</p>
</div>
<h2>How to read it</h2>
<div class="grid2">
  <div class="card"><h3>Final Action Dates</h3><p>The date your green-card number becomes available. If your priority date (when your petition was filed) is <em>earlier</em> than the date in this chart for your category and country, USCIS or the consulate can approve your case.</p></div>
  <div class="card"><h3>Dates for Filing</h3><p>The earliest date you can <em>submit</em> your adjustment-of-status application or start document collection with the National Visa Center &mdash; a head start before your Final Action Date is current.</p></div>
</div>
<h2>Recent bulletins</h2>
<ul class="archive">
{items}</ul>
<p class="note">Full cutoff-date tables are coming in a later version of this tab. For now, always use the official bulletin linked above as the source of truth.</p>"""
    h = page('/visa-bulletin.html', 'Visa Bulletin — Final Action Dates & Dates for Filing',
             'Monthly Visa Bulletin explainer, November 2026 key movements, archive, and how to read Final Action Dates vs Dates for Filing.',
             [('Home', '/'), ('Visa Bulletin', '/visa-bulletin.html')], body)
    out = SITE + '/visa-bulletin.html'
    text = mini(ver(h))
    if os.path.exists(out) and open(out).read() == text:
        print('visa-bulletin.html unchanged')
        return
    open(out, 'w').write(text)
    print('visa-bulletin.html written')


if __name__ == '__main__':
    main()
