
const $=id=>document.getElementById(id);const clientId=localStorage.getItem('campanario.client_id')||crypto.randomUUID();localStorage.setItem('campanario.client_id',clientId);let sessionCache=[],sessionId=null,busy=false,agents=[],system={},primary='morgana',viewingArchive=false,realtime=null,lastSequence=0,bubble=null,speaker=null;
const stage=$('stage');let followingLatest=true;
function atLatest(){return stage.scrollHeight-stage.scrollTop-stage.clientHeight<=96}
function updateJump(){const jump=$('jumpLatest');if(jump)jump.hidden=atLatest()}
function goLatest(){stage.scrollTop=stage.scrollHeight;followingLatest=true;updateJump()}
function afterContentAdded(shouldFollow){if(shouldFollow)goLatest();else updateJump()}
stage.addEventListener('scroll',()=>{followingLatest=atLatest();updateJump()},{passive:true});
$('jumpLatest').addEventListener('click',goLatest);
function name(id){return agents.find(a=>a.id===id)?.name||(id==='todd'?'Todd':id==='campanario'?'Campanário':'Morgana')}
const visualStates={morgana:'idle',todd:'idle',campanario:'idle'};
function avatarSrc(id,state='idle'){const safeId=['morgana','todd','campanario'].includes(id)?id:'campanario';const safeState=['idle','thinking','speaking'].includes(state)?state:'idle';return `/ui-assets/${safeId}_${safeState}.svg`}
function applySigilState(agentId,state){if(!visualStates.hasOwnProperty(agentId))return;visualStates[agentId]=state;document.querySelectorAll(`img[data-sigil-agent="${agentId}"]`).forEach(img=>{const url=avatarSrc(agentId,state);if(img.getAttribute('src')!==url)img.src=url;img.closest('.participant')?.setAttribute('data-activity',state)});if(agentId==='campanario'){const center=$('coreSigil');if(center&&center.getAttribute('src')!==avatarSrc(agentId,state))center.src=avatarSrc(agentId,state)}}
function updateSigilActivity(state,agentId=''){for(const id of ['morgana','todd'])applySigilState(id,state==='speaking'&&id===agentId?'speaking':state==='processing'?'thinking':'idle');applySigilState('campanario',state==='speaking'?'speaking':state==='processing'?'thinking':'idle')}
function setState(state,copy='',agentId=''){const map={present:['Presente','presente'],attentive:['Atento','atento'],processing:['Processando','engajado'],speaking:['Engajado','engajado']};const agentClass=agentId==='todd'||agentId==='morgana'?` ${agentId}`:'';$('core').className='core '+(state==='present'?'':state)+agentClass;$('stateTitle').textContent=map[state][0];$('topState').textContent=map[state][1];if(copy)$('stateCopy').textContent=copy;$('ambient').style.display='grid';updateSigilActivity(state,agentId)}

async function api(path,opt={}){const r=await fetch(path,opt);if(!r.ok){let detail='';try{detail=(await r.json()).detail||''}catch{}throw new Error(detail||`HTTP ${r.status}`)}return r.json()}
function renderParticipants(){ $('participants').innerHTML=agents.filter(a=>a.id==='morgana'||a.id==='todd').map(a=>`<span class="participant ${a.id} ${a.id===primary?'primary':''}" data-activity="${visualStates[a.id]}"><span class="sigil-avatar-wrap"><img class="mini-avatar" data-sigil-agent="${a.id}" src="${avatarSrc(a.id,visualStates[a.id])}" alt="Sigilo ${a.id}" loading="eager"></span>${a.id==='todd'?'Todd':'Morgana'}<span>${a.id===primary?' · voz principal':''}</span></span>`).join('') }

