"""Attach DOL wage level (I-IV) and annualized prevailing wage to filings that have a case number.
Usage: attach_levels.py LCA_DB TSV_DIR   (TSVs from extract_lca.py; run after match_cases.py)
cases.lvl: 1-4, or 0 when the filing states no level; cases.pw: annual prevailing wage, or null."""
import sqlite3, sys, glob, os

MULT = {'Year': 1, 'Hour': 2080, 'Week': 52, 'Bi-Weekly': 26, 'Month': 12}
LVL = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}

def main(db, tsv_dir):
    info = {}
    for f in sorted(glob.glob(os.path.join(tsv_dir, '*.tsv'))):
        if os.path.islink(f):
            continue
        for line in open(f):
            p = line.rstrip('\n').split('\t')
            if len(p) < 13:
                continue
            pw = None
            try:
                v = float(p[10].replace(',', '').replace('$', ''))
                a = v * MULT.get(p[11], 1)
                # same sanity band as offered wages; a mislabeled unit falls back to the raw figure
                pw = round(a) if 10_000 <= a <= 3_000_000 else (round(v) if 10_000 <= v <= 3_000_000 else None)
            except ValueError:
                pass
            info[p[0]] = (LVL.get(p[12].strip().upper(), 0), pw)
    c = sqlite3.connect(db)
    cols = [r[1] for r in c.execute('pragma table_info(cases)')]
    for col in ('lvl', 'pw'):
        if col not in cols:
            c.execute(f'alter table cases add column {col} int')
    c.execute('create index if not exists ix_cn on cases(cn)')
    rows = [(l, w, cn) for cn, (l, w) in info.items()]
    c.execute('update cases set lvl=0, pw=null')
    c.executemany('update cases set lvl=?, pw=? where cn=?', rows)
    c.commit()
    n, lv, pw = c.execute('select count(*), sum(lvl>0), count(pw) from cases').fetchone()
    print(f'filings {n:,}: wage level known {lv:,} ({lv / n:.1%}), prevailing wage known {pw:,} ({pw / n:.1%})')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
