"""Build search index + job-title data + per-employer job-title tables from lca.db.
Outputs (under SITE/data/): sx/<k>.json, title-shards/<k>.json, emp-titles/<k>.json, titles-top.json"""
import sqlite3,json,os,sys,collections,re,statistics,glob,shutil
sys.path.insert(0,os.path.dirname(__file__))
from titles import norm,pretty,slug
DB,SITE=sys.argv[1],sys.argv[2]
FYS=['2023','2024','2025','2026']
STOP={'inc','llc','corp','corporation','co','ltd','limited','the','of','and','lp','llp','pllc','pc','pa','na','us','usa','company','l','p','a','dba','d','b'}
def key(s): s=re.sub(r'[^a-z0-9]','',s.lower()); return s[:2]
def bucket(s,n):
    h=2166136261
    for ch in s.encode(): h=((h^ch)*16777619)&0xffffffff
    return h%n
NB_T,NB_E=256,512
STATIC_T=200   # titles with this many filings get a static page
def pct(v,q):
    if not v: return None
    i=(len(v)-1)*q; lo=int(i); hi=min(lo+1,len(v)-1); return round(v[lo]+(v[hi]-v[lo])*(i-lo))
def stats(v):
    v=sorted(v); return [pct(v,.1),pct(v,.25),pct(v,.5),pct(v,.75),pct(v,.9)]
c=sqlite3.connect(DB)
emp={s:(n,cnt) for s,n,cnt in c.execute('select slug,name,cnt from emp')}
static_emp={os.path.basename(f)[:-5] for f in glob.glob(SITE+'/employer/*.html')}-{'view'}
# ---- pass over cases
T_w=collections.defaultdict(list); T_var=collections.defaultdict(collections.Counter)
T_fy=collections.defaultdict(lambda:collections.defaultdict(list))
T_emp=collections.defaultdict(lambda:collections.defaultdict(list))
T_city=collections.defaultdict(lambda:collections.defaultdict(list))
E_t=collections.defaultdict(lambda:collections.defaultdict(lambda:collections.defaultdict(list)))
for s,t,w,city,st,fy in c.execute('select slug,title,wage,city,state,fy from cases'):
    n=norm(t)
    if not n: continue
    T_var[n][t]+=1; T_w[n].append(w); T_fy[n][fy].append(w); T_emp[n][s].append(w)
    if city: T_city[n][(city.title(),st)].append(w)
    E_t[s][n]['ALL'].append(w); E_t[s][n][fy].append(w)
print('titles',len(T_w))
title_slug={};title_disp={}
for n in T_w:
    title_slug[n]=slug(n); title_disp[n]=pretty(T_var[n])
def outdir(d):
    p=os.path.join(SITE,'data',d); shutil.rmtree(p,ignore_errors=True); os.makedirs(p); return p
# ---- title data shards (titles with >=5 filings)
TD=collections.defaultdict(dict); MIN_T=5
for n,ws in T_w.items():
    if len(ws)<MIN_T: continue
    sl=title_slug[n]
    emps=sorted(T_emp[n].items(),key=lambda kv:(-len(kv[1]),kv[0]))[:50]
    cities=sorted(T_city[n].items(),key=lambda kv:(-len(kv[1]),kv[0]))[:20]
    TD[bucket(sl,NB_T)][sl]={'n':title_disp[n],'c':len(ws),'p':stats(ws),
        'y':{fy:[len(v),stats(v)[2]] for fy,v in sorted(T_fy[n].items())},
        'e':[[s,emp[s][0],len(v),stats(v)[2],1 if s in static_emp else 0] for s,v in emps],
        'l':[[ci,st,len(v),stats(v)[2]] for (ci,st),v in cities]}
p=outdir('title-shards')
for k,d in TD.items(): json.dump(d,open(f'{p}/{k}.json','w'),separators=(',',':'),sort_keys=True)
# ---- per-employer job-title tables (top 150 titles)
ED=collections.defaultdict(dict)
for s,tt in E_t.items():
    rows=[]
    for n,d in sorted(tt.items(),key=lambda kv:(-len(kv[1]['ALL']),kv[0]))[:150]:
        a=sorted(d['ALL']); sl=title_slug[n]
        st_=stats(a)
        rows.append([title_disp[n],sl if len(T_w[n])>=MIN_T else '',len(a),st_[2],st_[0],st_[4],
                     [[len(d[f]),stats(d[f])[2]] if d.get(f) else 0 for f in FYS]])
    ED[bucket(s,NB_E)][s]=rows
p=outdir('emp-titles')
for k,d in ED.items(): json.dump(d,open(f'{p}/{k}.json','w'),separators=(',',':'),sort_keys=True)
# ---- search index: token-prefix shards. entry = [type, name, slug, count, median, static]
SX=collections.defaultdict(list)
def toks(name): return [w for w in re.findall(r'[a-z0-9]+',name.lower()) if w not in STOP and len(w)>=2]
emed={s:m for s,m in c.execute('select slug,p50 from emp')}
for s,(n,cnt) in emp.items():
    e=['e',n,s,cnt,emed.get(s),1 if s in static_emp else 0]
    for k in sorted({key(w) for w in toks(n)} or {key(s)}): SX[k].append(e)
for n,ws in T_w.items():
    if len(ws)<MIN_T: continue
    e=['t',title_disp[n],title_slug[n],len(ws),stats(ws)[2],1 if len(ws)>=STATIC_T else 0]
    for k in {key(w) for w in n.split() if len(w)>=2}: SX[k].append(e)
p=outdir('sx'); SPLIT=100_000; nfiles=0
def dump(name,lst):
    global nfiles; nfiles+=1; json.dump(lst,open(f'{p}/{name}.json','w'),separators=(',',':'))
def tok3(e,k2):
    # 3-char prefixes of the entry's tokens that start with k2
    src=e[1].lower() if e[0]=='e' else e[1].lower()
    return {w[:3] for w in re.findall(r'[a-z0-9]+',src) if w.startswith(k2) and len(w)>=3}
splits=[]
for k,lst in sorted(SX.items()):
    lst.sort(key=lambda e:(-e[3],e[0],e[2]))
    if len(json.dumps(lst,separators=(',',':')))<=SPLIT: dump(k,lst); continue
    splits.append(k); dump(k,lst[:300])          # 2-char query: best 300 only
    sub=collections.defaultdict(list)
    for e in lst:
        for k3 in tok3(e,k): sub[k3].append(e)
    for k3,l3 in sorted(sub.items()): dump(k3,l3[:4000])
json.dump(sorted(splits),open(SITE+'/data/sx-split.json','w'))
print('sx files',nfiles,'split keys',len(splits))
# top lists for fuzzy fallback + static title page list
top_t=sorted(((len(ws),n) for n,ws in T_w.items() if len(ws)>=MIN_T),reverse=True)
json.dump({'t':[[title_disp[n],title_slug[n],c_,1 if c_>=STATIC_T else 0] for c_,n in top_t[:3000]]},open(SITE+'/data/titles-top.json','w'),separators=(',',':'))
print('title shards',sum(len(d) for d in TD.values()),'emp-title rows',sum(len(d) for d in ED.values()),'sx entries',sum(len(l) for l in SX.values()))
