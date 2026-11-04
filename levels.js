/* Employer wage-level breakdown with fiscal-year tabs.
   Data: /data/emp-levels/<fnv1a(slug)%512>.json  slug -> {"ALL"|"<fy>": [[count, median] | 0  x 5]}
   index 0 = level not stated, 1-4 = DOL prevailing-wage Level I-IV. */
(function(){
'use strict';
var DV='2bc740cdd2';/* data version, set by pipeline/build_pages.py */
var NAMES=['Not stated','Level I · Entry','Level II · Qualified','Level III · Experienced','Level IV · Fully competent'];
var COLORS=['var(--hairline)','var(--l1)','var(--l2)','var(--l3)','var(--l4)'];
function bucket(s,n){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)>>>0;}return h%n;}
function money(v){return v==null?'—':'$'+Math.round(v).toLocaleString();}
window.initWageLevels=function(box){
  box=box||document.getElementById('wage-levels');
  if(!box||box.dataset.ready)return;box.dataset.ready='1';
  var slug=box.dataset.slug,out=box.querySelector('.wl-body')||box;
  fetch('/data/emp-levels/'+bucket(slug,512)+'.json?v='+DV).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
    var e=d[slug];if(!e)return;
    var periods=['ALL'].concat(Object.keys(e).filter(function(k){return k!=='ALL';}).sort().reverse()),cur='ALL';
    function render(){
      var row=e[cur]||[],tot=0,known=0;
      row.forEach(function(x,i){if(x){tot+=x[0];if(i)known+=x[0];}});
      var tabs='<div class="tabs" role="tablist" aria-label="Fiscal year">'+periods.map(function(p){
        return '<button type="button" role="tab" class="tab'+(p===cur?' active':'')+'" aria-selected="'+(p===cur)+'" data-p="'+p+'">'+(p==='ALL'?'All years':'FY'+p)+'</button>';}).join('')+'</div>';
      var bar='<div class="lvlbar" role="img" aria-label="Share of filings by wage level">'+[1,2,3,4].map(function(i){var x=row[i];if(!x||!known)return '';
        var pct=x[0]/known*100;return '<div style="width:'+pct.toFixed(1)+'%;background:'+COLORS[i]+'" title="'+NAMES[i]+': '+x[0].toLocaleString()+' ('+pct.toFixed(0)+'%)"></div>';}).join('')+'</div>';
      var rows=[1,2,3,4,0].map(function(i){var x=row[i];if(!x)return '';
        var share=i?(known?(x[0]/known*100).toFixed(0)+'%':'—'):'—';
        return '<tr><td><i class="lvl-dot" style="background:'+COLORS[i]+'"></i>'+NAMES[i]+'</td><td>'+x[0].toLocaleString()+'</td><td>'+share+'</td><td>'+money(x[1])+'</td></tr>';}).join('');
      out.innerHTML=tabs+bar+'<div class="tscroll"><table class="dt"><thead><tr><th>Wage level</th><th>Filings</th><th>Share</th><th>Median offered</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
        +'<p class="sub">DOL prevailing-wage levels the employer selected for each filing (Level I = entry, Level IV = fully competent). Share excludes filings that state no level. '+tot.toLocaleString()+' filings in this period.</p>';
      out.querySelectorAll('[data-p]').forEach(function(b){b.addEventListener('click',function(){cur=b.dataset.p;render();});});
    }
    render();
  }).catch(function(){});
};
function boot(){var b=document.getElementById('wage-levels');if(b)window.initWageLevels(b);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
