"""places.json for search: static city + state pages, parsed from their index pages."""
import re,json,sys
SITE=sys.argv[1];out=[]
num=lambda s:int(re.sub(r'[^0-9]','',s) or 0)
for s,n,c,m in re.findall(r'<tr><td><a href="/city/([^"]+)\.html">([^<]+)</a></td><td>([^<]*)</td><td>([^<]*)</td>',open(SITE+'/cities/index.html').read()):
    out.append(['c',n.replace('&amp;','&'),s,num(c),num(m) or None,1])
t=open(SITE+'/states/index.html').read()
for s,n in re.findall(r'<a href="/state/([A-Z]{2})\.html">([^<]+)</a>',t):
    if not any(o[0]=='s' and o[2]==s for o in out): out.append(['s',n,s,0,None,1])
json.dump(out,open(SITE+'/data/places.json','w'),separators=(',',':'));print('places',len(out))
