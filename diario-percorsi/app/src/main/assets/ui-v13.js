(function(){
  'use strict';

  var themeMeta=document.querySelector('meta[name="theme-color"]');
  if(themeMeta) themeMeta.setAttribute('content','#ffe97a');

  if(typeof CAT!=='undefined') CAT.friends={name:'Parenti e amici'};
  var homeGrid=document.querySelector('.home-grid');
  if(homeGrid && !document.getElementById('friendsTile')){
    var tile=document.createElement('button');
    tile.id='friendsTile';
    tile.className='tile friends';
    tile.setAttribute('onclick',"openCategory('friends')");
    tile.innerHTML='<span>👨‍👩‍👧‍👦</span>Parenti e amici';
    homeGrid.appendChild(tile);
  }
  var homeSubtitle=document.querySelector('#home .top .small');
  if(homeSubtitle) homeSubtitle.textContent='Fiat, macchina di papà, moto, camminate, parenti e amici.';
  var legend=document.querySelector('#home .legend');
  if(legend && !legend.querySelector('.chip.friendsChip')){
    var chip=document.createElement('span');
    chip.className='chip friendsChip';
    chip.innerHTML='<i class="dot friends"></i>Parenti e amici';
    legend.appendChild(chip);
  }

  var style=document.createElement('style');
  style.textContent='\
    .tile.friends{background:#8f68c8}\
    .dot.friends{background:#8f68c8}\
    .colorKeyboard{display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin:8px 0 12px}\
    .colorKey{height:46px;border-radius:13px;border:3px solid #5b552e;padding:0;position:relative;background:var(--keyColor)}\
    .colorKey.selected{outline:4px solid #202622;outline-offset:2px}\
    .colorKey.selected:after{content:"✓";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;color:white;text-shadow:0 1px 4px #000}\
    .colorKey.light.selected:after{color:#202622;text-shadow:none}\
    .colorKeyboardLabel{font-weight:850;margin:10px 0 5px;color:#665b2f}\
    .searchDivider{height:1px;background:#d7b74a;margin:12px 0}\
    @media(max-width:560px){.colorKeyboard{grid-template-columns:repeat(4,1fr)}}\
  ';
  document.head.appendChild(style);

  var colors=[
    ['#e53935','Rosso'],['#f57c00','Arancione'],['#ffd600','Giallo'],['#43a047','Verde'],
    ['#00acc1','Azzurro'],['#1e88e5','Blu'],['#5e35b1','Viola'],['#ec407a','Rosa'],
    ['#8d6e63','Marrone'],['#212121','Nero'],['#9e9e9e','Grigio'],['#ffffff','Bianco']
  ];
  var rewardColor=document.getElementById('rewardColor');
  var keyboard=null;
  function syncPalette(){
    if(!keyboard||!rewardColor)return;
    keyboard.querySelectorAll('.colorKey').forEach(function(btn){btn.classList.toggle('selected',btn.dataset.color.toLowerCase()===rewardColor.value.toLowerCase());});
  }
  if(rewardColor){
    rewardColor.style.display='none';
    var holder=rewardColor.parentElement;
    if(holder){
      var oldLabel=holder.querySelector('label');
      if(oldLabel) oldLabel.textContent='Scegli il colore dei premi';
      var label=document.createElement('div');
      label.className='colorKeyboardLabel';
      label.textContent='Tocca un colore';
      keyboard=document.createElement('div');
      keyboard.className='colorKeyboard';
      colors.forEach(function(item){
        var btn=document.createElement('button');
        btn.type='button';
        btn.className='colorKey'+(item[0]==='#ffffff'||item[0]==='#ffd600'?' light':'');
        btn.style.setProperty('--keyColor',item[0]);
        btn.dataset.color=item[0];
        btn.setAttribute('aria-label',item[1]);
        btn.title=item[1];
        btn.addEventListener('click',function(){
          rewardColor.value=item[0];
          rewardColor.dispatchEvent(new Event('input',{bubbles:true}));
          syncPalette();
        });
        keyboard.appendChild(btn);
      });
      holder.appendChild(label);
      holder.appendChild(keyboard);
      rewardColor.addEventListener('input',syncPalette);
      syncPalette();
    }
  }
  if(typeof newEntry==='function'){
    var originalNewEntry=newEntry;
    newEntry=function(){
      originalNewEntry();
      setTimeout(syncPalette,0);
    };
  }

  var startMarker=null,destinationMarker=null,startPoint=null,destinationPoint=null;
  function renderTripSearch(){
    var box=document.querySelector('.mapSearch');
    if(!box)return;
    box.innerHTML='\
      <div class="mapSearchRow">\
        <label for="startSearch"><b>Da dove si parte</b><input id="startSearch" type="search" placeholder="Es. Tarzana, Roma, Milano"></label>\
        <button id="startSearchBtn" type="button" class="btn primary mapSearchBtn">🔎 Cerca partenza</button>\
      </div>\
      <div id="startSearchMsg" class="searchMsg">Scrivi il punto di partenza e premi Cerca.</div>\
      <div id="startSearchResults" class="searchResults"></div>\
      <div class="searchDivider"></div>\
      <div class="mapSearchRow">\
        <label for="destinationSearch"><b>Dove vuoi andare</b><input id="destinationSearch" type="search" placeholder="Es. Santa Monica, Firenze, Napoli"></label>\
        <button id="destinationSearchBtn" type="button" class="btn primary mapSearchBtn">🔎 Cerca arrivo</button>\
      </div>\
      <div id="destinationSearchMsg" class="searchMsg">Scrivi dove vuoi arrivare e premi Cerca.</div>\
      <div id="destinationSearchResults" class="searchResults"></div>\
      <div class="searchMsg"><b>Non usa il GPS.</b> Dopo aver scelto partenza e arrivo, premi “Traccia percorso”.</div>';
    document.getElementById('startSearchBtn').addEventListener('click',function(){searchTripPlace('start')});
    document.getElementById('destinationSearchBtn').addEventListener('click',function(){searchTripPlace('destination')});
    document.getElementById('startSearch').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();searchTripPlace('start')}});
    document.getElementById('destinationSearch').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();searchTripPlace('destination')}});
  }
  async function searchTripPlace(kind){
    var isStart=kind==='start';
    var input=document.getElementById(isStart?'startSearch':'destinationSearch');
    var msg=document.getElementById(isStart?'startSearchMsg':'destinationSearchMsg');
    var results=document.getElementById(isStart?'startSearchResults':'destinationSearchResults');
    var button=document.getElementById(isStart?'startSearchBtn':'destinationSearchBtn');
    if(!input||!walkMap)return;
    var query=input.value.trim();
    results.innerHTML='';
    if(!query){msg.textContent=isStart?'Scrivi da dove si parte.':'Scrivi dove vuoi andare.';return;}
    msg.textContent='Sto cercando…';button.disabled=true;
    try{
      var url='https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&accept-language=it&q='+encodeURIComponent(query);
      var response=await fetch(url,{headers:{Accept:'application/json'}});
      if(!response.ok)throw new Error('search failed');
      var data=await response.json();
      if(!Array.isArray(data)||data.length===0){msg.textContent='Non ho trovato questo posto. Prova a scrivere anche lo Stato o la regione.';return;}
      msg.textContent=data.length===1?'Posto trovato.':'Ho trovato più risultati: scegli quello giusto.';
      results.innerHTML=data.map(function(item,index){return '<button type="button" class="searchResult" data-result="'+index+'"><b>'+esc(item.name||query)+'</b><small>'+esc(item.display_name||'')+'</small></button>';}).join('');
      results.querySelectorAll('.searchResult').forEach(function(btn){btn.addEventListener('click',function(){selectTripPlace(data[Number(btn.dataset.result)],kind)});});
      if(data.length===1)selectTripPlace(data[0],kind);
    }catch(error){msg.textContent='Non riesco a cercare adesso. Controlla la connessione internet e riprova.';}
    finally{button.disabled=false;}
  }
  function selectTripPlace(item,kind){
    if(!walkMap||!item)return;
    var isStart=kind==='start',lat=Number(item.lat),lon=Number(item.lon);
    if(!Number.isFinite(lat)||!Number.isFinite(lon))return;
    var point=L.latLng(lat,lon),label=item.display_name||item.name||'Posto trovato';
    if(isStart){
      if(startMarker)startMarker.remove();
      startPoint=point;startMarker=L.marker(point).addTo(walkMap).bindPopup('<b>Partenza</b><br>'+esc(label)).openPopup();
      document.getElementById('startSearchMsg').textContent='Partenza: '+label;
      document.getElementById('startSearchResults').innerHTML='';
    }else{
      if(destinationMarker)destinationMarker.remove();
      destinationPoint=point;destinationMarker=L.marker(point).addTo(walkMap).bindPopup('<b>Arrivo</b><br>'+esc(label)).openPopup();
      document.getElementById('destinationSearchMsg').textContent='Arrivo: '+label;
      document.getElementById('destinationSearchResults').innerHTML='';
    }
    if(startPoint&&destinationPoint)walkMap.fitBounds(L.latLngBounds([startPoint,destinationPoint]),{padding:[40,40],maxZoom:14});
    else walkMap.setView(point,13);
    setMapMode('move');setTimeout(function(){walkMap.invalidateSize();redrawRoute()},120);
  }
  if(typeof initWalkMap==='function'){
    var originalInitWalkMap=initWalkMap;
    initWalkMap=function(){
      startMarker=null;destinationMarker=null;startPoint=null;destinationPoint=null;
      originalInitWalkMap();
      renderTripSearch();
    };
  }
})();
