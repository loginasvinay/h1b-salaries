"""Job-title normalization shared by the pipeline."""
import re
ABBR={'sr':'senior','snr':'senior','jr':'junior','mgr':'manager','engr':'engineer','eng':'engineer','dev':'developer',
      'assoc':'associate','asst':'assistant','admin':'administrator','dir':'director','vp':'vice president','sw':'software',
      'tech':'technical','mgmt':'management','prof':'professor','spec':'specialist','coord':'coordinator','arch':'architect'}
ROMAN={'1':'i','2':'ii','3':'iii','4':'iv','5':'v'}
def norm(t):
    t=(t or '').lower().replace('&',' and ')
    t=re.sub(r'\bjc\s?\d+\b.*$','',t)            # Deloitte-style job codes
    t=re.sub(r'\(.*?\)','',t)
    t=re.sub(r'[^a-z0-9+# ]+',' ',t)
    w=[ABBR.get(x,x) for x in t.split()]
    if w and w[-1] in ROMAN: w[-1]=ROMAN[w[-1]]   # "engineer 2" == "engineer ii"
    return ' '.join(w).strip()
def slug(n):
    return re.sub(r'[^a-z0-9]+','-',n).strip('-')[:80]
def pretty(variants):
    """Pick the display form: most common original spelling, fixed up if shouty."""
    clean={}
    for v,k in variants.items():
        v=re.sub(r'\s*\bJC\s?\d+\b.*$','',v,flags=re.I); v=re.sub(r'\(.*?\)','',v).strip(' -,')
        if v: clean[v]=clean.get(v,0)+k
    best=max(clean.items(),key=lambda kv:(kv[1],kv[0]))[0].strip() if clean else max(variants,key=lambda v:(variants[v],v))
    if best.isupper() or best.islower():
        small={'and','of','in','for','the','to','at','on','a'}
        ws=best.lower().split()
        best=' '.join(x if (i and x in small) else (x.upper() if x in ('ii','iii','iv','vp','it','qa','ui','ux','ai','ml','sap','hr','ceo','cto','cfo','sre','etl','bi','erp') else x.capitalize()) for i,x in enumerate(ws))
    return re.sub(r'\s+',' ',best)
