(function(){
'use strict';

/* Diario Percorsi 1.5.0
   - Corregge il pulsante Elenco viaggi
   - Colora sabati, domeniche e festivita italiane
   - Evidenzia i tre compleanni richiesti
*/

function ensureTripSummaryScreen(){
  var app=document.querySelector('.app');
  if(!app)return;
  if(!document.getElementById('tripSummary')){
    var summary=document.createElement('section');
    summary.id='tripSummary';
    summary.className='screen';
    summary.innerHTML='<div class="top"><div style="flex:1"><h1>Elenco viaggi</h1><div class="small">Tutti i viaggi e i luoghi visitati.</div></div></div>'+
      '<button class="back" id="tripBackBtn">← Torna alla home</button>'+
      '<div id="tripTotals" class="card"></div>'+
      '<div class="section-title">Tutti i viaggi</div><div id="tripList"></div>'+
      '<div class="section-title">Mappa Google dei luoghi visitati</div>'+
      '<div class="card"><div id="googleVisitedMap" style="height:430px;border-radius:18px;overflow:hidden;background:#eee"></div><div id="googleMapMsg" class="small" style="margin-top:8px"></div></div>';
    var modal=document.getElementById('deleteModal');
    app.insertBefore(summary,modal||null);
  }
  var back=document.getElementById('tripBackBtn');
  if(back)back.onclick=function(){goHome();};
}

function ensureTripListButton(){
  var home=document.getElementById('home');
  if(!home)return;
  var b=document.getElementById('tripListBtn');
  if(!b){
    b=document.createElement('button');
    b.id='tripListBtn';
    b.className='btn primary';
    b.style.width='100%';
    b.style.marginTop='14px';
    b.innerHTML='☰ Elenco di tutti i viaggi';
    var grid=home.querySelector('.home-grid');
    if(grid&&grid.nextSibling)grid.parentNode.insertBefore(b,grid.nextSibling);else home.appendChild(b);
  }
  /* onclick sostituisce qualsiasi listener rotto della 1.4.0 */
  b.onclick=function(ev){
    if(ev){ev.preventDefault();ev.stopPropagation();}
    openTripSummaryV15();
    return false;
  };
}

function tripPlacesV15(all){
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

function openTripSummaryV15(){
  ensureTripSummaryScreen();
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
  show('tripSummary');
  setTimeout(function(){renderGoogleVisitedMapV15(tripPlacesV15(all));},80);
}
window.openTripSummary=openTripSummaryV15;
window.openTripSummaryV15=openTripSummaryV15;

var googleMapInstanceV15=null;
function renderGoogleVisitedMapV15(points){
  var el=document.getElementById('googleVisitedMap');
  var msg=document.getElementById('googleMapMsg');
  if(!el)return;
  el.innerHTML='';
  if(!points.length){
    el.innerHTML='<div style="padding:18px">Nessun luogo ancora disponibile. I luoghi vengono salvati quando scegli partenza e arrivo nella Camminata.</div>';
    if(msg)msg.textContent='';
    return;
  }
  var key=window.APP_CONFIG&&APP_CONFIG.MAPS_API_KEY?APP_CONFIG.MAPS_API_KEY:'';
  if(!key){
    el.innerHTML='<div style="padding:18px"><b>Mappa Google non attiva.</b><br>Manca la chiave Google Maps nella configurazione GitHub.</div>';
    if(msg)msg.textContent='I viaggi restano comunque salvati nell’elenco.';
    return;
  }
  function draw(){
    if(!(window.google&&google.maps))return;
    googleMapInstanceV15=new google.maps.Map(el,{center:{lat:points[0].lat,lng:points[0].lng},zoom:5,mapTypeControl:false,streetViewControl:false});
    var bounds=new google.maps.LatLngBounds();
    points.forEach(function(p){
      var pos={lat:p.lat,lng:p.lng};
      new google.maps.Marker({position:pos,map:googleMapInstanceV15,title:p.label});
      bounds.extend(pos);
    });
    if(points.length>1)googleMapInstanceV15.fitBounds(bounds);else googleMapInstanceV15.setZoom(12);
    if(msg)msg.textContent=points.length+' luoghi pinnati.';
  }
  if(window.google&&google.maps){draw();return;}
  window.__diarioGoogleReadyV15=draw;
  var existing=document.getElementById('googleMapsApiLoaderV15')||document.getElementById('googleMapsApiLoader');
  if(existing){
    var wait=0;
    var timer=setInterval(function(){
      wait++;
      if(window.google&&google.maps){clearInterval(timer);draw();}
      else if(wait>40){clearInterval(timer);if(msg)msg.textContent='Non riesco a caricare Google Maps.';}
    },250);
    return;
  }
  var s=document.createElement('script');
  s.id='googleMapsApiLoaderV15';
  s.async=true;s.defer=true;
  s.src='https://maps.googleapis.com/maps/api/js?key='+encodeURIComponent(key)+'&callback=__diarioGoogleReadyV15';
  s.onerror=function(){el.innerHTML='<div style="padding:18px">Non riesco a caricare Google Maps.</div>';};
  document.head.appendChild(s);
}

/* ---------- Calendario ---------- */
var specialBirthdays={
  '01-30':'Compleanno di Federico',
  '05-30':'Compleanno di papà',
  '08-31':'Compleanno di mamma'
};
var fixedItalianHolidays={
  '01-01':'Capodanno',
  '01-06':'Epifania',
  '04-25':'Festa della Liberazione',
  '05-01':'Festa dei Lavoratori',
  '06-02':'Festa della Repubblica',
  '08-15':'Ferragosto',
  '11-01':'Tutti i Santi',
  '12-08':'Immacolata Concezione',
  '12-25':'Natale',
  '12-26':'Santo Stefano'
};

function easterDate(year){
  var a=year%19,b=Math.floor(year/100),c=year%100,d=Math.floor(b/4),e=b%4;
  var f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30;
  var i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451);
  var month=Math.floor((h+l-7*m+114)/31),day=((h+l-7*m+114)%31)+1;
  return new Date(year,month-1,day);
}
function dateKey(monthIndex,day){return pad(monthIndex+1)+'-'+pad(day);}
function italianHolidayName(year,monthIndex,day){
  var key=dateKey(monthIndex,day);
  if(fixedItalianHolidays[key])return fixedItalianHolidays[key];
  var easter=easterDate(year);
  if(easter.getMonth()===monthIndex&&easter.getDate()===day)return 'Pasqua';
  var monday=new Date(easter.getFullYear(),easter.getMonth(),easter.getDate()+1);
  if(monday.getMonth()===monthIndex&&monday.getDate()===day)return 'Lunedì dell’Angelo';
  return '';
}
function specialBirthdayName(monthIndex,day){return specialBirthdays[dateKey(monthIndex,day)]||'';}
function ensureCalendarLegend(target){
  var cal=document.getElementById(target);if(!cal||!cal.parentNode)return;
  var id=target+'LegendV15';
  if(document.getElementById(id))return;
  var legend=document.createElement('div');legend.id=id;legend.className='calendarLegendV15';
  legend.innerHTML='<span><i class="legendSwatch holidaySwatch"></i>Sabati, domeniche e feste italiane</span><span><i class="legendSwatch birthdaySwatch"></i>Compleanni di famiglia</span>';
  cal.parentNode.insertBefore(legend,cal);
}

var calStyle=document.createElement('style');
calStyle.textContent='\
.calendarLegendV15{display:flex;flex-wrap:wrap;gap:10px 16px;margin:8px 0 10px;font-size:13px;font-weight:750;color:#5e542d}\
.calendarLegendV15 span{display:flex;align-items:center;gap:6px}\
.legendSwatch{display:inline-block;width:18px;height:18px;border-radius:5px;border:2px solid #4c472b}\
.holidaySwatch{background:#ffc4c4}\
.birthdaySwatch{background:#d8c4ff}\
.day.italianHoliday{background:#ffc4c4;border-color:#d25151}\
.day.italianHoliday b{color:#9d1f1f}\
.day.specialBirthday{background:#d8c4ff;border-color:#7c4bb3;box-shadow:inset 0 0 0 2px #7c4bb3}\
.day.specialBirthday b{color:#50247f}\
.birthdayMark{font-size:12px;margin-left:3px}\
.dow.weekendDow{color:#b72e2e;font-weight:900}\
';
document.head.appendChild(calStyle);

renderCalendar=function(target,date,filterCat){
  var y=date.getFullYear(),m=date.getMonth(),names=['L','M','M','G','V','S','D'];
  var first=(new Date(y,m,1).getDay()+6)%7,days=new Date(y,m+1,0).getDate();
  var items=load().filter(function(e){return !filterCat||e.cat===filterCat;});
  var h='<div class="calendar-head"><button class="btn light" onclick="shiftCal(\''+target+'\',-1)">‹</button><strong>'+date.toLocaleDateString('it-IT',{month:'long',year:'numeric'})+'</strong><button class="btn light" onclick="shiftCal(\''+target+'\',1)">›</button></div><div class="cal-grid">';
  h+=names.map(function(n,idx){return '<div class="dow '+(idx>=5?'weekendDow':'')+'">'+n+'</div>';}).join('');
  for(var i=0;i<first;i++)h+='<div class="day empty"></div>';
  for(var d=1;d<=days;d++){
    var ds=y+'-'+pad(m+1)+'-'+pad(d);
    var ev=items.filter(function(e){return e.date===ds;});
    var dow=new Date(y,m,d).getDay();
    var holiday=italianHolidayName(y,m,d);
    var weekend=(dow===0||dow===6);
    var birthday=specialBirthdayName(m,d);
    var classes=['day','clickable'];
    if(weekend||holiday)classes.push('italianHoliday');
    if(birthday)classes.push('specialBirthday');
    var labels=[];
    if(weekend)labels.push(dow===6?'Sabato':'Domenica');
    if(holiday)labels.push(holiday);
    if(birthday)labels.push(birthday);
    var title=labels.length?' title="'+esc(labels.join(' · '))+'"':'';
    h+='<div class="'+classes.join(' ')+'" data-date="'+ds+'" onclick="openDayEvents(\''+target+'\',\''+ds+'\')"'+title+'><b>'+d+'</b>'+(birthday?'<span class="birthdayMark">🎂</span>':'')+'<div class="dots">'+ev.slice(0,8).map(function(e){return '<i class="dot '+e.cat+'"></i>';}).join('')+'</div></div>';
  }
  h+='</div>';
  var targetEl=document.getElementById(target);
  if(targetEl)targetEl.innerHTML=h;
  ensureCalendarLegend(target);
};

ensureTripSummaryScreen();
ensureTripListButton();
try{renderCalendar('homeCalendar',currentCalDate,null);}catch(e){}
})();
