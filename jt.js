/* Employer "Salaries by job title" table: fiscal-year tabs, filter, sort, show-all, and a
   drill-down into the filings table. Data: /data/emp-titles/<fnv1a(slug)%512>.json, rows
   [title, titleSlug, filings, median, min, max, [[c,med]|0 per FY2023..FY2026]]. */
(function(){
'use strict';
var DV='2bc740cdd2';/* data version, set by pipeline/build_pages.py */
var FYS=['2023','2024','2025','2026'],NB=512,STATIC_T=200;
function bucket(s,n){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)>>>0;}return h%n;}
function escH(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString();}
window.H1BBucket=bucket;
window.initJobTitles=function(card){
  card=card||document.getElementById('job-titles');
  if(!card||card.dataset.ready)return;card.dataset.ready='1';
  var slug=card.dataset.slug,box=card.querySelector('#jt-box');
  fetch('/data/emp-titles/'+bucket(slug,NB)+'.json?v='+DV).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
    var rows=d[slug]||[];if(!rows.length)return;
    var fy='ALL',q='',qRaw='',all=false,sortK=2,dir=-1;
    var years=FYS.filter(function(y,i){return rows.some(function(r){return r[6][i];});});
    function view(){
      var i=FYS.indexOf(fy);
      return rows.map(function(r){
        if(fy==='ALL')return {t:r[0],s:r[1],c:r[2],m:r[3],lo:r[4],hi:r[5]};
        var y=r[6][i];return y?{t:r[0],s:r[1],c:y[0],m:y[1]}:null;
      }).filter(function(x){return x&&(!q||x.t.toLowerCase().indexOf(q)>=0);});
    }
    function render(){
      var v=view(),key=['t','c','m'][sortK===0?0:sortK===2?1:2];
      v.sort(function(a,b){var x=a[key],y=b[key];return (typeof x==='number'?x-y:String(x).localeCompare(y))*dir;});
      var shown=all||q?v:v.slice(0,25);
      var tabs='<div class="tabs" role="tablist" aria-label="Fiscal year">'+['ALL'].concat(years.slice().reverse()).map(function(y){
        return '<button type="button" role="tab" class="tab'+(y===fy?' active':'')+'" aria-selected="'+(y===fy)+'" data-fy="'+y+'">'+(y==='ALL'?'All years':'FY'+y)+'</button>';}).join('')+'</div>';
      function th(k,label){return '<th class="sort" tabindex="0" role="button" data-k="'+k+'"'+(sortK===k?' aria-sort="'+(dir>0?'ascending':'descending')+'"':'')+'>'+label+'</th>';}
      var h=tabs+'<input class="search slim" id="jt-q" placeholder="Filter job titles…" aria-label="Filter job titles" value="'+escH(qRaw)+'">'
        +'<div class="tscroll"><table class="dt"><thead><tr>'+th(0,'Job title')+th(2,'Filings')+th(3,'Median salary')+(fy==='ALL'?'<th>Typical range</th>':'')+'<th><span class="sr-only">Filings</span></th></tr></thead><tbody>'
        +shown.map(function(r){
          var name=r.s?'<a href="'+(r.c>=0&&isStatic(r.s)?'/title/'+r.s+'.html':'/title/view.html?t='+r.s)+'">'+escH(r.t)+'</a>':escH(r.t);
          return '<tr><td>'+name+'</td><td>'+r.c.toLocaleString()+'</td><td>'+money(r.m)+'</td>'+(fy==='ALL'?'<td>'+money(r.lo)+' – '+money(r.hi)+'</td>':'')
            +'<td><button type="button" class="linkbtn" data-t="'+escH(r.t)+'" aria-label="See '+escH(r.t)+' filings">Filings ›</button></td></tr>';
        }).join('')+'</tbody></table></div>';
      if(fy==='ALL')h+='<p class="sub">Typical range = 10th to 90th percentile of offered salaries.</p>';
      if(!q&&!all&&v.length>25)h+='<p><button type="button" class="btn ghost" id="jt-all">Show all '+v.length+' job titles</button></p>';
      if(!v.length)h+='<p class="sub">No job titles match.</p>';
      box.innerHTML=h;
      var inp=box.querySelector('#jt-q');
      inp.addEventListener('input',function(){qRaw=inp.value;q=qRaw.trim().toLowerCase();render();var n=box.querySelector('#jt-q');n.focus();n.setSelectionRange(n.value.length,n.value.length);});
      box.querySelectorAll('[data-fy]').forEach(function(b){b.addEventListener('click',function(){fy=b.dataset.fy;render();});});
      box.querySelectorAll('th[data-k]').forEach(function(t){
        function go(){var k=+t.dataset.k;if(sortK===k)dir=-dir;else{sortK=k;dir=k===0?1:-1;}render();}
        t.addEventListener('click',go);t.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
      });
      var a=box.querySelector('#jt-all');if(a)a.addEventListener('click',function(){all=true;render();});
      box.querySelectorAll('button[data-t]').forEach(function(b){b.addEventListener('click',function(){
        if(window.H1BFilings)window.H1BFilings.show(b.dataset.t,fy);
      });});
    }
    // titles with a static page: those listed in titles-top with the flag; fall back to the view page.
    var STATIC={};function isStatic(s){return !!STATIC[s];}
    fetch('/data/titles-top.json?v='+DV).then(function(r){return r.json();}).then(function(t){t.t.forEach(function(x){if(x[3])STATIC[x[1]]=1;});}).catch(function(){}).then(render);
  }).catch(function(){});
};
function boot(){var c=document.getElementById('job-titles');if(c)window.initJobTitles(c);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
