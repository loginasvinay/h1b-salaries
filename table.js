/* Sortable tables (table.sortable) + live filter inputs (input[data-filter="#tableId"]). */
(function(){
'use strict';
function val(td){
  var t=td.textContent.trim(),n=t.replace(/[$,%]/g,'').split(/[ –-]/)[0];
  return (n!==''&&!isNaN(n))?parseFloat(n):t.toLowerCase();
}
function sortable(tbl){
  if(tbl.dataset.sortReady)return;tbl.dataset.sortReady='1';
  var ths=tbl.querySelectorAll('thead th');
  ths.forEach(function(th,i){
    th.tabIndex=0;th.setAttribute('role','button');th.classList.add('sort');
    function go(){
      var dir=th.dataset.dir==='desc'?'asc':'desc';
      ths.forEach(function(o){delete o.dataset.dir;o.removeAttribute('aria-sort');});
      th.dataset.dir=dir;th.setAttribute('aria-sort',dir==='asc'?'ascending':'descending');
      var body=tbl.tBodies[0],rows=[].slice.call(body.rows);
      rows.sort(function(a,b){
        var x=val(a.cells[i]),y=val(b.cells[i]),r=(typeof x==='number'&&typeof y==='number')?x-y:String(x).localeCompare(String(y));
        return dir==='asc'?r:-r;
      });
      rows.forEach(function(r){body.appendChild(r);});
    }
    th.addEventListener('click',go);
    th.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
  });
}
function filters(){
  document.querySelectorAll('input[data-filter]').forEach(function(inp){
    var tbl=document.querySelector(inp.dataset.filter);if(!tbl)return;
    inp.addEventListener('input',function(){
      var q=inp.value.trim().toLowerCase();
      [].forEach.call(tbl.tBodies[0].rows,function(r){r.hidden=q&&r.textContent.toLowerCase().indexOf(q)<0;});
    });
  });
}
window.H1BTable={sortable:sortable,init:function(root){(root||document).querySelectorAll('table.sortable').forEach(sortable);}};
function boot(){window.H1BTable.init();filters();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
