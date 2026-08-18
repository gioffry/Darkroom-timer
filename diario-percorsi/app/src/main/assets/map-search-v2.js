let startSearchMarkerV2=null;
let destinationSearchMarkerV2=null;
let startSearchPointV2=null;
let destinationSearchPointV2=null;

function renderPlaceSearchV2(){
  const box=document.querySelector('.mapSearch');
  if(!box)return;
  box.innerHTML=`
    <div class="mapSearchRow">
      <label for="startSearch"><b>Da dove si parte</b>
        <input id="startSearch" type="search" placeholder="Es. Tarzana, Roma, Milano">
      </label>
      <button id="startSearchBtn" type="button" class="btn primary mapSearchBtn">🔎 Cerca partenza</button>
    </div>
    <div id="startSearchMsg" class="searchMsg">Scrivi il punto di partenza e premi Cerca.</div>
    <div id="startSearchResults" class="searchResults"></div>
    <div class="searchDivider"></div>
    <div class="mapSearchRow">
      <label for="destinationSearch"><b>Dove vuoi andare</b>
        <input id="destinationSearch" type="search" placeholder="Es. Santa Monica, Firenze, Napoli">
      </label>
      <button id="destinationSearchBtn" type="button" class="btn primary mapSearchBtn">🔎 Cerca arrivo</button>
    </div>
    <div id="destinationSearchMsg" class="searchMsg">Scrivi dove vuoi arrivare e premi Cerca.</div>
    <div id="destinationSearchResults" class="searchResults"></div>
    <div class="searchMsg"><b>Non usa il GPS.</b> Dopo aver scelto partenza e arrivo, premi “Traccia percorso”.</div>`;

  $('startSearchBtn').addEventListener('click',()=>searchPlaceV2('start'));
  $('destinationSearchBtn').addEventListener('click',()=>searchPlaceV2('destination'));
  $('startSearch').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();searchPlaceV2('start')}});
  $('destinationSearch').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();searchPlaceV2('destination')}});
}

const originalInitWalkMap=initWalkMap;
initWalkMap=function(){
  originalInitWalkMap();
  renderPlaceSearchV2();
};

async function searchPlaceV2(kind){
  const isStart=kind==='start';
  const input=$(isStart?'startSearch':'destinationSearch');
  const msg=$(isStart?'startSearchMsg':'destinationSearchMsg');
  const results=$(isStart?'startSearchResults':'destinationSearchResults');
  const button=$(isStart?'startSearchBtn':'destinationSearchBtn');
  if(!input||!walkMap)return;
  const query=input.value.trim();
  results.innerHTML='';
  if(!query){msg.textContent=isStart?'Scrivi da dove si parte.':'Scrivi dove vuoi andare.';return;}
  msg.textContent='Sto cercando…';
  button.disabled=true;
  try{
    const url='https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&accept-language=it&q='+encodeURIComponent(query);
    const response=await fetch(url,{headers:{Accept:'application/json'}});
    if(!response.ok)throw new Error('search failed');
    const data=await response.json();
    if(!Array.isArray(data)||data.length===0){
      msg.textContent='Non ho trovato questo posto. Prova a scrivere anche lo Stato o la regione.';
      return;
    }
    msg.textContent=data.length===1?'Posto trovato.':'Ho trovato più risultati: scegli quello giusto.';
    results.innerHTML=data.map((item,index)=>`<button type="button" class="searchResult" data-result="${index}"><b>${esc(item.name||query)}</b><small>${esc(item.display_name||'')}</small></button>`).join('');
    results.querySelectorAll('.searchResult').forEach(btn=>btn.addEventListener('click',()=>selectSearchResultV2(data[Number(btn.dataset.result)],kind)));
    if(data.length===1)selectSearchResultV2(data[0],kind);
  }catch(error){
    msg.textContent='Non riesco a cercare adesso. Controlla la connessione internet e riprova.';
  }finally{
    button.disabled=false;
  }
}

function selectSearchResultV2(item,kind){
  if(!walkMap||!item)return;
  const isStart=kind==='start';
  const lat=Number(item.lat),lon=Number(item.lon);
  if(!Number.isFinite(lat)||!Number.isFinite(lon))return;
  const point=L.latLng(lat,lon);
  const label=item.display_name||item.name||'Posto trovato';
  if(isStart){
    if(startSearchMarkerV2)startSearchMarkerV2.remove();
    startSearchPointV2=point;
    startSearchMarkerV2=L.marker(point).addTo(walkMap).bindPopup('<b>Partenza</b><br>'+esc(label)).openPopup();
    $('startSearchMsg').textContent='Partenza: '+label;
    $('startSearchResults').innerHTML='';
  }else{
    if(destinationSearchMarkerV2)destinationSearchMarkerV2.remove();
    destinationSearchPointV2=point;
    destinationSearchMarkerV2=L.marker(point).addTo(walkMap).bindPopup('<b>Arrivo</b><br>'+esc(label)).openPopup();
    $('destinationSearchMsg').textContent='Arrivo: '+label;
    $('destinationSearchResults').innerHTML='';
  }
  if(startSearchPointV2&&destinationSearchPointV2){
    walkMap.fitBounds(L.latLngBounds([startSearchPointV2,destinationSearchPointV2]),{padding:[40,40],maxZoom:14});
  }else{
    walkMap.setView(point,13);
  }
  setMapMode('move');
  setTimeout(()=>{walkMap.invalidateSize();redrawRoute()},120);
}