// Render only a tiny, safe subset of Markdown; never interpolate model text as HTML.
// This also fixes accidental literal \\*italics\\* emitted by small local models.
function renderConversationText(element,raw,role){
 const text=String(raw||'').replace(/\\([*_])/g,'$1');
 element.replaceChildren();
 if(role==='user'){element.textContent=text;return}
 const rx=/(\*\*([^*\n]+)\*\*|\*([^*\n]+)\*|https?:\/\/[^\s<>'"()]+)/g;
 let index=0,match;
 while((match=rx.exec(text))){
  if(match.index>index)element.append(document.createTextNode(text.slice(index,match.index)));
  let node;
  if(match[2]!==undefined){node=document.createElement('strong');node.textContent=match[2]}
  else if(match[3]!==undefined){node=document.createElement('em');node.textContent=match[3]}
  else {node=document.createElement('a');node.textContent=match[0];node.href=match[0];node.rel='noopener noreferrer';node.target='_blank'}
  element.append(node);index=rx.lastIndex;
 }
 if(index<text.length)element.append(document.createTextNode(text.slice(index)));
}
function parseCampanarioTime(value){if(!value)return new Date();if(typeof value==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d/.test(value)&&!/(?:Z|[+-]\d\d:\d\d)$/.test(value))return new Date(value+'Z');return new Date(value)}function formatMessageTime(value){const date=parseCampanarioTime(value);return Number.isNaN(date.getTime())?'--:--':date.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}function addTurn(role,text,agentId,createdAt){$('ambient').style.display='grid';const el=document.createElement('div');el.className=`turn ${role==='user'?'user':agentId||'morgana'}`;const avatar=role==='user'?'':`<span class="agent-sigil-wrap"><img class="agent-avatar" src="${avatarSrc(agentId,visualStates[agentId]||'idle')}" alt="Sigilo ${name(agentId)}"></span>`;el.innerHTML=`${avatar}<div class="message-meta"><div class="speaker">${role==='user'?'você':name(agentId)}</div><time class="message-time"></time></div><div class="utterance"></div>`;const stamp=el.querySelector('.message-time');stamp.textContent=formatMessageTime(createdAt);const parsed=parseCampanarioTime(createdAt);if(!Number.isNaN(parsed.getTime())){stamp.dateTime=parsed.toISOString();stamp.title=parsed.toLocaleString('pt-BR')}const utterance=el.querySelector('.utterance');utterance.dataset.raw=String(text||'');renderConversationText(utterance,utterance.dataset.raw,role);
  const follow=followingLatest;$('conversation').appendChild(el);afterContentAdded(follow);return el.querySelector('.utterance')}
function addError(text){const e=document.createElement('div');e.className='error';e.textContent=text;const follow=followingLatest;$('conversation').appendChild(e);afterContentAdded(follow)}
function setBusy(v){busy=v;$('prompt').disabled=v;$('send').disabled=v;$('newConversation').disabled=v;$('newSessionPanel').disabled=v;$('sidebarNew').disabled=v;$('statusline').textContent=v?'Gerando resposta…':'';if(v)setState('processing','Organizando o turno…');/* As sessoes sao renderizadas enquanto busy=true no fim de stream();
   sincronizar disabled ao encerrar o turno, sem exigir Nova conversa. */
  $('sessions').querySelectorAll('.history-row .session, .history-row .session-delete').forEach(button=>{button.disabled=v});}
function closeRealtime(){if(realtime){const ws=realtime;realtime=null;ws.close()}bubble=null;speaker=null}
function realtimeUrl(){const scheme=location.protocol==='https:'?'wss':'ws';return `${scheme}://${location.host}/ws/v1/events?session_id=${encodeURIComponent(sessionId)}&after_sequence=${lastSequence}&client_id=${encodeURIComponent(clientId)}`}
function handleRuntimeEvent(event){lastSequence=Math.max(lastSequence,event.sequence||0);const p=event.payload||{};if(event.event_type==='AGENT_RESPONSE_STARTED'){speaker=p.agent_id;bubble=null;setState('speaking',`${name(speaker)} está respondendo`,speaker)}if(event.event_type==='AGENT_RESPONSE_CHUNK'){if(!bubble||speaker!==p.agent_id){speaker=p.agent_id;bubble=addTurn('assistant','',speaker,event.occurred_at)}const follow=followingLatest;bubble.dataset.raw=(bubble.dataset.raw||'')+(p.text||'');renderConversationText(bubble,bubble.dataset.raw,'assistant');afterContentAdded(follow)}if(event.event_type==='AGENT_INTERRUPTED'){if(bubble&&!bubble.textContent.trim())bubble.closest('.turn')?.remove();bubble=null;speaker=null;setState('attentive','A resposta foi interrompida. Você pode tentar novamente.')}if(event.event_type==='AGENT_RESPONSE_FINISHED'){if(bubble&&!bubble.textContent.trim()){bubble.closest('.turn')?.remove()}const activeAvatar=$('conversation').lastElementChild?.querySelector('.agent-avatar');if(activeAvatar)activeAvatar.src=avatarSrc(p.agent_id||speaker,'idle');bubble=null;speaker=null;setState('attentive','Conversa aberta. Continue quando quiser.')}}
async function connectRealtime(skipHistory=false){if(!sessionId)return;closeRealtime();await new Promise((resolve,reject)=>{const ws=new WebSocket(realtimeUrl());realtime=ws;let ready=false;const timer=setTimeout(()=>{if(!ready){ws.close();reject(new Error('realtime_timeout'))}},5000);ws.onmessage=e=>{const frame=JSON.parse(e.data);if(frame.frame_type==='event'&&(!skipHistory||ready))handleRuntimeEvent(frame.event);if(frame.frame_type==='ready'){ready=true;lastSequence=Math.max(lastSequence,frame.replayed_through_sequence||0);clearTimeout(timer);resolve()}};ws.onerror=()=>{if(!ready){clearTimeout(timer);reject(new Error('realtime_unavailable'))}};ws.onclose=()=>{if(realtime===ws)realtime=null;if(!ready){clearTimeout(timer)}}})}
async function ensureRealtime(){if(realtime&&realtime.readyState===WebSocket.OPEN)return;await connectRealtime()}
async function boot(){system=await api('/api/v1/runtime');agents=await api('/api/v1/agents');primary=system.default_primary_agent_id||'morgana';$('model').textContent=system.model||'local';$('build').textContent=system.release_id||'—';$('agentDetails').innerHTML=agents.map(a=>`<div class="kv"><span>● ${a.name}</span><strong>${a.id===system.default_primary_agent_id?'voz principal · presente':'presente'}</strong></div>`).join('');renderParticipants();await refreshSessions();localStorage.removeItem('campanario.active_session');sessionId=null;$('conversation').innerHTML='';followingLatest=true;goLatest();setState('present');$('statusline').textContent='';void checkSystemStatus();$('prompt').focus()}
function closeSidebar(){ $('mainLayout').classList.remove('sidebar-open');$('sidebarToggle').setAttribute('aria-expanded','false') }
function renderSessions(){
  const el=$('sessions');el.replaceChildren();const term=$('sessionSearch').value.trim().toLocaleLowerCase('pt-BR');
  const visible=sessionCache.filter(s=>(s.title||'Conversa sem título').toLocaleLowerCase('pt-BR').includes(term));
  if(!visible.length){const empty=document.createElement('p');empty.className='history-empty';empty.textContent=term?'Nenhuma conversa com esse título.':'Nenhuma conversa salva ainda.';el.appendChild(empty)}
  visible.forEach(s=>{const b=document.createElement('button');b.type='button';b.className='session'+(s.id===sessionId?' active':'');b.setAttribute('aria-current',s.id===sessionId?'page':'false');
    const title=document.createElement('span');title.className='session-title';title.textContent=s.title||'Conversa sem título';
    const when=document.createElement('span');when.className='session-when';const d=parseCampanarioTime(s.updated_at);when.textContent=Number.isNaN(d.getTime())?'':d.toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'});
    b.append(title,when);b.title='Abrir e continuar esta conversa';b.disabled=busy;b.onclick=()=>selectSession(s).catch(e=>addError('Falha ao abrir conversa: '+e.message));
    const row=document.createElement('div');row.className='history-row';const del=document.createElement('button');del.type='button';del.className='session-delete';del.textContent='×';del.title='Excluir esta conversa';del.setAttribute('aria-label','Excluir conversa '+(s.title||'sem título'));del.disabled=busy;del.onclick=()=>void deleteConversation(s);row.append(b,del);el.appendChild(row)
  });
}
async function refreshSessions(){sessionCache=await api('/api/v1/sessions');renderSessions();return sessionCache}
async function selectSession(s){
  if(busy)return;
  // Load server history before switching active session, to avoid partial state on failure.
  const history=await api(`/api/v1/sessions/${s.id}/messages`);
  closeRealtime();sessionId=s.id;localStorage.setItem('campanario.active_session',sessionId);lastSequence=0;viewingArchive=false;
  primary=s.primary_agent_id||system.default_primary_agent_id||'morgana';renderParticipants();
  $('conversation').replaceChildren();followingLatest=false;history.forEach(m=>addTurn(m.role,m.content,m.agent_id,m.created_at));goLatest();
  if(!history.length)setState('present','Esta conversa ainda não possui mensagens.');else $('ambient').style.display='grid';
  $('statusline').textContent='';
  $('systemPanel').classList.remove('open');closeSidebar();renderSessions();
  await connectRealtime(true);$('prompt').focus();
}
function newConversation(){
  if(busy||!system)return;
  document.querySelector('[data-view="inicio"]')?.click();
  // A new technical episode begins on its first message. Previous episodes stay
  // in the archive; learned memories remain in the development memory store.
  closeRealtime();sessionId=null;localStorage.removeItem('campanario.active_session');lastSequence=0;viewingArchive=false;
  primary=system.default_primary_agent_id||'morgana';renderParticipants();updateSigilActivity('present');
  $('conversation').replaceChildren();followingLatest=true;goLatest();$('prompt').value='';
  $('systemPanel').classList.remove('open');closeSidebar();renderSessions();
  setState('present');
  $('statusline').textContent='';
  void refreshSessions().catch(err=>addError(`Não foi possível atualizar os episódios: ${err.message}`));
  $('prompt').focus();
}
async function createSession(refresh=true){const s=await api('/api/v1/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});sessionId=s.id;localStorage.setItem('campanario.active_session',sessionId);lastSequence=0;primary=s.primary_agent_id;renderParticipants();await connectRealtime();if(refresh)await refreshSessions();return s}
async function stream(text){await ensureRealtime();await api(`/api/v1/sessions/${sessionId}/turn`,{method:'POST',headers:{'Content-Type':'application/json','X-Campanario-Client-Id':clientId},body:JSON.stringify({message:text})});const ss=await refreshSessions(),s=ss.find(x=>x.id===sessionId);if(s){primary=s.primary_agent_id||primary;renderParticipants()}setState('attentive','Conversa aberta. Continue sem precisar chamar de novo.');$('statusline').textContent=''}
// Navigation requests are UI commands, not model-generated claims about real routes.
function navigationDestination(text){
 // Explicit route requests only; never turn ordinary discussion into GPS tracking.
 const m=text.match(/\b(?:rota|trajeto|caminho)\b[^\n.!?]{0,90}?\b(?:para|até|ao|à)\s+([^.!?\n]{3,130})/i);
 if(!m)return null;
 const destination=m[1].replace(/\s+(?:todd|morgana)(?:\s+(?:r[aá]pido|por favor|agora))?\s*$/i,'').replace(/\s+(?:r[aá]pido|por favor|agora)\s*$/i,'').trim();
 return destination.length>=3?destination:null;
}
// Route information is generated from verified navigation results, never invented by the agent.
window.addEventListener('campanario:navigation-status',e=>{
 const d=e.detail||{};
 if(d.kind==='ready'){
  const who=d.agent==='morgana'?'Morgana':'Todd';
  const km=(Number(d.distance)/1000).toFixed(1),mins=Math.max(1,Math.round(Number(d.duration)/60));
  addError(`${who} · Rota calculada para ${d.destination||'o destino'}: ${km} km, cerca de ${mins} min. Mapa aberto; guia iniciado quando o GPS estiver disponível. Estimativa sem trânsito ao vivo.`);
 }else if(d.kind==='error')addError('Navegação: '+String(d.message||'Não foi possível calcular a rota.'));
});
$('form').addEventListener('submit',async e=>{e.preventDefault();const text=$('prompt').value.trim();if(!text||busy)return;
 const destination=navigationDestination(text);
 if(destination){
  if(/^(?:sair|fugir|escapar|ir embora|deixar|afastar(?:-se)?)\s+(?:da|do|de)\s+(?:cidade|regi[aã]o|bairro|local)|^(?:um|algum)\s+lugar\s+seguro$/i.test(destination)){
    $('prompt').value='';addTurn('user',text);addError('Todd: Entendi que você quer sair da cidade, mas isso não é um destino específico. Para calcular uma rota real, diga para qual cidade, bairro ou local deseja ir. Não vou escolher um lugar aleatório.');return;
  }
  $('prompt').value='';addTurn('user',text);addError('Navegação: solicitando origem autorizada e calculando rota real para “'+destination+'”.');window.CampanarioNavigation?.open(destination,{auto:true,voice:localStorage.getItem('campanario.nav.voice')==='true',agent:/\btodd\b/i.test(text)?'todd':/\bmorgana\b/i.test(text)?'morgana':'todd'});return;}
 if(/\brota\s+no\s+mapa\b/i.test(text)){addError('Para abrir uma rota real, informe o destino. Exemplo: “Todd, rota para a Prefeitura de Maringá”. Também será necessária uma origem confirmada.');return;}
try{setBusy(true);if(!sessionId)await createSession();followingLatest=true;addTurn('user',text);goLatest();$('prompt').value='';await stream(text)}catch(err){addError(`Falha: ${err.message}`)}finally{setBusy(false);$('prompt').focus()}});$('prompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('form').requestSubmit()}});$('mic').onclick=()=>{setState('attentive','Estrutura de voz preparada; captura contínua/wake word ainda não está conectada.');$('statusline').textContent='voz ainda não conectada'};$('newConversation').onclick=newConversation;$('sidebarNew').onclick=newConversation;$('sessionSearch').addEventListener('input',renderSessions);$('sidebarToggle').onclick=()=>{const opened=$('mainLayout').classList.toggle('sidebar-open');$('sidebarToggle').setAttribute('aria-expanded',String(opened))};$('sidebarScrim').onclick=closeSidebar;$('newSessionPanel').onclick=newConversation;$('systemOpen').onclick=()=>$('systemPanel').classList.add('open');$('systemClose').onclick=()=>$('systemPanel').classList.remove('open');window.addEventListener('beforeunload',closeRealtime);
let systemStatus='loading';
function updateSystemStatus(next){systemStatus=next;const value=$('statusValue'),led=$('statusLed');if(value)value.textContent=({online:'Online',degraded:'Parcial - IA indisponivel',loading:'Carregando',offline:'Offline',error:'Fora de funcionamento'})[next]||'Indisponível';if(led)led.dataset.status=next;document.body.dataset.systemStatus=next;}
async function checkSystemStatus(){try{const response=await fetch('/api/app/status',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(!response.ok){updateSystemStatus('error');return;}const value=await response.json();updateSystemStatus(value.can_chat?'online':'degraded')}catch{updateSystemStatus('offline')}}
updateSystemStatus('loading');setInterval(()=>{void checkSystemStatus()},15000);
$('attachButton').addEventListener('click',()=>$('attachInput').click());
$('attachInput').addEventListener('change',async(e)=>{
 const file=e.target.files?.[0];if(!file)return;
 const feedback=$('uploadFeedback');feedback.hidden=false;
 if(file.size>200_000_000){feedback.textContent='Arquivo acima do limite de 200 MB. Para arquivos maiores, use Ferramentas → Biblioteca e importe da pasta autorizada.';e.target.value='';return;}
 if(!/\.(txt|md|pdf|csv|json|log)$/i.test(file.name)){feedback.textContent='Formato não permitido. Use TXT, MD, PDF, CSV, JSON ou LOG.';e.target.value='';return;}
 feedback.textContent=`Enviando ${file.name} (${(file.size/1e6).toFixed(1)} MB)…`;
 try{
  // O browser transmite o File diretamente, sem file.arrayBuffer()/Base64.
  const url='/api/v1/utilities/upload-stream?filename='+encodeURIComponent(file.name);
  const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
  const data=await res.json();
  if(!res.ok)throw Error(data.detail||`HTTP ${res.status}`);
  feedback.textContent=`${file.name} salvo na pasta autorizada (${(data.bytes/1e6).toFixed(1)} MB). Para usar no acervo, abra Ferramentas → Biblioteca e importe o arquivo existente.`;
 }catch(err){feedback.textContent=`Não foi possível enviar: ${err.message}`}
 finally{e.target.value=''}
});
$('settingsIcon').addEventListener('click',()=>{$('systemPanel').classList.remove('open')});
boot().then(checkSystemStatus).catch(e=>{addError('Campanário indisponível: '+e.message);updateSystemStatus('offline')});

