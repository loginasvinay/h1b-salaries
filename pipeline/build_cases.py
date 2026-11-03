"""Compact per-employer filings shards: /data/cases/<key>.json
{"T":[titles],"L":["City|ST"],"<slug>":[[titleIdx,wage,locIdx,recvDay,beginDay,fy2,case,level,pw]...]}
case = DOL case number: I-200-23355-584372 is stored as the integer 20023355584372 (0 if unknown).
level = DOL wage level 1-4 (0 if not stated); pw = annual prevailing wage (0 if unknown).
Days are counted from 2000-01-01; fy2 is the two-digit fiscal year. Rows sorted by submit date desc."""
import sqlite3,json,os,sys,collections,re,shutil,datetime
DB,SITE=sys.argv[1],sys.argv[2]
EPOCH=datetime.date(2000,1,1)
def day(s):
    if not s: return -1
    try: return (datetime.date.fromisoformat(s[:10])-EPOCH).days
    except ValueError: return -1
def key(s): return re.sub(r'[^a-z0-9]','',s.lower())[:2]
c=sqlite3.connect(DB)
sh=collections.defaultdict(lambda:collections.defaultdict(list))
cols=[r[1] for r in c.execute('pragma table_info(cases)')]
cn_sel='cn' if 'cn' in cols else 'null'
lv_sel='lvl' if 'lvl' in cols else '0'
pw_sel='pw' if 'pw' in cols else 'null'
def cnum(v):
    m=re.fullmatch(r'I-(\d{3})-(\d{5})-(\d{6})',v or '')
    return int(''.join(m.groups())) if m else 0
for s,t,w,ci,st,r,b,fy,cn,lv,pw in c.execute(f'select slug,title,wage,city,state,recv,begin,fy,{cn_sel},{lv_sel},{pw_sel} from cases'):
    sh[key(s)][s].append((t or '',w,(ci or '')+'|'+(st or ''),day(r),day(b),int(fy)%100,cnum(cn),lv or 0,pw or 0))
out=os.path.join(SITE,'data','cases');shutil.rmtree(out,ignore_errors=True);os.makedirs(out)
total=0
for k in sorted(sh):
    T={};L={};d={'T':[],'L':[]}
    for s in sorted(sh[k]):
        rows=sorted(sh[k][s],key=lambda x:(-x[3],x[0],x[1],x[6]))
        enc=[]
        for t,w,l,r,b,fy,cn,lv,pw in rows:
            if t not in T: T[t]=len(d['T']);d['T'].append(t)
            if l not in L: L[l]=len(d['L']);d['L'].append(l)
            enc.append([T[t],w,L[l],r,b,fy,cn,lv,pw])
        d[s]=enc;total+=len(enc)
    json.dump(d,open(f'{out}/{k}.json','w'),separators=(',',':'))
print('rows',total)
