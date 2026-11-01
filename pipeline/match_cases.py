"""Attach DOL case numbers to the existing filings in lca.db.
Usage: match_cases.py LCA_DB TSV_DIR
Each extracted row (extract_lca.py) is matched to a stored filing by job title + submit date +
start date, restricted to the employer (slug prefix from its name), preferring an exact wage match.
Writes cases.cn (case number) in place; prints match statistics."""
import sqlite3, sys, glob, re, collections, os

MULT = {'Year': 1, 'Hour': 2080, 'Week': 52, 'Bi-Weekly': 26, 'Month': 12}

def base(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().replace('&', ' ')).strip('-')[:60].strip('-')

def main(db, tsv_dir):
    c = sqlite3.connect(db)
    cols = [r[1] for r in c.execute('pragma table_info(cases)')]
    if 'cn' not in cols:
        c.execute('alter table cases add column cn text')
    c.execute('update cases set cn=null')
    idx = collections.defaultdict(list)
    for rid, s, t, w, r, b in c.execute('select rowid,slug,title,wage,recv,begin from cases'):
        idx[(t, r, b)].append([rid, s, w, False])
    total = matched = 0
    upd = []
    files = sorted(f for f in glob.glob(os.path.join(tsv_dir, '*.tsv')) if not os.path.islink(f))
    seen = set()
    for f in files:
        for line in open(f):
            p = line.rstrip('\n').split('\t')
            if len(p) < 9 or p[0] in seen:
                continue
            seen.add(p[0])
            total += 1
            cands = [x for x in idx.get((p[2], p[7], p[8]), ()) if not x[3]]
            if not cands:
                continue
            bs = base(p[1])
            cands = [x for x in cands if x[1].startswith(bs + '-')]
            if not cands:
                continue
            try:
                w = float(p[3].replace(',', '').replace('$', ''))
                wa = w * MULT.get(p[4], 1)
            except ValueError:
                w = wa = None
            pick = None
            if w is not None:
                for x in cands:
                    if abs(x[2] - wa) <= 1 or abs(x[2] - w) <= 1:
                        pick = x
                        break
            if pick is None:
                pick = cands[0] if len(cands) == 1 else None
            if pick is None:
                continue
            pick[3] = True
            upd.append((p[0], pick[0]))
            matched += 1
    c.executemany('update cases set cn=? where rowid=?', upd)
    c.commit()
    n = c.execute('select count(*) from cases').fetchone()[0]
    have = c.execute('select count(*) from cases where cn is not null').fetchone()[0]
    print(f'raw certified H-1B rows {total:,}; matched {matched:,}; site filings with case number {have:,} of {n:,} ({have / n:.2%})')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
