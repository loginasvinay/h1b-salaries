"""Rebuild lca.db from the deploy repo's shards (bootstrap until raw DOL files are available)."""
import json,sqlite3,os,sys,glob
SITE=sys.argv[1]; DB=sys.argv[2]
if os.path.exists(DB): os.remove(DB)
c=sqlite3.connect(DB); c.execute('pragma journal_mode=off'); c.execute('pragma synchronous=off')
c.execute('create table emp(slug text primary key,name text,cnt int,p10 int,p25 int,p50 int,p75 int,p90 int,pw int,score text,roles text,qtr text)')
c.execute('create table cases(slug text,title text,wage int,city text,state text,recv text,begin text,fy text,cn text)')
n=0
for f in sorted(glob.glob(SITE+'/data/emp-shards/*.json')):
    for s,e in json.load(open(f)).items():
        p=e['p']+[None]*(5-len(e['p']))
        c.execute('insert into emp values(?,?,?,?,?,?,?,?,?,?,?,?)',(s,e['n'],e['c'],*p[:5],e.get('w'),json.dumps(e.get('s')),json.dumps(e.get('r')),json.dumps(e.get('q'))))
import datetime
EPOCH=datetime.date(2000,1,1)
dd=lambda d:None if d<0 else (EPOCH+datetime.timedelta(days=d)).isoformat()
for f in sorted(glob.glob(SITE+'/data/cases/*.json')):
    sh=json.load(open(f)); T,L=sh.pop('T'),sh.pop('L')
    for s,rows in sh.items():
        recs=[]
        for row in rows:
            t,w,l,r,b,fy=row[:6]; cn=row[6] if len(row)>6 else 0
            ci,st=L[l].split('|')
            s14=str(cn).zfill(14) if cn else None
            recs.append((s,T[t],w,ci,st,dd(r),dd(b),str(2000+fy),f'I-{s14[:3]}-{s14[3:8]}-{s14[8:]}' if s14 else None))
        c.executemany('insert into cases values(?,?,?,?,?,?,?,?,?)',recs); n+=len(recs)
c.execute('create index ix_c on cases(slug)'); c.commit()
print('employers',c.execute('select count(*) from emp').fetchone()[0],'cases',n,'distinct titles',c.execute('select count(distinct lower(title)) from cases').fetchone()[0])
