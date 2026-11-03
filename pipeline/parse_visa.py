#!/usr/bin/env python3
"""Parse a DOS Visa Bulletin monthly page into structured cutoff dates.

Fail-closed by design: any structural surprise (missing table, missing row
or column, malformed cell) aborts with a non-zero exit and NO output, so a
caller must never publish a partial or guessed parse.

Sources: https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/
  <FY>/visa-bulletin-for-<month>-<year>.html  (FY: Oct-Dec -> year+1, else year)
Tables are located by shape, never by position: the employment table is the
one whose header names All Chargeability / China / India and whose rows are
1st / 2nd / 3rd / 5th Unreserved. The FIRST such table in the page is Final
Action Dates (section A precedes section B); the SECOND is Dates for Filing.
Cell values: C (current), U (unavailable), or DDMMMYY (e.g. 01AUG23).
Parenthetical change notes like "(WAS 01JUN22)" are stripped before validation.

Usage:
  python3 parse_visa.py <month> <year> [html-file]
    month: full name (e.g. november) or number (11)
    html-file: optional saved page; otherwise fetched live from travel.state.gov
  Prints JSON: {month, year, fiscal_year, final_action, dates_for_filing}
  where each section maps EB-1/EB-2/EB-3/EB-5 (+ family rows when present)
  to {all, china, india} values in C/U/DDMMMYY form.
"""
import html.parser
import json
import re
import sys
import urllib.request
from datetime import datetime

MONTHS = ['january', 'february', 'march', 'april', 'may', 'june',
          'july', 'august', 'september', 'october', 'november', 'december']
CELL_RE = re.compile(r'^(C|U|\d{2}[A-Z]{3}\d{2})$')
PAREN_RE = re.compile(r'\(.*?\)')


def norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


def clean_cell(s):
    s = PAREN_RE.sub('', norm(s)).strip().upper()
    return s


def valid_date(s):
    if s in ('C', 'U'):
        return True
    try:
        datetime.strptime(s, '%d%b%y')
        return True
    except ValueError:
        return False


class TableParser(html.parser.HTMLParser):
    """Collect tables in document order as lists of cell-text rows."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self._table = []
        elif tag == 'tr' and self._table is not None:
            self._row = []
        elif tag in ('td', 'th') and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self._cell is not None:
            self._row.append(norm(''.join(self._cell)))
            self._cell = None
        elif tag == 'tr' and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == 'table' and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def is_eb_table(table):
    if not table:
        return False
    header = ' '.join(table[0]).upper()
    first_cells = [norm(r[0]).lower() if r else '' for r in table[1:]]
    return ('CHINA' in header and 'INDIA' in header
            and any(c == '1st' for c in first_cells)
            and any(c == '2nd' for c in first_cells)
            and any(c == '3rd' for c in first_cells))


def col_map(header):
    cols = {}
    for i, h in enumerate(header):
        u = norm(h).upper()
        if u.startswith('ALL CHARGEABILITY'):
            cols['all'] = i
        elif u.startswith('CHINA'):
            cols['china'] = i
        elif u.startswith('INDIA'):
            cols['india'] = i
        elif u.startswith('MEXICO'):
            cols['mexico'] = i
        elif u.startswith('PHILIPPINES'):
            cols['philippines'] = i
    return cols


ROW_MAP = [('1st', 'EB-1'), ('2nd', 'EB-2'), ('3rd', 'EB-3'),
           ('5th unreserved', 'EB-5')]


def parse_eb_table(table, which):
    cols = col_map(table[0])
    for need in ('all', 'china', 'india'):
        if need not in cols:
            raise SystemExit(f'{which}: missing column {need} (header: {table[0]})')
    out = {}
    for raw_label, key in ROW_MAP:
        row = None
        for r in table[1:]:
            if r and norm(r[0]).lower().startswith(raw_label):
                row = r
                break
        if row is None:
            raise SystemExit(f'{which}: missing row {raw_label}')
        vals = {}
        for name, i in cols.items():
            if i >= len(row):
                raise SystemExit(f'{which} {key}: row too short')
            v = clean_cell(row[i])
            if not CELL_RE.match(v) or not valid_date(v):
                raise SystemExit(f'{which} {key} {name}: bad cell {v!r}')
            vals[name] = v
        out[key] = vals
    return out


def fiscal_year(month_num, year):
    return year + 1 if month_num >= 10 else year


def bulletin_url(month_num, year):
    fy = fiscal_year(month_num, year)
    return (f'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/'
            f'{fy}/visa-bulletin-for-{MONTHS[month_num - 1]}-{year}.html')


def main():
    if len(sys.argv) < 3:
        print('usage: parse_visa.py <month> <year> [html-file]', file=sys.stderr)
        return 2
    m = sys.argv[1].lower()
    month_num = int(m) if m.isdigit() else MONTHS.index(m) + 1
    year = int(sys.argv[2])
    if len(sys.argv) > 3:
        raw = open(sys.argv[3], 'rb').read()
    else:
        url = bulletin_url(month_num, year)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (visa-bulletin-parser)'})
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                print(f'HTTP {r.status} for {url}', file=sys.stderr)
                return 1
            raw = r.read()
    text = raw.decode('utf-8', 'replace')
    if f'Visa Bulletin For {MONTHS[month_num - 1].capitalize()} {year}' not in norm(text):
        # Title check is soft: AEM markup may split it; the table checks below are hard.
        pass
    p = TableParser()
    p.feed(text)
    eb_tables = [t for t in p.tables if is_eb_table(t)]
    if len(eb_tables) != 2:
        print(f'expected exactly 2 EB tables (Final + Filing), found {len(eb_tables)}',
              file=sys.stderr)
        return 1
    try:
        final_action = parse_eb_table(eb_tables[0], 'Final Action')
        dates_for_filing = parse_eb_table(eb_tables[1], 'Dates for Filing')
    except SystemExit as e:
        print(f'PARSE FAILED: {e}', file=sys.stderr)
        return 1
    print(json.dumps({
        'month': MONTHS[month_num - 1],
        'year': year,
        'fiscal_year': fiscal_year(month_num, year),
        'final_action': final_action,
        'dates_for_filing': dates_for_filing,
    }, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
