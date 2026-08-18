(function(){
'use strict';

var originalEnsureRewardStates=typeof ensureRewardStates==='function'?ensureRewardStates:null;
var originalGetRewardStates=typeof getRewardStates==='function'?getRewardStates:null;

ensureRewardStates=function(){
  var count=Math.floor(Number($('entryKm').value||0)+1e-9);
  if(rewardStates.length<count) rewardStates=rewardStates.concat(Array(count-rewardStates.length).fill(false));
  else if(rewardStates.length>count) rewardStates=rewardStates.slice(0,count);
  $('rewardCountText').value=String(count);
  return count;
};

getRewardStates=function(e){
  var count=Math.floor(Number(e&&e.km||0)+1e-9);
  var old=Array.isArray(e&&e.rewardStates)?e.rewardStates:[];
  return Array.from({length:count},function(_,i){return !!old[i];});
};

renderRewardGrid=function(){
  var count=ensureRewardStates(),color=$('rewardColor').value;
  $('rewardGrid').innerHTML=count?rewardStates.map(function(on,i){return '<button type="button" class="rewardChoice '+(on?'colored':'')+'" style="--rewardColor:'+color+'" onclick="toggleReward('+i+')" aria-label="Premio '+(i+1)+'">'+rewardSvgs[i%rewardSvgs.length]+'</button>';}).join(''):'<div class="small" style="grid-column:1/-1;padding:8px">Inserisci almeno <b>1 km</b> per ottenere il primo premio.</div>';
};

var rule=document.querySelector('.rewardRule');
if(rule) rule.innerHTML='Ogni <b>1 chilometro</b> ottieni 1 premio. Per esempio: 1 km = 1 premio, 5 km = 5 premi.';
document.querySelectorAll('.mapStatus').forEach(function(x){x.innerHTML='I premi compaiono sul percorso ogni <b>1 chilometro</b>.';});
document.querySelectorAll('.small').forEach(function(x){if(x.textContent.indexOf('100 metri')>=0)x.innerHTML=x.innerHTML.replace(/100 metri/g,'1 chilometro');});

var originalOpenCategory=typeof openCategory==='function'?openCategory:null;
if(originalOpenCategory){
  openCategory=function(cat){
    originalOpenCategory(cat);
    if($('catSubtitle')) $('catSubtitle').textContent=cat==='walk'?'Mappa del mondo, percorso e premi ogni 1 km':'Premi ogni 1 km e diario personale';
  };
}

function stripHtml(s){var d=document.createElement('div');d.innerHTML=String(s||'');return d.textContent.trim();}
function capturePlaces(){
  var out=[];
  try{
    if(typeof walkMap!=='undefined'&&walkMap&&typeof L!=='undefined'){
      walkMap.eachLayer(function(layer){
        if(layer instanceof L.Marker){
          var p=layer.getLatLng();
          var popup=layer.getPopup&&layer.getPopup();
          var label=popup?stripHtml(popup.getContent()):'Luogo visitato';
          if(!out.some(function(x){return Math.abs(x.lat-p.lat)<1e-7&&Math.abs(x.lng-p.lng)<1e-7;})) out.push({lat:p.lat,lng:p.lng,label:label});
        }
      });
    }
  }catch(e){}
  return out;
}

var originalSaveEntry=typeof saveEntry==='function'?saveEntry:null;
if(originalSaveEntry){
  saveEntry=function(){
    var before=load().map(function(e){return e.id;});
    var places=currentCat==='walk'?capturePlaces():[];
    originalSaveEntry();
    var all=load();
    var fresh=all.find(function(e){return before.indexOf(e.id)<0;});
    if(fresh){
      fresh.rewardEvery=1000;
      fresh.rewardStates=getRewardStates(fresh);
      if(places.length) fresh.visitedPlaces=places;
      persist(all);
    }
  };
}

var app=document.querySelector('.app');
if(app&&!document.getElementById('tripSummary')){
  var summary=document.createElement('section');
  summary.id='tripSummary';summary.className='screen';
  summary.innerHTML='<div class="top"><div style="flex:1"><h1>Elenco viaggi</h1><div class="small">Tutti i viaggi e i luoghi visitati.</div></div></div><button class="back" id="tripBackBtn">← Torna alla home</button><div id="tripTotals" class="card"></div><div class="section-title">Tutti i viaggi</div><div id="tripList"></div><div class="section-title">Mappa Google dei luoghi visitati</div><div class="card"><div id="googleVisitedMap" style="height:430px;border-radius:18px;overflow:hidden;background:#eee"></div><div id="googleMapMsg" class="small" style="margin-top:8px"></div></div>';
  var modal=document.getElementById('deleteModal');
  app.insertBefore(summary,modal||null);
  document.getElementById('tripBackBtn').addEventListener('click',function(){goHome();});
}

var home=document.getElementById('home');
if(home&&!document.getElementById('tripListBtn')){
  var b=document.createElement('button');
  b.id='tripListBtn';b.className='btn primary';b.style.width='100%';b.style.marginTop='14px';b.innerHTML='☰ Elenco di tutti i viaggi';
  var grid=home.querySelector('.home-grid');
  if(grid&&grid.nextSibling) grid.parentNode.insertBefore(b,grid.nextSibling); else home.appendChild(b);
  b.addEventListener('click',openTripSummary);
}

function tripPlaces(all){
  var pts=[];
  all.forEach(function(e){(Array.isArray(e.visitedPlaces)?e.visitedPlaces:[]).forEach(function(p){if(Number.isFinite(Number(p.lat))&&Number.isFinite(Number(p.lng)))pts.push({lat:Number(p.lat),lng:Number(p.lng),label:p.label||e.title||'Luogo visitato'});});});
  var unique=[];
  pts.forEach(function(p){if(!unique.some(function(q){return Math.abs(q.lat-p.lat)<1e-6&&Math.abs(q.lng-p.lng)<1e-6;}))unique.push(p);});
  return unique;
}

window.openTripSummary=function(){
  var all=load().slice().sort(function(a,b){return String(b.date+b.time).localeCompare(String(a.date+a.time));});
  var km=all.reduce(function(s,e){return s+(Number(e.km)||0);},0);
  $('tripTotals').innerHTML='<b>'+all.length+'</b> viaggi registrati · <b>'+km.toFixed(1).replace('.0','')+' km</b> totali';
  $('tripList').innerHTML=all.length?all.map(function(e){var places=Array.isArray(e.visitedPlaces)?e.visitedPlaces:[];var placeText=places.length?'<div class="small" style="margin-top:5px">📍 '+places.map(function(p){return esc(p.label||'Luogo');}).join(' → ')+'</div>':'';return '<div class="entry"><div style="flex:1"><strong>'+esc(e.title||((CAT[e.cat]&&CAT[e.cat].name)||'Viaggio'))+'</strong><div class="meta">'+fmtDate(e.date)+' · '+((CAT[e.cat]&&CAT[e.cat].name)||e.cat)+(e.km?' · '+String(e.km).replace('.',',')+' km':'')+'</div>'+placeText+'</div><button class="btn primary" onclick="openDetail(\''+e.id+'\',\'home\')">Apri</button></div>';}).join(''):'<div class="card small">Non hai ancora registrato viaggi.</div>';
  show('tripSummary');
  setTimeout(function(){renderGoogleVisitedMap(tripPlaces(all));},50);
};

var googleMapInstance=null;
function renderGoogleVisitedMap(points){
  var el=$('googleVisitedMap'),msg=$('googleMapMsg');if(!el)return;
  if(!points.length){el.innerHTML='<div style="padding:18px">Nessun luogo ancora disponibile. I luoghi vengono salvati quando scegli partenza e arrivo nella Camminata.</div>';msg.textContent='';return;}
  var key=window.APP_CONFIG&&APP_CONFIG.MAPS_API_KEY?APP_CONFIG.MAPS_API_KEY:'';
  if(!key){el.innerHTML='<div style="padding:18px"><b>Mappa Google non attiva.</b><br>Manca la chiave Google Maps nei GitHub Secrets.</div>';msg.textContent='I viaggi restano comunque salvati nell’elenco.';return;}
  function draw(){
    var center={lat:points[0].lat,lng:points[0].lng};
    googleMapInstance=new google.maps.Map(el,{center:center,zoom:5,mapTypeControl:false,streetViewControl:false});
    var bounds=new google.maps.LatLngBounds();
    points.forEach(function(p){var pos={lat:p.lat,lng:p.lng};new google.maps.Marker({position:pos,map:googleMapInstance,title:p.label});bounds.extend(pos);});
    if(points.length>1)googleMapInstance.fitBounds(bounds);else googleMapInstance.setZoom(12);
    msg.textContent=points.length+' luoghi pinnati.';
  }
  if(window.google&&google.maps){draw();return;}
  if(document.getElementById('googleMapsApiLoader')){window.__diarioGoogleDraw=draw;return;}
  window.__diarioGoogleDraw=draw;
  window.__diarioGoogleReady=function(){if(window.__diarioGoogleDraw)window.__diarioGoogleDraw();};
  var s=document.createElement('script');s.id='googleMapsApiLoader';s.async=true;s.defer=true;s.src='https://maps.googleapis.com/maps/api/js?key='+encodeURIComponent(key)+'&callback=__diarioGoogleReady';s.onerror=function(){el.innerHTML='<div style="padding:18px">Non riesco a caricare Google Maps.</div>';};document.head.appendChild(s);
}

renderRewardGrid();
})();
