/* Filings table: one row per certified H-1B case.
   Columns: Employer | Job title | Base salary | Location | Submit date |
   Start date. Client-side sortable, 50 rows per page, fiscal-year filter.
   Case rows live in /data/case-shards/<key>.json, keyed by employer slug. */
(function(){
function escH(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString();}
function loc(city,st){if(city&&st)return city+', '+st;return city||st||'—';}
window.initFilings=function(o){
  var box=document.getElementById('filings-box');
  if(!box||box.dataset.done)return;
  box.dataset.done='1';
  var rows=null,sortCol='recv',sortDir=-1,page=1,PER=50,fy='ALL',loaded=false;
  box.innerHTML='<p><button class="btn" id="filings-load">Show all '+o.count.toLocaleString()+' filings</button></p><div id="filings-wrap" style="display:none"></div>';
  var wrap=box.querySelector('#filings-wrap');
  var btn=box.querySelector('#filings-load');
  function load(){
    if(loaded)return;loaded=true;
    btn.disabled=true;btn.textContent='Loading filings…';
    fetch('/data/case-shards/'+o.key+'.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(sh){
      rows=sh[o.slug]||[];
      btn.style.display='none';wrap.style.display='';
      render();
    }).catch(function(){
      loaded=false;btn.disabled=false;btn.textContent='Retry loading filings';
      wrap.innerHTML='<p>Could not load filings. Please try again.</p>';wrap.style.display='';
    });
  }
  btn.addEventListener('click',load);
  if('IntersectionObserver' in window){
    new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){load();ob.disconnect();}},{rootMargin:'200px'}).observe(box);
  }
  function arrow(c){return sortCol===c?(sortDir===1?' ▲':' ▼'):'';}
  function render(){
    var filtered=rows.filter(function(r){return fy==='ALL'||r[6]===fy;});
    var col={title:0,wage:1,loc:2,recv:4,begin:5}[sortCol];
    filtered.sort(function(a,b){
      var av=a[col],bv=b[col];
      if(av==null&&bv==null)return 0;
      if(av==null)return 1;
      if(bv==null)return -1;
      if(typeof av==='number')return (av-bv)*sortDir;
      av=String(av);bv=String(bv);
      return (av<bv?-1:av>bv?1:0)*sortDir;
    });
    var pages=Math.max(1,Math.ceil(filtered.length/PER));
    if(page<1)page=1;
    if(page>pages)page=pages;
    var start=(page-1)*PER,chunk=filtered.slice(start,start+PER);
    var yrs={};rows.forEach(function(r){yrs[r[6]]=1;});
    var opts='<option value="ALL">All fiscal years</option>'+Object.keys(yrs).sort().map(function(y){return '<option value="'+y+'"'+(fy===y?' selected':'')+'>FY'+y+'</option>';}).join('');
    var th=function(c,label){return '<th data-c="'+c+'" style="cursor:pointer;white-space:nowrap">'+label+arrow(c)+'</th>';};
    var h='<p><label>Fiscal year <select id="fy-sel" class="compare" style="width:auto;display:inline-block;margin:0 .5rem">'+opts+'</select></label> '
      +filtered.length.toLocaleString()+' filings</p>'
      +'<table><tr><th>Employer</th>'+th('title','Job title')+th('wage','Base salary')+th('loc','Location')+th('recv','Submit date')+th('begin','Start date')+'</tr>'
      +chunk.map(function(r){
        return '<tr><td>'+escH(o.name)+'</td><td>'+escH(r[0])+'</td><td>'+money(r[1])+'</td><td>'+escH(loc(r[2],r[3]))+'</td><td>'+(r[4]||'—')+'</td><td>'+(r[5]||'—')+'</td></tr>';
      }).join('')+'</table>';
    var pg='<p style="margin-top:.8rem">';
    function pbtn(p,label,dis){return '<button class="tab'+(p===page?' active':'')+'" data-p="'+p+'"'+(dis?' disabled':'')+'>'+label+'</button>';}
    pg+=pbtn(page-1,'‹ Prev',page<=1);
    var lo=Math.max(1,page-3),hi=Math.min(pages,page+3);
    for(var p=lo;p<=hi;p++)pg+=pbtn(p,''+p,false);
    pg+=pbtn(page+1,'Next ›',page>=pages);
    pg+=' <span style="color:var(--text2)">Page '+page+' of '+pages+' · showing '+(filtered.length?start+1:0)+'–'+Math.min(start+PER,filtered.length)+' of '+filtered.length.toLocaleString()+'</span></p>';
    wrap.innerHTML=h+pg;
    wrap.querySelectorAll('th[data-c]').forEach(function(t){
      t.addEventListener('click',function(){
        var c=t.dataset.c;
        if(sortCol===c)sortDir=-sortDir;else{sortCol=c;sortDir=(c==='wage'||c==='recv'||c==='begin')?-1:1;}
        page=1;render();
      });
    });
    wrap.querySelectorAll('button[data-p]').forEach(function(b){
      b.addEventListener('click',function(){if(!b.disabled){page=+b.dataset.p;render();}});
    });
    var sel=wrap.querySelector('#fy-sel');
    sel.addEventListener('change',function(){fy=sel.value;page=1;render();});
  }
};
})();
