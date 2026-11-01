"""End-to-end checks for the H-1B site. Run against a local server or the live site:
    python3 pipeline/test_site.py http://localhost:8765
    python3 pipeline/test_site.py https://h1b-salaries.pages.dev
Exits non-zero if any check fails."""
import sys, re, os, glob
from playwright.sync_api import sync_playwright

B = sys.argv[1].rstrip('/')
ok, bad = [], []

def check(name, cond, detail=''):
    (ok if cond else bad).append(name)
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

def num(s):
    return int(re.sub(r'[^0-9]', '', s) or 0)

def same_page(want, got):
    strip = lambda u: re.sub(r'\.html(?=$|\?)', '', u.split('#')[0])
    return strip(want) == strip(got)

def search(pg, q, wait=2500):
    pg.fill('#q', '')
    pg.fill('#q', q)
    pg.wait_for_function("document.querySelector('#res').textContent.indexOf('Searching')<0", timeout=15000)
    pg.wait_for_timeout(300)
    return pg.eval_on_selector_all('#res a', 'els=>els.map(e=>[e.querySelector(".n")?e.querySelector(".n").textContent:e.textContent,e.getAttribute("href")])')

with sync_playwright() as p:
    kw = {'executable_path': '/usr/bin/google-chrome'} if os.path.exists('/usr/bin/google-chrome') else {}
    br = p.chromium.launch(args=['--no-sandbox'], **kw)
    pg = br.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))

    # 1. Static employer page
    u = B + '/employer/google-llc-google.html'
    pg.goto(u)
    t = pg.inner_text('body')
    check('google: stats', '34,084' in t and '$179,560' in t and re.search(r'Sponsorship score:\s*78', t) is not None)
    check('google: no redirect', same_page(u, pg.url), pg.url)
    pg.wait_for_selector('#jt-box .tabs', timeout=20000)
    jt = pg.inner_text('#jt-box')
    check('google: job-title table interactive', 'Software Engineer' in jt and 'All years' in jt)
    pg.click('#jt-box [data-fy="2025"]')
    check('google: job-title FY tab', 'FY2025' in pg.inner_text('#jt-box .tab.active'))
    pg.click('#jt-box button[data-t]')            # "See filings" for the top title
    pg.wait_for_selector('#filings-wrap table', timeout=60000)
    w = pg.inner_text('#filings-wrap')
    check('google: drill-down filters filings', 'matching' in w, re.search(r'[\d,]+ filings[^\n]*', w).group(0))
    pg.click('#f-clear')
    pg.click('#filings-wrap [data-fy="ALL"]')
    n = num(re.search(r'([\d,]+) filings', pg.inner_text('#filings-wrap')).group(1))
    check('google: all filings 34,084', n == 34084, str(n))
    cnos = pg.eval_on_selector_all('#filings-wrap td.cno', 'els=>els.map(e=>e.textContent)')
    good = [c for c in cnos if re.fullmatch(r'I-\d{3}-\d{5}-\d{6}', c)]
    check('google: case numbers shown', len(good) >= 45, f'{len(good)}/{len(cnos)} rows')

    # 2. Amazon pagination
    pg.goto(B + '/employer/amazon-com-services-llc-amazon.html')
    pg.click('#filings-load')
    pg.wait_for_selector('#filings-wrap table', timeout=90000)
    w = pg.inner_text('#filings-wrap')
    check('amazon: 55,891 filings / 1,118 pages', '55,891' in w and 'of 1,118' in w)
    pg.click('#filings-wrap button[data-p="2"]')
    check('amazon: page 2', 'Page 2 of 1,118' in pg.inner_text('#filings-wrap'))

    # 3. Search
    pg.goto(B + '/')
    r = search(pg, 'cra')
    emps = [x[0] for x in r if x[1].startswith('/employer/')]
    want = ['CRA International', 'Cravath', 'Crawford, Murphy', 'CRADLEPOINT', 'CRAVE INFOTECH', 'Crawford Hospital']
    check('search cra: employer order', all(e.startswith(wn) for e, wn in zip(emps, want)) and len(emps) >= 6, ' | '.join(emps[:6]))
    r = search(pg, 'software engineer')
    check('search software engineer: title first', r and r[0][0] == 'Software Engineer' and r[0][1].startswith('/title/'), str(r[:2]))
    r = search(pg, 'google')
    check('search google: Google LLC first', r and r[0][0] == 'Google LLC', str(r[:1]))
    r = search(pg, 'tata')
    check('search tata: TCS first', r and r[0][0].startswith('TATA CONSULTANCY'), str(r[:1]))
    r = search(pg, 'infosys data analyst')
    check('search combo: employer + title', r and 'INFOSYS' in r[0][0].upper() and 't=' in r[0][1], str(r[:1]))
    r = search(pg, 'gogle')
    check('search typo: did you mean Google', any(x[0] == 'Google LLC' for x in r), str(r[:3]))
    r = search(pg, 'seattle')
    check('search city', any(x[1].startswith('/city/seattle') for x in r), str(r[:3]))
    r = search(pg, 'data scien')
    check('search partial: data scientist', r and r[0][0] == 'Data Scientist', str(r[:1]))

    # 4. Tail employer via direct view link
    u = B + '/employer/view.html?e=cravath-swaine-moore-llp-cravat'
    pg.goto(u)
    pg.wait_for_selector('#emp-view h1')
    check('cravath: renders', pg.inner_text('#emp-view h1') == 'Cravath, Swaine & Moore LLP')
    check('cravath: no redirect', same_page(u, pg.url), pg.url)
    pg.wait_for_selector('#jt-box .tabs', timeout=20000)
    pg.click('#filings-load')
    pg.wait_for_selector('#filings-wrap table', timeout=60000)
    check('cravath: 53 filings', re.search(r'\b53 filings', pg.inner_text('#filings-wrap')) is not None)

    # 5. Employer + title deep link
    pg.goto(B + '/employer/google-llc-google.html?t=data%20scientist#filings')
    pg.wait_for_selector('#filings-wrap table', timeout=60000)
    check('deep link ?t= filters', 'matching' in pg.inner_text('#filings-wrap'))

    # 6. Title pages
    pg.goto(B + '/title/software-engineer.html')
    t = pg.inner_text('body')
    check('title page: software engineer', 'Software Engineer H-1B Salary' in t and 'salary by employer' in t)
    pg.goto(B + '/titles/')
    check('titles index', pg.locator('#tlist tbody tr').count() == 1000)
    pg.goto(B + '/title/view.html?t=cost-accountant')
    pg.wait_for_selector('#t-view h1')
    check('title view: tail title', 'Cost Accountant' in pg.inner_text('#t-view h1'), pg.inner_text('#t-view h1'))

    # 7. Misses never navigate
    for u in ['/employer/view.html?e=no-such-xyz', '/title/view.html?t=no-such-xyz']:
        pg.goto(B + u)
        pg.wait_for_timeout(1500)
        check('miss shows message: ' + u, 'not found' in pg.inner_text('body').lower() and same_page(B + u, pg.url), pg.url)
    pg.goto(B + '/employer/view.html')
    pg.wait_for_timeout(800)
    check('bare view: no redirect', same_page(B + '/employer/view.html', pg.url), pg.url)

    # 8. No sideways scrolling on a small phone (desktop-style scrollbar = narrowest real case)
    sp = br.new_page(viewport={'width': 340, 'height': 760})
    wide = []
    for u in ['/', '/employer/google-llc-google.html', '/employer/view.html?e=cravath-swaine-moore-llp-cravat',
              '/title/software-engineer.html', '/titles/', '/sponsors.html', '/compare.html']:
        sp.goto(B + u)
        sp.wait_for_timeout(1200)
        sw, vw = sp.evaluate('[document.documentElement.scrollWidth,document.documentElement.clientWidth]')
        if sw > vw:
            wide.append(f'{u} {sw}>{vw}')
    check('phone: no horizontal overflow', not wide, '; '.join(wide))
    check('no JS errors', not errs, '; '.join(errs[:3]))
    br.close()

# 8. Cloudflare Pages budget (local builds only)
if B.startswith('http://localhost'):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = [f for f in glob.glob(root + '/**/*', recursive=True) if os.path.isfile(f) and '/.git/' not in f]
    big = max(os.path.getsize(f) for f in files)
    check('budget: files < 15,000', len(files) < 15000, str(len(files)))
    check('budget: largest file < 10 MB', big < 10 * 2**20, f'{big/2**20:.1f} MB')
    check('no _redirects file', not os.path.exists(root + '/_redirects'))

print(f'\n{len(ok)} passed, {len(bad)} failed')
sys.exit(1 if bad else 0)
