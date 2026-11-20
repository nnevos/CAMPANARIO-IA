/* Navigation starts from an explicit chat command; location always respects browser/OS permission. */
(function(){
let controller=null;
function mount(){
 if(controller)controller.destroy();
 const frame=document.getElementById('gpsMap'),canvas=document.getElementById('gpsCanvas');if(!frame||!canvas)return;
 const ctx=canvas.getContext('2d');let lat=-25.4284,lon=-49.2733,z=12,marker=null,track=[],route=[],offline=false,alive=true,down=null;
 const cache=new Map();let width=1,height=1,redrawQueued=false,requested=0,loaded=0;
 const rad=Math.PI/180;
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 const world=(la,lo)=>{const n=256*2**z;return [(lo+180)/360*n,(1-Math.log(Math.tan(clamp(la,-85,85)*rad)+1/Math.cos(clamp(la,-85,85)*rad))/Math.PI)/2*n]};
 const inverse=(x,y)=>{const n=256*2**z;return [(180/Math.PI)*Math.atan(Math.sinh(Math.PI*(1-2*y/n))),x/n*360-180]};
 const requestDraw=()=>{if(!alive||redrawQueued)return;redrawQueued=true;requestAnimationFrame(()=>{redrawQueued=false;draw()})};
 function resize(){const r=frame.getBoundingClientRect();width=Math.max(1,Math.floor(r.width));height=Math.max(1,Math.floor(r.height));const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);requestDraw()}
 function draw(){if(!alive)return;ctx.fillStyle='#1b2227';ctx.fillRect(0,0,width,height);const [cx,cy]=world(lat,lon),count=2**z;let missing=0;
  const x0=Math.floor((cx-width/2)/256),x1=Math.floor((cx+width/2)/256),y0=Math.floor((cy-height/2)/256),y1=Math.floor((cy+height/2)/256);
  for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){
   const px=Math.round(x*256-cx+width/2),py=Math.round(y*256-cy+height/2);if(y<0||y>=count)continue;
   const tx=((x%count)+count)%count,key=`${offline?'offline':'online'}:${z}:${tx}:${y}`;let item=cache.get(key);
   if(item?.state==='ready')ctx.drawImage(item.img,px,py,256,256);else{
    missing++;ctx.strokeStyle='#343c42';ctx.strokeRect(px,py,256,256);
    if(!item){const img=new Image();item={img,state:'loading'};cache.set(key,item);img.onload=()=>{item.state='ready';requestDraw()};img.onerror=()=>{item.state='error';requestDraw()};img.src=offline?`/api/app/maps/tiles/${z}/${tx}/${y}.png`:`https://tile.openstreetmap.org/${z}/${tx}/${y}.png`;
    }
   }
  }
  function dot(la,lo,color,r=7){const [x,y]=world(la,lo);const px=x-cx+width/2,py=y-cy+height/2;ctx.beginPath();ctx.arc(px,py,r+3,0,Math.PI*2);ctx.fillStyle='#0a1016cc';ctx.fill();ctx.beginPath();ctx.arc(px,py,r,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.lineWidth=2;ctx.strokeStyle='#fff';ctx.stroke()}
  if(track.length){ctx.strokeStyle='#efb648';ctx.lineWidth=3;ctx.beginPath();track.forEach((p,i)=>{const [x,y]=world(p.lat,p.lon);const px=x-cx+width/2,py=y-cy+height/2;if(i)ctx.lineTo(px,py);else ctx.moveTo(px,py)});ctx.stroke();dot(track[0].lat,track[0].lon,'#35c878',5);dot(track[track.length-1].lat,track[track.length-1].lon,'#e85b52',5)}
  if(route.length){ctx.strokeStyle='#48b8ff';ctx.lineWidth=5;ctx.lineJoin='round';ctx.beginPath();route.forEach((p,i)=>{const [x,y]=world(p.lat,p.lon);if(i)ctx.lineTo(x-cx+width/2,y-cy+height/2);else ctx.moveTo(x-cx+width/2,y-cy+height/2)});ctx.stroke();dot(route[route.length-1].lat,route[route.length-1].lon,'#4aa7ff',6)}
  if(marker)dot(marker.lat,marker.lon,'#dcb15b');
  const msg=document.getElementById('mapMessage');if(msg)msg.textContent=missing?`${offline?'Pacote offline':'Mapa online'}: ${missing} blocos não disponíveis/carregando. ${offline?'Verifique a cobertura do MBTiles.':'Verifique a conexão com a internet.'}`:'Mapa carregado. Arraste para mover; +/− para zoom.';
 }
 function center(la,lo,zoom){if(!Number.isFinite(la)||!Number.isFinite(lo)||Math.abs(la)>85||Math.abs(lo)>180)return false;lat=la;lon=lo;if(zoom!=null)z=clamp(zoom,2,18);requestDraw();return true}
 function zoom(delta){const before=world(lat,lon);z=clamp(z+delta,2,18);cache.clear();requestDraw()}
 frame.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;down={x:e.clientX,y:e.clientY,lat,lon};frame.setPointerCapture(e.pointerId)});
 frame.addEventListener('pointermove',e=>{if(!down)return;const [x,y]=world(down.lat,down.lon);const p=inverse(x-(e.clientX-down.x),y-(e.clientY-down.y));lat=clamp(p[0],-85,85);lon=p[1];requestDraw()});
 frame.addEventListener('pointerup',()=>{down=null});frame.addEventListener('pointercancel',()=>{down=null});
 frame.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?1:-1)},{passive:false});
 document.getElementById('gpsZoomIn').onclick=()=>zoom(1);document.getElementById('gpsZoomOut').onclick=()=>zoom(-1);
 const state=document.getElementById('gpsState'),info=document.getElementById('gpsInfo');
 document.getElementById('gpsManual').onclick=()=>{const la=Number(document.getElementById('gpsLat').value),lo=Number(document.getElementById('gpsLon').value);if(!document.getElementById('gpsLat').value||!document.getElementById('gpsLon').value||!center(la,lo,14)){info.textContent='Coordenadas inválidas.';return}marker={lat:la,lon:lo};state.textContent='Posição manual';info.textContent=`Coordenadas informadas manualmente: ${la.toFixed(5)}, ${lo.toFixed(5)} (não são GPS)`;requestDraw()};
 document.getElementById('gpsLocate').onclick=()=>{if(!navigator.geolocation){state.textContent='GPS indisponível';info.textContent='Este motor de janela não oferece geolocalização. Use coordenadas manuais ou trilhas do celular.';return}state.textContent='Solicitando permissão…';navigator.geolocation.getCurrentPosition(p=>{if(!alive)return;const la=p.coords.latitude,lo=p.coords.longitude;marker={lat:la,lon:lo};center(la,lo,15);state.textContent='Posição obtida';info.textContent=`${la.toFixed(6)}, ${lo.toFixed(6)} · precisão estimada ${Math.round(p.coords.accuracy)} m · ${new Date(p.timestamp).toLocaleString('pt-BR')}`},e=>{if(!alive)return;state.textContent='Localização indisponível';info.textContent=`Não foi possível obter localização (${e.code}). Verifique permissões do Windows ou use coordenadas manuais.`},{enableHighAccuracy:true,timeout:12000,maximumAge:0})};
 document.getElementById('gpsTracks').onclick=async()=>{const list=document.getElementById('gpsTrackList');list.textContent='Consultando trilhas autorizadas…';try{const r=await fetch('/api/app/gps/tracks',{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);const tracks=await r.json();list.replaceChildren();if(!tracks.length){list.textContent='Nenhuma trilha compartilhada pelo celular.';return}for(const t of tracks){const b=document.createElement('button');b.className='ui-btn';b.textContent=`${t.name||t.id||'Trilha'} · ${t.point_count||'?'} pontos`;b.onclick=()=>{const points=t.points||[];track=points.map(p=>({lat:Number(p.lat??p.latitude),lon:Number(p.lon??p.longitude)})).filter(p=>Number.isFinite(p.lat)&&Number.isFinite(p.lon)&&Math.abs(p.lat)<=85&&Math.abs(p.lon)<=180);if(track.length){center(track[0].lat,track[0].lon,14);info.textContent=`Trilha: ${track.length} pontos`}else info.textContent='Trilha sem coordenadas.'};list.append(b)}}catch(e){list.textContent=`Erro ao consultar trilhas: ${e.message}`}};

 // Route guidance: no simulated location; updates only from user-authorized geolocation.
 let navSteps=[],watchId=null,stepIndex=0,lastSpoken=-1,voiceOn=localStorage.getItem('campanario.nav.voice')==='true',rerouteAt=0,offRouteCount=0,navTarget=null,routeRequest=0;
 const navSummary=document.getElementById('navSummary'),navInstruction=document.getElementById('navInstruction');
 const valid=(la,lo)=>Number.isFinite(la)&&Number.isFinite(lo)&&Math.abs(la)<=85&&Math.abs(lo)<=180;
 const distanceMeters=(a,b)=>{const r=6371000,dLat=(b.lat-a.lat)*rad,dLon=(b.lon-a.lon)*rad;const h=Math.sin(dLat/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dLon/2)**2;return 2*r*Math.asin(Math.min(1,Math.sqrt(h)))};
 const instruction=s=>{const m=s.modifier||'',road=s.name?` na ${s.name}`:'';if(s.type==='arrive')return 'Você chegou ao destino.';if(s.type==='depart')return `Siga em frente${road}.`;if(s.type==='roundabout'||s.type==='rotary')return `Entre na rotatória${road}.`;if(m.includes('left'))return `Vire à esquerda${road}.`;if(m.includes('right'))return `Vire à direita${road}.`;if(s.type==='uturn'||m==='uturn')return 'Faça o retorno quando for permitido.';return `Continue${road}.`};
 function speak(message){if(!voiceOn||!('speechSynthesis' in window))return;const u=new SpeechSynthesisUtterance(message);u.lang='pt-BR';u.rate=.96;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)}
 function stopGuide(){if(watchId!==null){navigator.geolocation.clearWatch(watchId);watchId=null}window.speechSynthesis?.cancel();document.getElementById('navStart').disabled=!route.length;document.getElementById('navStop').disabled=true}
 document.getElementById('navVoice').checked=voiceOn;document.getElementById('navVoice').onchange=e=>{voiceOn=e.target.checked;localStorage.setItem('campanario.nav.voice',String(voiceOn));if(!voiceOn)window.speechSynthesis?.cancel()};
 async function findDestination(q,auto=false,origin=null){
  const box=document.getElementById('navResults');box.textContent='Pesquisando destino…';
  const query=new URLSearchParams({q});if(origin) {query.set('near_lat',String(origin.lat));query.set('near_lon',String(origin.lon));}
  const r=await fetch('/api/app/navigation/search?'+query);if(!r.ok)throw Error('Busca online indisponível');
  const items=await r.json();box.replaceChildren();if(!items.length)throw Error('Destino não encontrado');
  function choose(item){document.getElementById('navLat').value=item.lat;document.getElementById('navLon').value=item.lon;navTarget={lat:item.lat,lon:item.lon,name:item.name};box.textContent='Destino: '+item.name}
  if(auto&&origin){
   // Pick an unambiguous local place automatically, not merely the first global geocoder result.
   // Multiple branches with the same name require clarification.
   const normalized=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
   const terms=normalized(q).split(' ').filter(w=>w.length>2);
   const candidates=items.map(item=>{
    const d=distanceMeters(origin,{lat:Number(item.lat),lon:Number(item.lon)});
    const label=normalized(item.name);const matches=terms.filter(w=>label.includes(w)).length;
    return {...item,meters:d,score:matches/(terms.length||1)};
   }).filter(item=>item.meters<80000&&item.score>=0.8).sort((a,b)=>b.score-a.score||a.meters-b.meters);
   if(candidates.length===1||(candidates.length>1&&candidates[0].score>candidates[1].score+0.19)){
    choose(candidates[0]);return true;
   }
   if(!candidates.length){box.textContent='Nenhum destino compatível encontrado perto da origem. Informe a cidade ou o endereço completo.';return false;}
   box.textContent='Há vários locais com esse nome. Escolha a unidade correta: ';
   candidates.slice(0,6).forEach(item=>{const b=document.createElement('button');b.className='ui-btn';b.style.margin='3px';b.textContent=item.name.slice(0,100);b.onclick=async()=>{choose(item);await calculateRoute(true)};box.append(b)});
   return false;
  }
  // If multiple results exist, ask the user instead of guessing which campus/location.
  box.textContent='Selecione o destino correto: ';
  items.forEach(item=>{const b=document.createElement('button');b.className='ui-btn';b.style.margin='3px';b.textContent=item.name.slice(0,100);b.onclick=async()=>{choose(item);if(auto)await calculateRoute(true)};box.append(b)});
  return false;
 }
 document.getElementById('navSearch').onclick=async()=>{try{await findDestination(document.getElementById('navDestination').value.trim())}catch(e){document.getElementById('navResults').textContent=e.message}};
 async function calculateRoute(autoGuide=false,origin=null){
  const request=++routeRequest;
  if(!origin)stopGuide();route=[];navSteps=[];requestDraw();
  const a=origin||marker,b={lat:Number(document.getElementById('navLat').value),lon:Number(document.getElementById('navLon').value)};
  if(!a||!valid(b.lat,b.lon)||!document.getElementById('navLat').value||!document.getElementById('navLon').value){navSummary.textContent='Confirme origem e destino para calcular a rota.';return false}
  navSummary.textContent='Calculando rota rodoviária online…';
  try{const qs=new URLSearchParams({start_lat:a.lat,start_lon:a.lon,end_lat:b.lat,end_lon:b.lon});const res=await fetch('/api/app/navigation/route?'+qs);if(!res.ok)throw Error((await res.json()).detail||'Falha no roteamento');const data=await res.json();if(!alive||request!==routeRequest)return false;
   route=data.points;navSteps=data.steps;stepIndex=0;lastSpoken=-1;marker=a;center(a.lat,a.lon,14);requestDraw();
   navSummary.textContent=`${document.getElementById('navAgent').value==='todd'?'Todd':'Morgana'} · Rota real: ${(data.distance/1000).toFixed(1)} km · aproximadamente ${Math.round(data.duration/60)} min (estimativa, sem trânsito ao vivo).`;
   navInstruction.textContent=navSteps.length?instruction(navSteps[0]):'Rota calculada.';document.getElementById('navStart').disabled=!route.length;
   window.dispatchEvent(new CustomEvent('campanario:navigation-status',{detail:{kind:'ready',agent:document.getElementById('navAgent').value,destination:navTarget?.name||'',distance:data.distance,duration:data.duration}}));
   if(autoGuide)startGuide();return true;
  }catch(e){if(request===routeRequest){navSummary.textContent='Não foi possível calcular: '+e.message;window.dispatchEvent(new CustomEvent('campanario:navigation-status',{detail:{kind:'error',message:String(e.message||'Serviço indisponível')}}))}return false}
 }
 document.getElementById('navCalculate').onclick=()=>void calculateRoute(false);
 function segmentDistance(p,a,b){const k=Math.cos(p.lat*rad),ax=(a.lon-p.lon)*k*111320,ay=(a.lat-p.lat)*111320,bx=(b.lon-p.lon)*k*111320,by=(b.lat-p.lat)*111320;const dx=bx-ax,dy=by-ay,t=clamp(-(ax*dx+ay*dy)/(dx*dx+dy*dy||1),0,1);return Math.hypot(ax+t*dx,ay+t*dy)}
 function routeDeviation(p){let d=Infinity;for(let i=1;i<route.length;i++)d=Math.min(d,segmentDistance(p,route[i-1],route[i]));return d}
 function startGuide(){
  if(!route.length)return;if(!navigator.geolocation){navSummary.textContent='Guia ao vivo exige localização autorizada neste PC. A rota permanece visível.';return}
  stopGuide();document.getElementById('navStop').disabled=false;document.getElementById('navStart').disabled=true;navSummary.textContent='Guia iniciado. Aguardando posição atualizada do GPS…';
  watchId=navigator.geolocation.watchPosition(async p=>{if(!alive)return;const current={lat:p.coords.latitude,lon:p.coords.longitude};marker=current;center(current.lat,current.lon);
   const accuracy=Number(p.coords.accuracy)||9999;if(accuracy>100){navSummary.textContent=`GPS impreciso (±${Math.round(accuracy)} m). Aguardando melhor sinal.`;return}
   const deviation=routeDeviation(current);offRouteCount=deviation>90?offRouteCount+1:0;
   if(offRouteCount>=3&&Date.now()-rerouteAt>30000&&navTarget){rerouteAt=Date.now();offRouteCount=0;navSummary.textContent='Desvio detectado. Recalculando rota…';speak('Recalculando rota.');await calculateRoute(false,current);document.getElementById('navStart').disabled=true;document.getElementById('navStop').disabled=false;}
   if(!navSteps.length)return;let best=stepIndex,dist=Infinity;for(let i=stepIndex;i<Math.min(navSteps.length,stepIndex+6);i++){const loc=navSteps[i].location;if(!loc||loc.length<2)continue;const d=distanceMeters(current,{lat:loc[1],lon:loc[0]});if(d<dist){dist=d;best=i}}if(best>stepIndex&&dist<65)stepIndex=best;
   const s=navSteps[stepIndex],next=navSteps[Math.min(stepIndex+1,navSteps.length-1)],loc=next?.location,meters=loc?.length===2?distanceMeters(current,{lat:loc[1],lon:loc[0]}):null,message=instruction(next||s);
   navInstruction.textContent=(meters!==null?`Em aproximadamente ${Math.round(meters)} m: `:'')+message;
   navSummary.textContent=`Guia ativo · GPS ±${Math.round(accuracy)} m · ${Math.round(deviation)} m da rota. Siga a sinalização real.`;
   if(meters!==null&&meters<170&&stepIndex!==lastSpoken){speak(message);lastSpoken=stepIndex}requestDraw();
  },e=>{navSummary.textContent='Localização indisponível ('+e.code+'). Guia interrompido.';stopGuide()},{enableHighAccuracy:true,maximumAge:3000,timeout:15000});
 }
 document.getElementById('navStart').onclick=startGuide;
 document.getElementById('navStop').onclick=()=>{stopGuide();navSummary.textContent='Guia interrompido; rota permanece visível.'};
 // An explicit chat request opens the map and searches a real place.
 // The user chooses among results; the route is never fabricated.
 const fromChat=async e=>{if(!alive)return;const destination=String(e.detail?.destination||'').slice(0,130);if(!destination)return;
  document.getElementById('navDestination').value=destination;
  document.getElementById('navAgent').value=e.detail?.agent==='morgana'?'morgana':'todd';
  navSummary.textContent='Solicitando origem autorizada antes de procurar destinos próximos…';
  try{
   // Never geocode vague destinations globally before obtaining the actual origin.
   if(!marker){
    if(!navigator.geolocation){navSummary.textContent='Origem indisponível. Informe coordenadas manuais ou ative localização no Windows.';return;}
    await new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(p=>{
     if(!Number.isFinite(p.coords.latitude)||!Number.isFinite(p.coords.longitude)||p.coords.accuracy>10000){reject(new Error('Localização imprecisa. Informe a origem manualmente.'));return;}
     marker={lat:p.coords.latitude,lon:p.coords.longitude};center(marker.lat,marker.lon,13);
     state.textContent='Posição obtida';info.textContent=`Origem GPS: ${marker.lat.toFixed(5)}, ${marker.lon.toFixed(5)} · ±${Math.round(p.coords.accuracy)} m`;resolve();
    },reject,{enableHighAccuracy:true,timeout:12000,maximumAge:0}));
   }
   navSummary.textContent='Origem obtida. Procurando destino e iniciando a navegação automaticamente…';
   const chosen=await findDestination(destination,!!e.detail?.auto,marker);if(!chosen){navSummary.textContent='Confirme o destino correto antes de calcular a rota.';return;}
   await calculateRoute(!!e.detail?.auto);
  }catch(err){navSummary.textContent='Navegação: '+(err.message||'localização não autorizada. Informe a origem manualmente.');window.dispatchEvent(new CustomEvent('campanario:navigation-status',{detail:{kind:'error',message:navSummary.textContent}}));}
 };
 window.addEventListener('campanario:navigation-request',fromChat);

 const ro=new ResizeObserver(resize);ro.observe(frame);resize();
 fetch('/api/app/maps/status',{cache:'no-store'}).then(r=>r.json()).then(s=>{if(!alive)return;offline=!!s.offline_available&&s.format==='png';document.getElementById('mapSource').textContent=offline?`Mapa offline: ${s.name||'MBTiles PNG'} (sem internet)`:'Mapa online (OpenStreetMap). Offline: instale MBTiles PNG.';cache.clear();requestDraw()}).catch(()=>{document.getElementById('mapSource').textContent='Mapa online; status offline indisponível'});
 controller={destroy(){window.removeEventListener('campanario:navigation-request',fromChat);stopGuide();alive=false;ro.disconnect();cache.clear()}};
 }
 window.CampanarioMap={mount};
})();
