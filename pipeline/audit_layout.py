"""Responsive audit: horizontal overflow, small tap targets, tiny text, at phone/tablet/desktop widths.
python3 pipeline/audit_layout.py http://localhost:8765 [screenshot_dir]"""
import sys,os,json
from playwright.sync_api import sync_playwright
B=sys.argv[1].rstrip('/');SHOT=sys.argv[2] if len(sys.argv)>2 else None
PAGES=['/','/employer/google-llc-google.html','/employer/view.html?e=cravath-swaine-moore-llp-cravat','/title/software-engineer.html',
 '/titles/','/employers/','/sponsors.html','/roles/','/role/15-1252.html','/cities/','/city/seattle-wa.html','/states/','/state/CA.html',
 '/perm.html','/perm/trends.html','/perm/denials.html','/compare.html','/about.html','/disclaimer.html','/privacy.html']
JS='''()=>{const vw=document.documentElement.clientWidth,out={sw:document.documentElement.scrollWidth,vw,over:[],tap:[],tiny:[]};
for(const e of document.querySelectorAll('body *')){const r=e.getBoundingClientRect();if(!r.width||getComputedStyle(e).visibility==='hidden')continue;
 if(r.right>vw+1&&!e.closest('.tscroll,.tabs,nav,header,.disc-banner')){let p=e.parentElement,sc=false;while(p){const o=getComputedStyle(p).overflowX;if(o==='auto'||o==='scroll'){sc=true;break;}p=p.parentElement;}
   if(!sc)out.over.push(e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.split(' ')[0]:'')+' r='+Math.round(r.right));}
 if(e.matches('a,button,input,select,[role=button]')&&(r.height<32||r.width<32)&&!e.closest('p,td,li,.note,footer,.crumbs,.disc-banner p'))out.tap.push((e.textContent||e.tagName).trim().slice(0,25)+' '+Math.round(r.width)+'x'+Math.round(r.height));
 if(e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&parseFloat(getComputedStyle(e).fontSize)<12)out.tiny.push(e.tagName+':'+e.textContent.trim().slice(0,20));}
out.over=[...new Set(out.over)].slice(0,8);out.tap=[...new Set(out.tap)].slice(0,8);out.tiny=[...new Set(out.tiny)].slice(0,5);return out;}'''
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for w,h,name in [(375,812,'phone'),(768,1024,'tablet'),(1280,900,'desktop')]:
        ctx=b.new_context(viewport={'width':w,'height':h},is_mobile=w<700,has_touch=w<700,device_scale_factor=2 if w<700 else 1)
        pg=ctx.new_page()
        for u in PAGES:
            pg.goto(B+u);pg.wait_for_timeout(900)
            r=pg.evaluate(JS)
            flag='OVERFLOW' if r['sw']>r['vw'] else 'ok'
            if flag!='ok' or r['over'] or (name=='phone' and r['tap']):
                print(f"{name:7} {u:58} {flag} sw={r['sw']} vw={r['vw']}\n   over={r['over']}\n   tap={r['tap'] if name=='phone' else ''} tiny={r['tiny']}")
            if SHOT and name=='phone' and u in ('/','/employer/google-llc-google.html','/compare.html','/perm/trends.html','/sponsors.html'):
                pg.screenshot(path=f"{SHOT}/m_{u.strip('/').replace('/','_').replace('.html','') or 'home'}.png")
        ctx.close()
    b.close()
