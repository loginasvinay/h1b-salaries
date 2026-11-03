/* Site search: employers (all 121k), job titles, occupations, cities, states.
   Index: /data/sx/<2|3-char prefix>.json, entries [type, name, slug, count, median, static].
   A query matches an entry when every query word is a prefix of some word in its name.
   Built by pipeline/build_search.py. */
(function(){
'use strict';
var DV='a841fd90e9';/* data version, set by pipeline/build_pages.py */
var SX={},SPLIT=null,EXTRA=null,TOP=null;
var STOP={inc:1,llc:1,corp:1,corporation:1,co:1,ltd:1,limited:1,the:1,of:1,and:1,lp:1,llp:1,pllc:1,pc:1,pa:1,na:1,us:1,usa:1,company:1};
function getJSON(u){return fetch(u+(u.indexOf('?')<0?'?':'&')+'v='+DV).then(function(r){if(!r.ok)throw new Error(r.status);return r.json();});}
function words(s){return (s.toLowerCase().match(/[a-z0-9+#]+/g)||[]);}
function escH(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function money(v){return v==null?'':'$'+Math.round(v).toLocaleString();}
function loadSplit(){if(!SPLIT)SPLIT=getJSON('/data/sx-split.json').then(function(a){var o={};a.forEach(function(k){o[k]=1;});return o;}).catch(function(){return {};});return SPLIT;}
function shardFor(tok){
  return loadSplit().then(function(sp){
    var k2=tok.slice(0,2),k=(tok.length>=3&&sp[k2])?tok.slice(0,3):k2;
    if(!SX[k])SX[k]=getJSON('/data/sx/'+k+'.json').catch(function(){return [];});
    return SX[k];
  });
}
function loadExtra(){
  if(!EXTRA)EXTRA=getJSON('/data/search.json').then(function(d){
    var out=[];
    (d.roles||[]).forEach(function(r){out.push(['o',r.t,r.s,r.c,null,1]);});
    return getJSON('/data/places.json').then(function(p){return out.concat(p);}).catch(function(){return out;});
  }).catch(function(){return [];});
  return EXTRA;
}
function link(e){
  switch(e[0]){
    case 'e':return e[5]?'/employer/'+e[2]+'.html':'/employer/view.html?e='+encodeURIComponent(e[2]);
    case 't':return e[5]?'/title/'+e[2]+'.html':'/title/view.html?t='+encodeURIComponent(e[2]);
    case 'o':return '/role/'+e[2]+'.html';
    case 'c':return '/city/'+e[2]+'.html';
    case 's':return '/state/'+e[2]+'.html';
  }
  return '/';
}
function matches(e,qw){
  var ew=e._w||(e._w=words(e[1]));
  for(var i=0;i<qw.length;i++){
    var ok=false;
    for(var j=0;j<ew.length;j++){if(ew[j].lastIndexOf(qw[i],0)===0){ok=true;break;}}
    if(!ok)return false;
  }
  return true;
}
function score(e,q,qw){
  var n=e[1].toLowerCase().replace(/[^a-z0-9+# ]+/g,' ').replace(/\s+/g,' ').trim(),s=0;
  if(n===q)s+=1000;else if(n.lastIndexOf(q,0)===0)s+=400;
  var ew=e._w||words(e[1]);
  if(ew.length&&ew[0].lastIndexOf(qw[0],0)===0)s+=150;
  // occupations/states aggregate whole categories, so their counts dwarf real titles and employers
  s+=({t:20,e:20,c:10,o:-60,s:-60})[e[0]]||0;
  return s+Math.log(1+e[3])*22;
}
function lookup(q){
  var qw=words(q).filter(function(w){return !STOP[w];});
  if(!qw.length)qw=words(q);
  if(!qw.length)return Promise.resolve({q:q,items:[]});
  var lead=qw.slice().sort(function(a,b){return b.length-a.length;})[0];
  return Promise.all([shardFor(lead),loadExtra()]).then(function(r){
    var seen={},items=[];
    r[0].concat(r[1]).forEach(function(e){
      var id=e[0]+e[2];if(seen[id]||!matches(e,qw))return;seen[id]=1;
      items.push({e:e,s:score(e,q.toLowerCase().trim(),qw)});
    });
    items.sort(function(a,b){return b.s-a.s;});
    if(items.length||qw.length<2)return {q:q,items:items,qw:qw};
    return combo(qw).then(function(c){return {q:q,items:[],combo:c,qw:qw};});
  });
}
/* "google software engineer" -> best employer for one part + best title for the rest */
function combo(qw){
  var tries=[];
  for(var i=1;i<qw.length;i++){
    tries.push([qw.slice(0,i),qw.slice(i)]);tries.push([qw.slice(i),qw.slice(0,i)]);
  }
  function best(ws,type){
    var lead=ws.slice().sort(function(a,b){return b.length-a.length;})[0];
    return shardFor(lead).then(function(list){
      var top=null;list.forEach(function(e){if(e[0]===type&&matches(e,ws)&&(!top||e[3]>top[3]))top=e;});return top;
    });
  }
  return Promise.all(tries.map(function(t){return Promise.all([best(t[0],'e'),best(t[1],'t')]);})).then(function(rs){
    var b=null;rs.forEach(function(r){if(r[0]&&r[1]&&(!b||r[0][3]+r[1][3]>b[0][3]+b[1][3]))b=r;});return b;
  });
}
/* typo fallback against the top employers + titles */
function lev(a,b){
  if(Math.abs(a.length-b.length)>2)return 9;
  var p=[],i,j;for(j=0;j<=b.length;j++)p[j]=j;
  for(i=1;i<=a.length;i++){var c=[i];for(j=1;j<=b.length;j++)c[j]=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));p=c;}
  return p[b.length];
}
function fuzzy(q){
  if(!TOP)TOP=Promise.all([getJSON('/data/search.json'),getJSON('/data/titles-top.json')]).then(function(r){
    var out=[];r[0].employers.forEach(function(e){out.push(['e',e.n,e.s,e.c,null,1]);});
    r[1].t.forEach(function(t){out.push(['t',t[0],t[1],t[2],null,t[3]||0]);});return out;
  }).catch(function(){return [];});
  q=q.toLowerCase().replace(/[^a-z0-9 ]+/g,'');
  return TOP.then(function(list){
    var tol=q.length<=4?1:2,hits=[];
    list.forEach(function(e){
      var n=e[1].toLowerCase().replace(/[^a-z0-9 ]+/g,''),d=lev(q,n.slice(0,q.length));
      if(d<=tol)hits.push({e:e,s:-d*1000+Math.log(1+e[3])});
    });
    hits.sort(function(a,b){return b.s-a.s;});return hits.slice(0,6);
  });
}
var LABEL={t:'Job titles',e:'Employers',o:'Occupations',c:'Cities',s:'States'};
var ORDER=['t','e','o','c','s'],CAP={t:6,e:8,o:3,c:3,s:2};
function row(e,i){
  var meta=e[3]?e[3].toLocaleString()+' filings':'';
  if(e[4])meta+=' · median '+money(e[4]);
  return '<a role="option" id="sr-'+i+'" href="'+link(e)+'"><span class="n">'+escH(e[1])+'</span><span class="c">'+meta+'</span></a>';
}
window.H1BSearch={
  attach:function(input,box){
    var seq=0,active=-1,timer=null;
    input.setAttribute('role','combobox');input.setAttribute('aria-autocomplete','list');
    input.setAttribute('aria-controls',box.id);input.setAttribute('aria-expanded','false');
    box.setAttribute('role','listbox');
    function opts(){return box.querySelectorAll('a[role=option]');}
    function setActive(i){
      var o=opts();if(!o.length)return;
      active=(i+o.length)%o.length;
      for(var k=0;k<o.length;k++)o[k].classList.toggle('active',k===active);
      input.setAttribute('aria-activedescendant',o[active].id);o[active].scrollIntoView({block:'nearest'});
    }
    function render(r){
      var groups={},h='',i=0;
      r.items.forEach(function(x){var t=x.e[0];(groups[t]=groups[t]||[]).push(x.e);});
      // put whichever group holds the best hit first
      var order=ORDER.slice();if(r.items.length){var f=r.items[0].e[0];order.splice(order.indexOf(f),1);order.unshift(f);}
      order.forEach(function(t){
        var g=groups[t];if(!g)return;
        h+='<div class="sr-h">'+LABEL[t]+(g.length>CAP[t]?' <span class="c">'+g.length.toLocaleString()+' matches</span>':'')+'</div>';
        g.slice(0,CAP[t]).forEach(function(e){h+=row(e,i++);});
      });
      if(r.combo){
        var E=r.combo[0],T=r.combo[1];
        var href=(E[5]?'/employer/'+E[2]+'.html':'/employer/view.html?e='+encodeURIComponent(E[2]));
        href+=(href.indexOf('?')>0?'&':'?')+'t='+encodeURIComponent(T[1])+'#filings';
        h='<div class="sr-h">'+escH(T[1])+' at '+escH(E[1])+'</div><a role="option" id="sr-0" href="'+href+'"><span class="n">'+escH(T[1])+' filings at '+escH(E[1])+'</span><span class="c">open filtered table</span></a>';
      }
      box.innerHTML=h;active=-1;input.setAttribute('aria-expanded',h?'true':'false');
      if(!h){
        fuzzy(r.q).then(function(f){
          if(input.value.trim()!==r.q)return;
          if(!f.length){box.innerHTML='<p class="sr-none">No matches for “'+escH(r.q)+'”. Try a company name (Google, Infosys) or a job title (data scientist).</p>';return;}
          var j=0;box.innerHTML='<div class="sr-h">Did you mean</div>'+f.map(function(x){return row(x.e,j++);}).join('');
          input.setAttribute('aria-expanded','true');
        });
      }
    }
    function run(){
      var q=input.value.trim(),my=++seq;
      if(q.length<2){box.innerHTML='';input.setAttribute('aria-expanded','false');return;}
      box.innerHTML='<p class="sr-none">Searching…</p>';
      lookup(q).then(function(r){if(my===seq)render(r);}).catch(function(){if(my===seq)box.innerHTML='<p class="sr-none">Search is unavailable right now. Please try again.</p>';});
    }
    input.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(run,120);});
    input.addEventListener('keydown',function(ev){
      if(ev.key==='ArrowDown'){ev.preventDefault();setActive(active+1);}
      else if(ev.key==='ArrowUp'){ev.preventDefault();setActive(active-1);}
      else if(ev.key==='Enter'){var o=opts();if(o.length){ev.preventDefault();window.location.href=o[active>=0?active:0].getAttribute('href');}}
      else if(ev.key==='Escape'){box.innerHTML='';input.setAttribute('aria-expanded','false');}
    });
    var pre=new URLSearchParams(location.search).get('q');
    if(pre){input.value=pre;run();}
  },
  lookup:lookup
};
})();
