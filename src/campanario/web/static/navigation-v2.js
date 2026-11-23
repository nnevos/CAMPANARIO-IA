/* Campanario Maps V2: one navigation service per browser tab, independent of
   the Maps/Patrol DOM. Only actual GPS fixes are sent to the local backend. */
(function(){
 'use strict';
 let snapshot=null,watchId=null,lastVoiceSeq=-1,selected=null,lastFix=null,display=null;
 let voiceOn=localStorage.getItem('campanario.nav.voice')==='true';
 let destinationLabel='',origin=null,providerStatus='';
 const path='/api/app/navigation/v2';
 const $=id=>document.getElementById(id);
 const errMessage=async response=>{let value={};try{value=await response.json()}catch{}return String(value.detail||`HTTP ${response.status}`)};
 async function call(suffix,body=null){const response=await fetch(path+suffix,{method:body===null?'GET':'POST',headers:body===null?{}:{'Content-Type':'application/json'},body:body===null?undefined:JSON.stringify(body),cache:'no-store'});if(!response.ok)throw Error(await errMessage(response));return response.json()}
 const report=message=>{const summary=$('navSummary'),banner=$('mapsV2Status');if(summary)summary.textContent=message;if(banner)banner.textContent=message;};
 function speech(step,stage,meters){const m=step.modifier||'',type=step.type||'',road=step.name?` na ${step.name}`:'';
  if(type==='arrive')return 'Você está chegando ao destino.';
  let text=type==='roundabout'||type==='rotary'?'Entre na rotatória':m.includes('left')?'Vire à esquerda':m.includes('right')?'Vire à direita':type==='depart'?'Siga em frente':'Continue';
  if(stage==='advance')return `Em aproximadamente ${Math.round(meters/100)*100} metros, ${text.toLowerCase()}${road}.`;
  if(stage==='approach')return `Em aproximadamente ${Math.round(meters/10)*10} metros, ${text.toLowerCase()}${road}.`;
  return `${text}${road}.`;
 }
 function speak(s){if(!voiceOn||!window.speechSynthesis)return;const utter=new SpeechSynthesisUtterance(s);utter.lang='pt-BR';utter.rate=.95;utter.volume=Math.min(1,Math.max(0,Number(localStorage.getItem('campanario.nav.volume')||0.8)));window.speechSynthesis.cancel();window.speechSynthesis.speak(utter)}
 function notify(){if(!snapshot)return;window.dispatchEvent(new CustomEvent('campanario:navigation-v2-update',{detail:snapshot}));
  const status=$('mapsV2Status');if(status)status.textContent=`Maps V2: ${snapshot.state}${snapshot.reason?' · '+snapshot.reason:''}`;
  const instruction=$('navInstruction');let s=snapshot.instructions?.at(-1);if(instruction&&s)instruction.textContent=speech(s.maneuver,s.stage,s.meters);
  if($('mapsV2Trip')&&snapshot.route){const distance=snapshot.remaining_distance_m_estimate??snapshot.route.distance;const secs=snapshot.remaining_duration_s_estimate??snapshot.route.duration;
    $('mapsV2Trip').textContent=`Restam ~${(distance/1000).toFixed(1)} km / ~${Math.round(secs/60)} min · chegada estimada ${new Date(Date.now()+secs*1000).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})} (sem trânsito)`;
  }else if($('mapsV2Trip'))$('mapsV2Trip').textContent='Sem viagem ativa.';
  if($('navStart'))$('navStart').disabled=!['READY','PAUSED'].includes(snapshot.state);
  if($('navStop'))$('navStop').disabled=!['NAVIGATING','OFF_ROUTE','RECALCULATING','PAUSED','ARRIVED'].includes(snapshot.state);
  if(snapshot.voice_event_seq!==lastVoiceSeq&&s&&snapshot.state==='NAVIGATING'){lastVoiceSeq=snapshot.voice_event_seq;speak(speech(s.maneuver,s.stage,s.meters))}
  if(['ARRIVED','STOPPED','ERROR'].includes(snapshot.state))stopWatching();
 }
 function update(value){snapshot=value;notify();return value}
 function stopWatching(){if(watchId!==null&&navigator.geolocation){navigator.geolocation.clearWatch(watchId);watchId=null;}window.speechSynthesis?.cancel()}
 function fixFromPosition(p){const a=p.coords.accuracy;if(!Number.isFinite(a)||a>100||Date.now()-p.timestamp>20000)return null;
  return {lat:p.coords.latitude,lon:p.coords.longitude,accuracy:a,timestamp:p.timestamp/1000};}
 async function handleFix(p){const fix=fixFromPosition(p);if(!fix){report('Aguardando GPS recente com precisão de até 100 m.');return}lastFix=fix;
  try{let data=await call('/fix',fix);update(data);
   if(data.state==='RECALCULATING'){report('Desvio confirmado. Recalculando no provedor disponível…');try{data=await call('/recalculate',{});update(data);report('Nova rota calculada.')}catch(e){report('Recálculo falhou: '+e.message)}}
  }catch(e){report('GPS: '+e.message)}
 }
 function startWatching(){if(watchId!==null)return;if(!navigator.geolocation){report('Navegação ao vivo indisponível: dispositivo sem geolocalização.');return}
  watchId=navigator.geolocation.watchPosition(p=>void handleFix(p),e=>report('GPS indisponível: '+e.message),{enableHighAccuracy:true,timeout:15000,maximumAge:2500});
 }
 // Searching an address is NOT live navigation: approximate GPS is useful
 // context, never a reason to reject a simple destination search.
 async function getOrigin({precise=false,optional=false}={}){
  if(lastFix&&Date.now()-lastFix.timestamp*1000<(precise?10000:120000)&&(!precise||lastFix.accuracy<=100))return lastFix;
  if(!navigator.geolocation){if(optional)return null;throw Error('GPS indisponível. Informe uma origem manual para calcular a rota.');}
  try{
   const position=await new Promise((ok,fail)=>navigator.geolocation.getCurrentPosition(ok,fail,{enableHighAccuracy:precise,timeout:precise?13000:8000,maximumAge:precise?0:60000}));
   const accuracy=Number(position.coords.accuracy);
   const fix={lat:Number(position.coords.latitude),lon:Number(position.coords.longitude),accuracy,
     timestamp:position.timestamp/1000};
   if(!Number.isFinite(fix.lat)||!Number.isFinite(fix.lon)||Math.abs(fix.lat)>85||Math.abs(fix.lon)>180||
      !Number.isFinite(accuracy)||accuracy<=0||Date.now()-position.timestamp>(precise?20000:120000)||
      (precise&&accuracy>100)){
    if(optional)return null;
    throw Error(precise?'GPS sem precisão suficiente para navegar ao vivo. Aguarde um sinal melhor.':'Origem indisponível. Informe coordenadas manuais.');
   }
   lastFix=fix;return fix;
  }catch(e){if(optional)return null;throw e;}
 }
 // GPS acquired automatically by the Maps panel is reused for search/route.
 // It is not uploaded to the server until a user explicitly requests a route or navigation.
 window.addEventListener('campanario:location-fix',e=>{
  const fix=e.detail;
  if(!fix||!Number.isFinite(fix.lat)||!Number.isFinite(fix.lon)||!Number.isFinite(fix.accuracy))return;
  if(Date.now()-fix.timestamp*1000>120000)return;
  lastFix=fix;
  if(!origin||!origin.manual)origin=fix;
 });
 function manuallyGivenOrigin(){const lat=$('gpsLat')?.value,lon=$('gpsLon')?.value;
  if(lat!==''&&lon!==''&&lat!==undefined&&lon!==undefined&&Number.isFinite(Number(lat))&&Number.isFinite(Number(lon))&&Math.abs(Number(lat))<=85&&Math.abs(Number(lon))<=180)return {lat:Number(lat),lon:Number(lon),manual:true};
  return null;}
 function labelCandidates(items){const box=$('navResults');if(!box)return;box.replaceChildren();if(!items.length){box.textContent='Nenhum destino compatível encontrado nos provedores de mapas.';return}
  const p=document.createElement('p');p.textContent='Escolha o destino correto (distância exibida é aproximada, em linha reta):';box.append(p);
  items.slice(0,8).forEach(item=>{const button=document.createElement('button');button.type='button';button.className='ui-btn';button.style.margin='3px';const near=item.air_distance_m==null?'':` · ${(item.air_distance_m/1000).toFixed(1)} km em linha reta`;
    button.textContent=item.name+near;button.onclick=()=>{selected=item;destinationLabel=item.name;box.textContent='Destino confirmado: '+item.name;const la=$('navLat'),lo=$('navLon');if(la)la.value=item.lat;if(lo)lo.value=item.lon;};box.append(button);});
 }
 async function resolve(query,auto=false){
  const near=manuallyGivenOrigin()||origin||await getOrigin({optional:true});
  if(near)origin=near;
  if(!near&&/\b(mais pr[oó]xim[oa]|perto de mim|nas proximidades)\b/i.test(query))
   throw Error('Para buscar o mais próximo, informe uma origem manual ou habilite a localização. A pesquisa por endereço continua disponível sem GPS.');
  if(near?.accuracy>100)report(`Busca com localização aproximada (±${Math.round(near.accuracy)} m); confirme o destino no mapa.`);
  const explicitDistant=/(?:\bde\b|\bem\b|\bna\b|\bno\b)\s+[\p{L}]{3,}/iu.test(query)&&!/^posto de gasolina(?:\s+mais próximo)?$/i.test(query);
  const result=await call('/resolve',{query,...(near?{near_lat:near.lat,near_lon:near.lon}:{}),explicit_distant:explicitDistant});
  if(result.selected){selected=result.selected;destinationLabel=selected.name;labelCandidates([selected]);if(auto)return await calculate(true);return result}
  selected=null;labelCandidates(result.candidates);report(result.ambiguous?'Vários destinos possíveis: selecione um antes de iniciar.':'Escolha um destino válido para continuar.');return result;
 }
 async function calculate(autoStart=false){if(!selected){const a=$('navLat')?.value,b=$('navLon')?.value;if(a!==''&&b!==''&&a!==undefined&&b!==undefined){selected={lat:Number(a),lon:Number(b),name:'Coordenadas informadas'};}else throw Error('Selecione o destino primeiro.')}
  const start=manuallyGivenOrigin()||origin||await getOrigin();origin=start;
  report('Calculando rota no provedor OSM disponível…');
  const mode=$('mapsV2Mode')?.value||'driving';
  const result=await call('/route',{start_lat:start.lat,start_lon:start.lon,end_lat:selected.lat,end_lon:selected.lon,mode,destination_name:destinationLabel||selected.name||''});update(result);
  const r=result.route;report(`Rota ${r.provider||'OSRM'}: ${(r.distance/1000).toFixed(1)} km · ${Math.round(r.duration/60)} min, sem trânsito ao vivo.`);
  if(autoStart)await start();return result;
 }
 async function start(){
  // A manually entered origin may calculate a route, but cannot stand in for
  // actual GPS in a turn-by-turn live navigation session.
  const gps=await getOrigin({precise:true});
  const value=await call('/command/start',{});update(value);
  await handleFix({coords:{latitude:gps.lat,longitude:gps.lon,accuracy:gps.accuracy},timestamp:gps.timestamp*1000});
  startWatching();report('Guia ativo com GPS recente autorizado.');return value;
 }
 async function pause(){const value=await call('/command/pause',{});stopWatching();return update(value)}
 async function resume(){const value=await call('/command/resume',{});update(value);startWatching();return value}
 async function stop(){stopWatching();selected=null;origin=null;return update(await call('/command/stop',{}))}
 async function restore(){try{const value=await call('/status');lastVoiceSeq=value.voice_event_seq;update(value);if(['NAVIGATING','OFF_ROUTE','RECALCULATING'].includes(value.state))startWatching()}catch(e){report('Maps V2 indisponível: '+e.message)}}
 function bindUI(){if(!$('navCalculate'))return;
  const input=$('navDestination');if(input)input.oninput=()=>{selected=null;destinationLabel='';};
  const search=$('navSearch');if(search)search.onclick=()=>void resolve($('navDestination').value.trim(),false).catch(e=>report('Busca: '+e.message));
  $('navCalculate').onclick=()=>void calculate(false).catch(e=>report('Rota: '+e.message));
  $('navStart').onclick=()=>void (snapshot?.state==='PAUSED'?resume():start()).catch(e=>report('Navegação: '+e.message));
  $('navStop').onclick=()=>void stop().catch(e=>report('Encerrar: '+e.message));
  if($('navVoice')){$('navVoice').checked=voiceOn;$('navVoice').onchange=e=>{voiceOn=e.target.checked;localStorage.setItem('campanario.nav.voice',String(voiceOn));if(!voiceOn)window.speechSynthesis?.cancel()};}
  if($('mapsV2Pause'))$('mapsV2Pause').onclick=()=>void pause().catch(e=>report(e.message));
  if($('mapsV2Resume'))$('mapsV2Resume').onclick=()=>void resume().catch(e=>report(e.message));
  if($('mapsV2Repeat'))$('mapsV2Repeat').onclick=()=>{const step=snapshot?.instructions?.at(-1);if(step)speak(speech(step.maneuver,step.stage,step.meters));else report('Ainda não há manobra recebida pelo roteador.');};
  if($('mapsV2Volume')){$('mapsV2Volume').value=localStorage.getItem('campanario.nav.volume')||'0.8';$('mapsV2Volume').oninput=e=>localStorage.setItem('campanario.nav.volume',e.target.value);}
  notify();
 }
 // An unobtrusive navigation indicator remains accessible from Chat.
 const chip=document.createElement('button');chip.type='button';chip.id='campNavV2Chip';chip.className='ui-btn';
 chip.style.cssText='position:fixed;bottom:78px;right:18px;z-index:1900;max-width:210px;box-shadow:0 3px 16px #0008';
 chip.hidden=true;chip.title='Voltar ao mapa sem encerrar a rota';
 chip.onclick=()=>document.querySelector('[data-view="patrulha"]')?.click();
 document.body.appendChild(chip);
 window.addEventListener('campanario:navigation-v2-update',e=>{const state=e.detail?.state;chip.hidden=!['READY','NAVIGATING','PAUSED','OFF_ROUTE','RECALCULATING'].includes(state);chip.textContent='◉ Navegação · '+state;});
 window.addEventListener('campanario:navigation-request',e=>{const destination=String(e.detail?.destination||'').trim();if(!destination)return;
  const input=$('navDestination');if(input)input.value=destination;
  report('Procurando destino (GPS opcional para endereços): '+destination);
  // The entire navigation session outlives Maps view changes.
  void resolve(destination,!!e.detail?.auto).catch(err=>report('Não foi possível navegar: '+err.message));
 });
 window.CampanarioNavigationV2={bindUI,restore,resolve,calculate,start,pause,resume,stop,status:()=>snapshot};
 void restore();
})();
