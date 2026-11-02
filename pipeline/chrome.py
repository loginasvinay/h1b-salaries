"""Shared page chrome (head, header, footer, disclaimer banner) for generated pages."""
import json, html
BASE = 'https://h1bsalary.clearinfohub.com'
STAMP = 'Data: DOL filings FY2023–FY2026 (through June 2026) · Page updated November 2026'
NAV = ('<nav><a href="/">Search</a><a href="/employers/">Employers</a><a href="/titles/">Job titles</a>'
       '<a href="/sponsors.html">Top sponsors</a><a href="/roles/">Roles</a>\n'
       '<a href="/cities/">Cities</a><a href="/states/">States</a><a href="/perm.html">PERM</a>'
       '<a href="/compare.html">Compare</a><a href="/about.html">About the data</a></nav>')
NOTE = ('<div class="note">Estimates from public U.S. Department of Labor records — wages are employer-attested '
        '<em>offered</em> wages, not verified salaries paid; counts are filings, not people. Not legal, financial, '
        'or career advice. See our <a href="/disclaimer.html">disclaimer &amp; terms</a>.</div>')
BANNER = ('<div class="disc-banner" id="disc-banner" role="note"><p>Estimates from public U.S. Department of Labor '
          'records — wages are employer-attested offered wages, not verified salaries paid. Not legal, financial, or '
          'career advice. <a href="/disclaimer.html">Full disclaimer</a></p><button type="button" id="disc-close" '
          'aria-label="Dismiss disclaimer banner">&times;</button></div>\n'
          "<script>(function(){try{var b=document.getElementById('disc-banner');if(!b)return;if(localStorage.getItem('h1b-disc-dismissed')){b.remove();return;}function pad(){document.body.style.paddingBottom=b.offsetHeight+'px';}pad();window.addEventListener('resize',pad);document.getElementById('disc-close').addEventListener('click',function(){try{localStorage.setItem('h1b-disc-dismissed','1');}catch(e){}b.remove();document.body.style.paddingBottom='';});}catch(e){}})();</script>")
FOOTER = ('<footer>Data: U.S. Department of Labor OFLC LCA disclosure files, certified H-1B cases, FY2023–FY2026.\n'
          'LCA wage is the <em>offered</em> wage attested by the employer, not actual salary paid.\n'
          'Figures are estimates from public records — see our <a href="/disclaimer.html">disclaimer &amp; terms</a>\n'
          'and <a href="/privacy.html">privacy policy</a>.</footer>')

esc = lambda s: html.escape(str(s), quote=True)

def money(v):
    return '—' if v is None else '$' + format(round(v), ',')

def page(path, title, desc, crumbs, body, extra_ld=(), scripts=''):
    """crumbs: [(name, path)], path relative to site root starting with '/'."""
    bl = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p}
                              for i, (n, p) in enumerate(crumbs)]}
    lds = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False)
                  for x in (bl, *extra_ld))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#f5f6f8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f141c" media="(prefers-color-scheme: dark)">
<link rel="preload" href="/fonts/instrument-sans.woff" as="font" type="font/woff" crossorigin><link rel="stylesheet" href="/style.css"><link rel="canonical" href="{BASE}{path}">{lds}<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6389116228399687" crossorigin="anonymous"></script></head><body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="wrap"><a class="logo" href="/">H1B <span>Pay Data</span></a>
{NAV}</div></header>
<div class="wrap" id="main">
{body}
</div>
{FOOTER}
{BANNER}
{scripts}</body></html>
'''
