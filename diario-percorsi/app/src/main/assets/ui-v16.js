(function(){
'use strict';

/* Diario Percorsi 1.6.0
   - Elimina la dipendenza dalla chiave Google Maps nell'elenco viaggi
   - Calcola automaticamente i km delle camminate
*/

function haversineKm(a,b){
  var R=6371.0088;
  var toRad=function(x){return x*Math.PI/180;};
  var lat1=toRad(Number(a.lat)),lat2=toRad(Number(b.lat));
  var dLat=lat2-lat1,dLon=toRad(Number(b.lng)-Number(a.lng));
  var h=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLon/2)*Math.sin(dLon/2);
  return 2*R*Math.atan2(Math.sqrt(h),Math.sqrt(1-h));
}

function tracedRouteKm(){
  var total=0;
  if(!Array.isArray(routeStrokes))return 0;
  routeStrokes.forEach(function(stroke){
    if(!Array.isArray(stroke))return;
    for(var i=1;i<stroke.length;i++) total+=haversineKm(stroke[i-1],stroke[i]);
  });
  return total;
}

function selectedEndpoints(){
  var start=null,end=null;
  try{
    if(walkMap&&typeof L!=='undefined'){
      walkMap.eachLayer(function(layer){
        if(!(layer instanceof L.Marker))return;
        var popup=layer.getPopup&&layer.getPopup();
        var html=popup?String(popup.getContent()||''):'';
        var text=html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim().toLowerCase();
        if(text.indexOf('partenza')>=0)start=layer.getLatLng();
        if(text.indexOf('arrivo')>=0)end=layer.getLatLng();
      });
    }
  }catch(e){}
  return {start:start,end:end};
}

function ensureAutoDistanceHint(){
  var input=document.getElementById('entryKm');
  if(!input||!input.parentElement)return null;
  var hint=document.getElementById('autoDistanceHintV16');
  if(!hint){
    hint=document.createElement('div');
    hint.id='autoDistanceHintV16';
    hint.className='small';
    hint.style.marginTop='6px';
    input.parentElement.appendChild(hint);
  }
  return hint;
}

function setupDistanceField(){
  var input=document.getElementById('entryKm');
  if(!input)return;
  var label=input.parentElement?input.parentElement.querySelector('label'):null;
  var hint=ensureAutoDistanceHint();
  if(currentCat==='walk'){
    input.readOnly=true;
    input.setAttribute('inputmode','none');
    input.style.background='#f2edcf';
    if(label)label.textContent='Distanza calcolata (km)';
    if(hint)hint.textContent='La distanza si calcola da sola. Se tracci il percorso con la matita, uso il tragitto disegnato; altrimenti uso partenza e arrivo in linea d’aria.';
    updateAutomaticDistance();
  }else{
    input.readOnly=false;
    input.setAttribute('inputmode','decimal');
    input.style.background='';
    if(label)label.textContent='Distanza (km)';
    if(hint)hint.textContent='';
  }
}

var updatingAutoDistance=false;
function updateAutomaticDistance(){
  if(updatingAutoDistance||currentCat!=='walk')return;
  var input=document.getElementById('entryKm');
  if(!input)return;
  var km=tracedRouteKm();
  var source='percorso tracciato';
  if(km<=0){
    var ep=selectedEndpoints();
    if(ep.start&&ep.end){km=haversineKm(ep.start,ep.end);source='partenza e arrivo in linea d’aria';}
    else {km=0;source='in attesa di partenza e arrivo';}
  }
  var rounded=km>0?Math.round(km*100)/100:0;
  var next=rounded?String(rounded):'';
  if(input.value!==next){
    updatingAutoDistance=true;
    input.value=next;
    try{if(typeof renderRewardGrid==='function')renderRewardGrid();}catch(e){}
    updatingAutoDistance=false;
  }
  var hint=ensureAutoDistanceHint();
  if(hint){
    if(km>0)hint.innerHTML='Distanza automatica: <b>'+String(rounded).replace('.',',')+' km</b> · calcolata da '+source+'.';
    else hint.textContent='Scegli partenza e arrivo. Se poi tracci il percorso, la distanza verrà aggiornata sul tragitto disegnato.';
  }
}

if(typeof newEntry==='function'){
  var previousNewEntryV16=newEntry;
  newEntry=function(){
    previousNewEntryV16();
    setTimeout(setupDistanceField,80);
  };
}

if(typeof redrawRoute==='function'){
  var previousRedrawRouteV16=redrawRoute;
  redrawRoute=function(){
    updateAutomaticDistance();
    previousRedrawRouteV16();
  };
}

/* ---------- Elenco viaggi: mappa senza chiave API ---------- */
var visitedLeafletMapV16=null;
function tripPlacesV16(all){
  var pts=[];
  all.forEach(function(e){
    (Array.isArray(e.visitedPlaces)?e.visitedPlaces:[]).forEach(function(p){
      var lat=Number(p.lat),lng=Number(p.lng);
      if(Number.isFinite(lat)&&Number.isFinite(lng))pts.push({lat:lat,lng:lng,label:p.label||e.title||'Luogo visitato'});
    });
  });
  var unique=[];
  pts.forEach(function(p){
    if(!unique.some(function(q){return Math.abs(q.lat-p.lat)<1e-6&&Math.abs(q.lng-p.lng)<1e-6;}))unique.push(p);
  });
  return unique;
}

function renderVisitedMapV16(points){
  var el=document.getElementById('googleVisitedMap');
  var msg=document.getElementById('googleMapMsg');
  if(!el)return;
  if(visitedLeafletMapV16){try{visitedLeafletMapV16.remove();}catch(e){}visitedLeafletMapV16=null;}
  el.innerHTML='';
  if(!points.length){
    el.innerHTML='<div style="padding:18px">Nessun luogo ancora disponibile. I luoghi vengono salvati quando scegli partenza e arrivo nella Camminata.</div>';
    if(msg)msg.textContent='';
    return;
  }
  if(typeof L==='undefined'){
    el.innerHTML='<div style="padding:18px">Non riesco a caricare la mappa. Controlla la connessione internet.</div>';
    if(msg)msg.textContent='';
    return;
  }
  visitedLeafletMapV16=L.map(el,{worldCopyJump:true}).setView([points[0].lat,points[0].lng],5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(visitedLeafletMapV16);
  var bounds=[];
  points.forEach(function(p){
    var ll=[p.lat,p.lng];
    L.marker(ll).addTo(visitedLeafletMapV16).bindPopup(esc(p.label));
    bounds.push(ll);
  });
  if(bounds.length>1)visitedLeafletMapV16.fitBounds(bounds,{padding:[35,35],maxZoom:13});
  else visitedLeafletMapV16.setZoom(12);
  if(msg)msg.textContent=points.length+' luoghi pinnati. Questa mappa non richiede nessuna chiave API.';
  setTimeout(function(){if(visitedLeafletMapV16)visitedLeafletMapV16.invalidateSize();},150);
}

function openTripSummaryV16(){
  var all=load().slice().sort(function(a,b){return String((b.date||'')+(b.time||'')).localeCompare(String((a.date||'')+(a.time||'')));});
  var km=all.reduce(function(s,e){return s+(Number(e.km)||0);},0);
  var totals=document.getElementById('tripTotals');
  var list=document.getElementById('tripList');
  if(totals)totals.innerHTML='<b>'+all.length+'</b> viaggi registrati · <b>'+km.toFixed(1).replace('.0','')+' km</b> totali';
  if(list){
    list.innerHTML=all.length?all.map(function(e){
      var places=Array.isArray(e.visitedPlaces)?e.visitedPlaces:[];
      var placeText=places.length?'<div class="small" style="margin-top:5px">📍 '+places.map(function(p){return esc(p.label||'Luogo');}).join(' → ')+'</div>':'';
      var catName=(CAT[e.cat]&&CAT[e.cat].name)||e.cat||'Viaggio';
      return '<div class="entry"><div style="flex:1"><strong>'+esc(e.title||catName)+'</strong><div class="meta">'+fmtDate(e.date)+' · '+esc(catName)+(e.km?' · '+String(e.km).replace('.',',')+' km':'')+'</div>'+placeText+'</div><button class="btn primary" onclick="openDetail(\''+e.id+'\',\'home\')">Apri</button></div>';
    }).join(''):'<div class="card small">Non hai ancora registrato viaggi.</div>';
  }
  var summary=document.getElementById('tripSummary');
  if(summary){
    var titles=summary.querySelectorAll('.section-title');
    if(titles.length>1)titles[1].textContent='Mappa dei luoghi visitati';
  }
  show('tripSummary');
  setTimeout(function(){renderVisitedMapV16(tripPlacesV16(all));},100);
}

window.openTripSummary=openTripSummaryV16;
var tripBtn=document.getElementById('tripListBtn');
if(tripBtn){tripBtn.onclick=function(ev){if(ev){ev.preventDefault();ev.stopPropagation();}openTripSummaryV16();return false;};}

setupDistanceField();
})();
