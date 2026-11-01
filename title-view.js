/* Long-tail job-title profile (/title/view.html?t=<slug>), rendered from
   /data/title-shards/<fnv1a(slug)%256>.json. Never navigates away on a miss. */
(function(){
'use strict';
function bucket(s,n){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)>>>0;}return h%n;}
function escH(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString();}
var box=document.getElementById('t-view');if(!box)return;
var slug='';try{slug=(new URLSearchParams(location.search).get('t')||'').trim();}catch(e){}
if(!slug){box.innerHTML='<h1>Job titles</h1><p>Pick a job title from <a href="/">search</a> or <a href="/titles/">the job title list</a>.</p>';return;}
fetch('/data/title-shards/'+bucket(slug,256)+'.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
  var t=d[slug];
  if(!t){box.innerHTML='<h1>Job title not found</h1><p>No H-1B filings found for “'+escH(slug)+'”. Try <a href="/?q='+encodeURIComponent(slug.replace(/-/g,' '))+'">searching for it</a>.</p>';return;}
  var p=t.p;
  document.title=t.n+' H-1B Salary — Median Pay by Employer & City';
  var md=document.querySelector('meta[name="description"]');if(md)md.content=t.n+' H-1B salary: median '+money(p[2])+' across '+t.c.toLocaleString()+' certified filings.';
  var cells=[[t.c.toLocaleString(),'certified filings'],[money(p[2]),'Median base salary'],[money(p[1]),'25th pct'],[money(p[3]),'75th pct'],[money(p[4]),'90th pct'],[money(p[0]),'10th pct']];
  var ys=Object.keys(t.y).sort().reverse();
  var h='<nav class="crumbs"><a href="/">Home</a> › <a href="/titles/">Job titles</a> › '+escH(t.n)+'</nav>'
    +'<h1>'+escH(t.n)+' H-1B Salary</h1>'
    +'<p class="lede">'+t.c.toLocaleString()+' certified H-1B filings list the job title <strong>'+escH(t.n)+'</strong> (FY2023–FY2026). The median offered base salary is <strong>'+money(p[2])+'</strong>.</p>'
    +'<div class="stats">'+cells.map(function(c){return '<div class="stat"><div class="v">'+c[0]+'</div><div class="l">'+c[1]+'</div></div>';}).join('')+'</div>'
    +'<div class="note">Estimates from public U.S. Department of Labor records — wages are employer-attested <em>offered</em> wages, not verified salaries paid; counts are filings, not people. Not legal, financial, or career advice. See our <a href="/disclaimer.html">disclaimer &amp; terms</a>.</div>'
    +'<div class="grid2"><div class="card"><h2>Salary by fiscal year</h2><table class="dt"><thead><tr><th>Year</th><th>Filings</th><th>Median</th></tr></thead><tbody>'
    +ys.map(function(y){return '<tr><td>FY'+y+'</td><td>'+t.y[y][0].toLocaleString()+'</td><td>'+money(t.y[y][1])+'</td></tr>';}).join('')+'</tbody></table></div>'
    +'<div class="card"><h2>Top cities</h2><table class="dt"><thead><tr><th>City</th><th>Filings</th><th>Median</th></tr></thead><tbody>'
    +t.l.map(function(l){return '<tr><td>'+escH(l[0])+', '+escH(l[1])+'</td><td>'+l[2].toLocaleString()+'</td><td>'+money(l[3])+'</td></tr>';}).join('')+'</tbody></table></div></div>'
    +'<div class="card"><h2>'+escH(t.n)+' salary by employer</h2><table class="dt sortable"><thead><tr><th>Employer</th><th>Filings</th><th>Median salary</th></tr></thead><tbody>'
    +t.e.map(function(e){var href=e[4]?'/employer/'+e[0]+'.html':'/employer/view.html?e='+encodeURIComponent(e[0]);return '<tr><td><a href="'+href+'">'+escH(e[1])+'</a></td><td>'+e[2].toLocaleString()+'</td><td>'+money(e[3])+'</td></tr>';}).join('')
    +'</tbody></table></div>';
  box.innerHTML=h;
  if(window.H1BTable)window.H1BTable.init(box);
}).catch(function(){box.innerHTML='<h1>Job title</h1><p>Could not load this job title. Please try again or use <a href="/">search</a>.</p>';});
})();
