"""Stream a DOL OFLC LCA disclosure .xlsx into a compact TSV of certified H-1B rows.
Usage: extract_lca.py IN.xlsx OUT.tsv
Columns: case_number, employer_name, job_title, wage_from, wage_unit, worksite_city, worksite_state,
         received_date, begin_date, soc_code, pw_wage, pw_unit, pw_level
Reads the sheet XML directly (lxml iterparse) — openpyxl is far too slow for 7M rows."""
import sys, zipfile, datetime, re
from lxml import etree

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
WANT = ['CASE_NUMBER', 'CASE_STATUS', 'VISA_CLASS', 'EMPLOYER_NAME', 'JOB_TITLE', 'WAGE_RATE_OF_PAY_FROM',
        'WAGE_UNIT_OF_PAY', 'WORKSITE_CITY', 'WORKSITE_STATE', 'RECEIVED_DATE', 'BEGIN_DATE', 'SOC_CODE',
        'PREVAILING_WAGE', 'PW_UNIT_OF_PAY', 'PW_WAGE_LEVEL']
OUT = ['CASE_NUMBER', 'EMPLOYER_NAME', 'JOB_TITLE', 'WAGE_RATE_OF_PAY_FROM', 'WAGE_UNIT_OF_PAY', 'WORKSITE_CITY',
       'WORKSITE_STATE', 'RECEIVED_DATE', 'BEGIN_DATE', 'SOC_CODE', 'PREVAILING_WAGE', 'PW_UNIT_OF_PAY', 'PW_WAGE_LEVEL']
EXCEL0 = datetime.date(1899, 12, 30)

def col_index(ref):
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return n - 1

def as_date(v):
    if not v:
        return ''
    try:
        f = float(v)
        return (EXCEL0 + datetime.timedelta(days=int(f))).isoformat()
    except ValueError:
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})', v)
        if m:
            return m.group(0)
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', v)
        return f'{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}' if m else ''

def main(src, dst):
    z = zipfile.ZipFile(src)
    names = z.namelist()
    sst = []
    if 'xl/sharedStrings.xml' in names:
        for _, si in etree.iterparse(z.open('xl/sharedStrings.xml'), tag=NS + 'si'):
            sst.append(''.join(si.itertext()))
            si.clear()
    sheet = sorted(n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml$', n))[0]
    hdr = None
    kept = total = 0
    with open(dst, 'w') as out:
        for _, row in etree.iterparse(z.open(sheet), tag=NS + 'row'):
            vals = {}
            for c in row.iterfind(NS + 'c'):
                t = c.get('t')
                if t == 'inlineStr':
                    v = ''.join(c.itertext())
                else:
                    ve = c.find(NS + 'v')
                    v = ve.text if ve is not None else ''
                    if t == 's' and v:
                        v = sst[int(v)]
                vals[col_index(c.get('r'))] = (v or '').strip()
            row.clear()
            while row.getprevious() is not None:
                del row.getparent()[0]
            if hdr is None:
                hdr = {v.upper(): i for i, v in vals.items()}
                miss = [w for w in WANT if w not in hdr]
                if miss:
                    raise SystemExit(f'missing columns {miss}')
                continue
            total += 1
            g = lambda k: vals.get(hdr[k], '')
            if not g('CASE_STATUS').lower().startswith('certified') or g('VISA_CLASS') != 'H-1B':
                continue
            if g('CASE_STATUS').lower() != 'certified':   # LCA statuses: Certified / Certified - Withdrawn
                continue
            rec = {k: g(k) for k in OUT}
            rec['RECEIVED_DATE'] = as_date(rec['RECEIVED_DATE'])
            rec['BEGIN_DATE'] = as_date(rec['BEGIN_DATE'])
            out.write('\t'.join(rec[k].replace('\t', ' ').replace('\n', ' ') for k in OUT) + '\n')
            kept += 1
    print(f'{src}: {total:,} rows, kept {kept:,} certified H-1B')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
