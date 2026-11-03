/* Filings table: one row per certified H-1B case.
   Columns: Case number | Job title | Wage level | Base salary | Prevailing wage | Location | Submit date | Start date.
   (The employer is the page itself, so it is not repeated on every row.)
   Fiscal-year tabs, text filter (job title or city), sortable, 50 rows per page.
   Data: /data/cases/<key>.json  {"T":[titles],"L":["City|ST"],"<slug>":[[t,wage,l,recvDay,beginDay,fy2,case,level,pw]]}
   case: DOL case number packed as digits (20023355584372 -> I-200-23355-584372), 0 when unknown.
   (days since 2000-01-01). Loads only when the section is opened or scrolled into view,
   or right away when the URL carries ?t=<job title>. */
(function(){
'use strict';
var DV='2bc740cdd2';/* data version, set by pipeline/build_pages.py */
function escH(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString();}
var EPOCH=Date.UTC(2000,0,1);
function dstr(d){if(d<0)return '—';return new Date(EPOCH+d*864e5).toISOString().slice(0,10);}
function caseNo(n){if(!n)return '';var s=String(n);while(s.length<14)s='0'+s;return 'I-'+s.slice(0,3)+'-'+s.slice(3,8)+'-'+s.slice(8);}
function loc(l){var p=l.split('|');if(p[0]&&p[1])return p[0]+', '+p[1];return p[0]||p[1]||'—';}
var api={pending:null};
var LV=['—','I','II','III','IV'];
window.H1BFilings={show:function(title,fy){
  var card=document.getElementById('filings');if(card)card.scrollIntoView({behavior:'smooth',block:'start'});
  if(api.apply)api.apply(title,fy);else api.pending=[title,fy];
}};
window.initFilings=function(o){
  var box=document.getElementById('filings-box');
  if(!box||box.dataset.done)return;
  box.dataset.done='1';
  var rows=null,T=null,L=null,sortCol='recv',sortDir=-1,page=1,PER=50,fy='ALL',lv='ALL',q='',qRaw='',loaded=false;
  var pre='';try{pre=new URLSearchParams(location.search).get('t')||'';}catch(e){}
  if(pre){qRaw=pre;q=pre.toLowerCase();}
  box.innerHTML='<p><button class="btn" id="filings-load">Show all '+o.count.toLocaleString()+' filings</button></p><div id="filings-wrap" style="display:none"></div>';
  var wrap=box.querySelector('#filings-wrap'),btn=box.querySelector('#filings-load');
  function load(){
    if(loaded)return;loaded=true;
    btn.disabled=true;btn.textContent='Loading filings…';
    fetch('/data/cases/'+o.key+'.json?v='+DV).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(sh){
      T=sh.T;L=sh.L;rows=(sh[o.slug]||[]).map(function(r){return {t:T[r[0]],w:r[1],l:loc(L[r[2]]),r:r[3],b:r[4],fy:String(2000+r[5]),c:caseNo(r[6]),v:r[7]||0,p:r[8]||null};});
      btn.style.display='none';wrap.style.display='';
      render(false);
    }).catch(function(){
      loaded=false;btn.disabled=false;btn.textContent='Retry loading filings';
      wrap.innerHTML='<p>Could not load filings. Please try again.</p>';wrap.style.display='';
    });
  }
  api.apply=function(title,f){qRaw=String(title||'');q=qRaw.trim().toLowerCase();if(f)fy=f;page=1;if(rows)render(false);else load();};
  if(api.pending){api.apply.apply(null,api.pending);api.pending=null;}
  btn.addEventListener('click',load);
  if(pre)load();
  else if('IntersectionObserver' in window){
    new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){load();ob.disconnect();}},{rootMargin:'200px'}).observe(box);
  }
  function arrow(c){return sortCol===c?(sortDir===1?' ▲':' ▼'):'';}
  function render(keepFocus){
    var filtered=rows.filter(function(r){
      return (fy==='ALL'||r.fy===fy)&&(lv==='ALL'||String(r.v)===lv)&&(!q||r.t.toLowerCase().indexOf(q)>=0||r.l.toLowerCase().indexOf(q)>=0||r.c.toLowerCase().indexOf(q)>=0);
    });
    var col={title:'t',wage:'w',loc:'l',recv:'r',begin:'b',cno:'c',lvl:'v',pw:'p'}[sortCol];
    filtered.sort(function(a,b){
      var av=a[col],bv=b[col];
      if(av==null&&bv==null)return 0;if(av==null)return 1;if(bv==null)return -1;
      if(typeof av==='number')return ((av<0?-1e9:av)-(bv<0?-1e9:bv))*sortDir;
      return (av<bv?-1:av>bv?1:0)*sortDir;
    });
    var pages=Math.max(1,Math.ceil(filtered.length/PER));
    if(page<1)page=1;if(page>pages)page=pages;
    var start=(page-1)*PER,chunk=filtered.slice(start,start+PER);
    var yrs={};rows.forEach(function(r){yrs[r.fy]=1;});
    var tabs='<div class="tabs" role="tablist" aria-label="Fiscal year">'+['ALL'].concat(Object.keys(yrs).sort().reverse()).map(function(y){
      return '<button type="button" role="tab" class="tab'+(y===fy?' active':'')+'" aria-selected="'+(y===fy)+'" data-fy="'+y+'">'+(y==='ALL'?'All years':'FY'+y)+'</button>';}).join('')+'</div>';
    var th=function(c,label){return '<th class="sort" tabindex="0" role="button" data-c="'+c+'"'+(sortCol===c?' aria-sort="'+(sortDir>0?'ascending':'descending')+'"':'')+'>'+label+arrow(c)+'</th>';};
    var h=tabs+'<div class="toolbar"><input class="search slim" id="f-q" placeholder="Filter by job title, city or case number…" aria-label="Filter filings by job title, city or case number" value="'+escH(qRaw)+'">'
      +'<label class="sub">Wage level <select id="f-lv" class="lv-sel" aria-label="Filter by wage level">'+[['ALL','All'],['1','Level I'],['2','Level II'],['3','Level III'],['4','Level IV'],['0','Not stated']].map(function(o){return '<option value="'+o[0]+'"'+(o[0]===lv?' selected':'')+'>'+o[1]+'</option>';}).join('')+'</select></label>'
      +'<span class="sub">'+filtered.length.toLocaleString()+' filings'+(q?' matching “'+escH(q)+'” <button type="button" class="linkbtn" id="f-clear">clear</button>':'')+'</span></div>'
      +'<div class="tscroll"><table class="dt filings"><thead><tr>'+th('cno','Case number')+th('title','Job title')+th('lvl','Wage level')+th('wage','Base salary')+th('pw','Prevailing wage')+th('loc','Location')+th('recv','Submit date')+th('begin','Start date')+'</tr></thead><tbody>'
      +chunk.map(function(r){
        return '<tr><td class="cno">'+(r.c||'—')+'</td><td>'+escH(r.t)+'</td><td class="lv">'+LV[r.v]+'</td><td>'+money(r.w)+'</td><td>'+money(r.p)+'</td><td>'+escH(r.l)+'</td><td>'+dstr(r.r)+'</td><td>'+dstr(r.b)+'</td></tr>';
      }).join('')+'</tbody></table></div>';
    var pg='<nav class="pager" aria-label="Filings pages">';
    function pbtn(p,label,dis){return '<button type="button" class="tab'+(p===page?' active':'')+'" data-p="'+p+'"'+(dis?' disabled':'')+(p===page?' aria-current="page"':'')+'>'+label+'</button>';}
    pg+=pbtn(page-1,'‹ Prev',page<=1);
    var lo=Math.max(1,page-3),hi=Math.min(pages,page+3);
    for(var p=lo;p<=hi;p++)pg+=pbtn(p,''+p,false);
    pg+=pbtn(page+1,'Next ›',page>=pages);
    pg+=' <span class="sub">Page '+page+' of '+pages.toLocaleString()+' · showing '+(filtered.length?start+1:0)+'–'+Math.min(start+PER,filtered.length)+' of '+filtered.length.toLocaleString()+'</span></nav>';
    wrap.innerHTML=h+pg;
    var inp=wrap.querySelector('#f-q');
    inp.addEventListener('input',function(){qRaw=inp.value;q=qRaw.trim().toLowerCase();page=1;render(true);});
    if(keepFocus){inp.focus();inp.setSelectionRange(inp.value.length,inp.value.length);}
    var lsel=wrap.querySelector('#f-lv');lsel.addEventListener('change',function(){lv=lsel.value;page=1;render(false);});
    var clr=wrap.querySelector('#f-clear');if(clr)clr.addEventListener('click',function(){q='';qRaw='';page=1;render(false);});
    wrap.querySelectorAll('[data-fy]').forEach(function(b){b.addEventListener('click',function(){fy=b.dataset.fy;page=1;render(false);});});
    wrap.querySelectorAll('th[data-c]').forEach(function(t){
      function go(){var c=t.dataset.c;if(sortCol===c)sortDir=-sortDir;else{sortCol=c;sortDir=(c==='wage'||c==='recv'||c==='begin'||c==='pw'||c==='lvl')?-1:1;}page=1;render(false);}
      t.addEventListener('click',go);t.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
    });
    wrap.querySelectorAll('button[data-p]').forEach(function(b){
      b.addEventListener('click',function(){if(!b.disabled){page=+b.dataset.p;render(false);}});
    });
  }
};
})();
