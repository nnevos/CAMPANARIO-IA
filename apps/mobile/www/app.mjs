import {emptyState,loadState,saveState,eraseState,newMutation,applySync,outgoing,searchItems} from './store.mjs';
import {request,normalizeServer,checkRelease,VERSION} from './transport.mjs';

const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state=emptyState(),view='chat',currentChat=null,editingNote=null,connected=false,sending=false,syncing=false,toastTimer,writeQueue=Promise.resolve(),storageReady=false;
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,7000);}
function persist(change){
  if(!storageReady)return Promise.reject(new Error("Armazenamento indisponivel. Nenhum dado sera sobrescrito."));
  writeQueue=writeQueue.catch(()=>{}).then(async()=>{const before=structuredClone(state);try{change(state);await saveState(state);}catch(e){state=before;throw e;}});
  return writeQueue;
}
function confirmAction(title,text,phrase){
  const dialog=$('confirmDialog');$('confirmTitle').textContent=title;$('confirmText').textContent=text;$('confirmLabel').textContent='Digite '+phrase;$('confirmInput').value='';$('confirmAccept').disabled=true;
  return new Promise(resolve=>{let done=false;const finish=value=>{if(done)return;done=true;dialog.close();resolve(value);};$('confirmInput').oninput=()=>$('confirmAccept').disabled=$('confirmInput').value!==phrase;$('confirmCancel').onclick=()=>finish(false);$('confirmAccept').onclick=()=>{if($('confirmInput').value===phrase)finish(true);};dialog.oncancel=()=>finish(false);dialog.showModal();$('confirmInput').focus();});
}
function setSigils(next='idle') {for(const id of ['morgana','todd','campanario']){const node=$(id==='campanario'?'coreSigil':id+'Sigil');node.src='assets/'+id+'_'+next+'.svg';}}
function connectionKey(){return state.connection?state.connection.server+'|'+state.connection.device_id:'';}
function chat(){return state.chats.find(c=>c.id===currentChat);}
function setView(next){view=next;for(const name of ['chat','library','notes','gps','settings'])$(name+'View').hidden=name!==next;$('composer').hidden=next!=='chat';document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===next));if(next==='chat')renderChat();if(next==='library')renderLibrary();if(next==='notes')renderNotes();if(next==='settings')renderSettings();if(next==='gps')renderGps();else stopGps();}
function statusLabel(){return connected?'PC conectado - processamento no PC':'Modo local - IA do PC desconectada';}
function renderChat(){
  const item=chat(),host=$('messages');host.replaceChildren();
  const messages=[...(item?.messages||[]),...(item?.pending||[]).map(p=>({role:'user',content:p.text,pending:p.state}))];
  for(const m of messages){
    const name=m.role==='user'?'Voce':m.agent_id==='todd'?'Todd':'Morgana';
    const node=document.createElement('article');node.className='message '+(m.role==='user'?'user':m.agent_id||'morgana')+(m.pending?' draft':'');
    const meta=document.createElement('div');meta.className='meta';
    if(m.role!=='user'){const img=document.createElement('img');img.src='assets/'+(m.agent_id==='todd'?'todd':'morgana')+'_idle.svg';img.alt='';meta.append(img);}
    const label=document.createElement('span');label.textContent=name+(m.pending?' / '+({draft:'rascunho local',sending:'enviando',uncertain:'envio incerto'}[m.pending]||m.pending):'');meta.append(label);node.append(meta);
    const content=document.createElement('div');content.textContent=m.content;node.append(content);host.append(node);
  }
  $('chatState').textContent=sending?'Processando no PC...':statusLabel();
  const actions=$('draftActions');actions.replaceChildren();
  const pending=item?.pending||[];
  if(pending.some(p=>p.state==='draft')){const b=document.createElement('button');b.textContent='Enviar rascunhos ao PC';b.disabled=!connected||sending;b.onclick=sendDrafts;actions.append(b);}
  if(item?.remoteId&&item.owner===connectionKey()){const b=document.createElement('button');b.textContent='Recuperar conversa do PC';b.disabled=!connected||sending;b.onclick=()=>recover().catch(e=>toast(e.message));actions.append(b);}
  $('send').disabled=sending;$('newChat').disabled=sending;$('historyOpen').disabled=sending;
  $('main').scrollTop=$('main').scrollHeight;
}
async function ensureChat(){if(currentChat)return;currentChat=crypto.randomUUID();const id=currentChat;await persist(s=>s.chats.push({id,remoteId:null,owner:'',title:'Nova conversa',created:Date.now(),messages:[],pending:[]}));}
async function sendText(text){
  if(sending)return;await ensureChat();const id=currentChat;
  const pending={id:crypto.randomUUID(),text,state:'draft'};
  await persist(s=>{const c=s.chats.find(c=>c.id===id);c.pending.push(pending);if(c.title==='Nova conversa')c.title=text.slice(0,55);});
  $('prompt').value='';renderChat();
  if(connected)await deliver(pending.id);else toast('Rascunho salvo no aparelho. Nenhuma IA local do celular esta instalada. O envio ao PC exige sua acao.');
}
async function deliver(pendingId){
  const item=chat();if(!item||sending)return;
  if(!state.connection?.chat_allowed){toast('Este dispositivo nao tem autorizacao para usar o chat do PC.');return;}
  if(item.owner&&item.owner!==connectionKey()){toast('Esta conversa pertence a outro pareamento. Abra uma nova conversa.');return;}
  sending=true;setSigils('thinking');renderChat();
  const id=item.id;let attempted=false;
  try{
    if(!item.remoteId){const response=await request(state.connection,'sessions',{client_id:id});await persist(s=>{const c=s.chats.find(c=>c.id===id);c.remoteId=response.id;c.owner=connectionKey();});}
    const target=state.chats.find(c=>c.id===id);const p=target?.pending.find(p=>p.id===pendingId);if(!p||p.state!=='draft')return;
    await persist(s=>s.chats.find(c=>c.id===id).pending.find(p=>p.id===pendingId).state='sending');
    attempted=true;
    const response=await request(state.connection,'sessions/'+state.chats.find(c=>c.id===id).remoteId+'/turn',{request_id:pendingId,message:p.text},150000);
    await persist(s=>{const c=s.chats.find(c=>c.id===id);c.messages=response.messages;c.pending=c.pending.filter(p=>p.id!==pendingId);});
  }catch(e){
    await persist(s=>{const p=s.chats.find(c=>c.id===id)?.pending.find(p=>p.id===pendingId);if(p)p.state=attempted?'uncertain':'draft';});
    toast(e.message+(attempted?' Use Recuperar conversa antes de reenviar.':''));
  }finally{sending=false;setSigils();renderChat();}
}
async function sendDrafts(){
  if(!await confirmAction('Enviar rascunhos','Os rascunhos serao enviados ao PC e poderao entrar no historico e na memoria do sistema.','ENVIAR'))return;
  const ids=(chat()?.pending||[]).filter(p=>p.state==='draft').map(p=>p.id);
  for(const id of ids){await deliver(id);if(chat()?.pending.some(p=>p.state==='uncertain'))break;}
}
async function recover(){
  const c=chat();if(!c?.remoteId)return;
  const id=c.id,completed=[];
  for(const p of c.pending.filter(p=>p.state==='sending'||p.state==='uncertain')){
    const result=await request(state.connection,'turns/'+p.id);
    if(result.state==='done')completed.push(p.id);
    else toast(result.state==='pending'?'O PC ainda nao confirmou o termino. Nenhum reenvio foi feito.':'O processamento falhou. Confira o historico antes de criar uma nova mensagem.');
  }
  const messages=await request(state.connection,'sessions/'+c.remoteId+'/messages');
  await persist(s=>{const target=s.chats.find(c=>c.id===id);target.messages=messages;target.pending=target.pending.filter(p=>!completed.includes(p.id));});renderChat();
}
function renderHistory(){
  const host=$('historyItems');host.innerHTML=state.chats.length?state.chats.slice().reverse().map(c=>`<div class="card note-row"><button data-chat="${esc(c.id)}">${esc(c.title)}<br><small>${new Date(c.created).toLocaleDateString('pt-BR')}</small></button><button data-delete-chat="${esc(c.id)}" class="danger" aria-label="Excluir copia local">&times;</button></div>`).join(''):'<p>Nenhuma conversa salva neste aparelho.</p>';
  host.querySelectorAll('[data-chat]').forEach(b=>b.onclick=()=>{if(sending)return;currentChat=b.dataset.chat;$('historyDialog').close();setView('chat');});
  host.querySelectorAll('[data-delete-chat]').forEach(b=>b.onclick=async()=>{if(sending)return;if(!await confirmAction('Excluir copia local','A conversa continua no PC. Esta acao apaga apenas a copia e os rascunhos deste aparelho.','EXCLUIR LOCAL'))return;await persist(s=>s.chats=s.chats.filter(c=>c.id!==b.dataset.deleteChat));if(currentChat===b.dataset.deleteChat)currentChat=null;renderHistory();renderChat();});
}
function renderLibrary(){
  const value=state.snapshot;$('snapshotInfo').textContent=value.revision?`Pacote ${value.revision} / ${value.items.length} itens / sincronizado em ${new Date(value.updated*1000).toLocaleString('pt-BR')}`:'Nenhum pacote baixado. Selecione conteudo no PC e sincronize este aparelho.';
  const items=searchItems(state,$('search').value);const host=$('libraryItems');host.replaceChildren();
  if(!items.length){const p=document.createElement('p');p.textContent='Nenhum resultado local.';host.append(p);return;}
  for(const item of items){const article=document.createElement('details');article.className='card';const summary=document.createElement('summary');summary.textContent=item.title;const source=document.createElement('small');source.textContent=item.source||'Conteudo selecionado';const text=document.createElement('div');text.className='content';text.textContent=item.text;article.append(summary,source,text);host.append(article);}
}
function renderNotes(){
  const host=$('noteList');host.innerHTML=state.notes.filter(n=>!n.deleted||n.conflict).slice().reverse().map(n=>`<div class="card"><button data-note="${esc(n.id)}">${esc(n.title||'Sem titulo')}</button><p>${esc(n.body.slice(0,150))}</p><span class="badge">${n.conflict?'Conflito - copia local preservada':n.dirty?'Somente local / pendente':'Sincronizada'}</span>${n.conflict?`<div class="actions"><button data-copy-conflict="${esc(n.id)}">Preservar minha versao como nova nota</button></div>`:''}</div>`).join('')||'<p>Suas notas ficam neste aparelho. Nada e enviado sem sincronizacao.</p>';
  host.querySelectorAll('[data-note]').forEach(b=>b.onclick=()=>editNote(b.dataset.note));
  host.querySelectorAll('[data-copy-conflict]').forEach(b=>b.onclick=async()=>{const id=b.dataset.copyConflict;await persist(s=>{const n=s.notes.find(n=>n.id===id),remote=n.conflict;s.notes.push(newMutation({},{title:n.title+' (copia local)',body:n.body,deleted:false}));if(remote?.id)Object.assign(n,remote,{base_revision:remote.revision,dirty:false,conflict:null,deleted:!!remote.deleted});else s.notes=s.notes.filter(n=>n.id!==id);});renderNotes();});
}
function editNote(id=null){editingNote=id;const note=state.notes.find(n=>n.id===id);$('noteTitle').value=note?.title||'';$('noteBody').value=note?.body||'';$('noteFeedback').textContent='';$('deleteNote').hidden=!note;$('noteDialog').showModal();}
async function sync(){
  if(syncing)return;if(!state.connection?.token){toast('Pareie o aparelho antes de sincronizar.');return;}
  syncing=true;toast('Sincronizando notas e pacote selecionado...');
  try{
    const response=await request(state.connection,'notes/sync',{mutations:outgoing(state.notes)});
    await persist(s=>s.notes=applySync(s.notes,response));
    const snapshot=await request(state.connection,'snapshot');
    if(!Array.isArray(snapshot.items)||snapshot.items.some(i=>typeof i.text!=='string'||typeof i.title!=='string'))throw new Error('Pacote invalido; conteudo anterior preservado');
    await persist(s=>s.snapshot=snapshot);connected=true;
    toast(response.results.some(r=>r.status==='conflict')?'Sincronizacao concluida com conflitos. As duas versoes foram preservadas.':'Notas e pacote offline sincronizados. Nenhum rascunho de chat foi enviado.');
  }catch(e){connected=false;toast(e.message);}finally{syncing=false;setView(view);}
}
async function connectStatus(){
  if(!state.connection?.token){connected=false;return;}
  try{const result=await request(state.connection,'status');connected=true;await persist(s=>s.connection.chat_allowed=result.chat_allowed);}
  catch(e){connected=false;toast(e.message);}setView(view);
}
function renderSettings(){
  const server=state.connection?.server||'';
  $('settingsView').innerHTML=`<h1>Conexao e autonomia</h1><div class="connection-status">${esc(statusLabel())}</div><div class="card"><h2>Servidor no PC</h2><p>Conecte por HTTPS. A interface e os dados baixados continuam disponiveis sem o PC.</p><label>Endereco do servidor<input id="serverAddress" type="url" placeholder="https://seu-pc:8443" value="${esc(server)}" autocapitalize="none"></label><label>Codigo gerado nas configuracoes do PC<input id="pairCode" autocomplete="off" autocapitalize="none"></label><div class="actions"><button id="pairButton">Parear aparelho</button><button id="connectButton">Testar conexao</button><button id="syncButton">Sincronizar agora</button></div><p>${window.CampanarioNative?'Armazenamento local protegido pelo Android Keystore.':'Modo de pre-visualizacao: dados locais sem criptografia e credencial somente nesta sessao.'}</p></div><div class="notice">Offline: notas, consulta textual do pacote baixado, historico em cache e rascunhos. IA no proprio celular, TTS novo e mapas offline ainda nao estao instalados. GPS local disponivel na aba GPS em Android. Sem PC, o app nao inventa respostas.</div><div class="card"><h2>Atualizacoes</h2><p>Versao ${VERSION}. Sem executar a branch principal ou substituir codigo silenciosamente.</p><label>Repositorio publico do GitHub<input id="releaseRepo" value="${esc(state.repository)}" placeholder="dono/repositorio" autocapitalize="none"></label><button id="checkRelease">Verificar release</button><p id="releaseStatus"></p><div id="releaseAction"></div></div><div class="card"><h2>Privacidade</h2><p>Apagar dados locais nao apaga conversas, notas ou backups existentes no PC. Revogue o dispositivo no PC para encerrar seu acesso.</p><button id="eraseLocal" class="danger">Apagar todos os dados deste aparelho</button></div>`;
  $('pairButton').onclick=async()=>{
    if(sending||syncing){toast('Finalize a operacao atual primeiro.');return;}
    try{
      const address=normalizeServer($('serverAddress').value.trim()),code=$('pairCode').value.trim();
      if(state.connection&&!await confirmAction('Trocar pareamento','A biblioteca em cache sera substituida. Notas locais serao preservadas e so irao para o novo dispositivo quando voce sincronizar.','TROCAR'))return;
      const result=await request({server:address},'pair',{code});
      await persist(s=>{s.connection={server:address,...result};s.snapshot={revision:0,items:[],updated:null};s.notes=s.notes.filter(n=>!n.deleted).map(n=>newMutation({...n,base_revision:0},{deleted:false}));});connected=true;toast('Pareado. Selecione o conteudo no PC e sincronize.');renderSettings();
    }catch(e){toast(e.message);}
  };
  $('connectButton').onclick=()=>connectStatus().catch(e=>toast(e.message));$('syncButton').onclick=sync;
  $('checkRelease').onclick=async()=>{try{const repository=$('releaseRepo').value.trim();const result=await checkRelease(repository);await persist(s=>s.repository=repository);$('releaseStatus').textContent=`Release ${result.version}: ${result.available?'atualizacao disponivel':'nenhuma versao mais nova'}.`;$('releaseAction').replaceChildren();if(result.available){const b=document.createElement('button');b.textContent='Abrir release para baixar APK';b.onclick=()=>{if(window.CampanarioNative)window.CampanarioNative.openRelease(result.url);else window.open(result.url,'_blank','noopener,noreferrer');};$('releaseAction').append(b);}}catch(e){$('releaseStatus').textContent=e.message;}};
  $('eraseLocal').onclick=async()=>{if(sending||syncing){toast('Finalize a operacao atual primeiro.');return;}if(!await confirmAction('Apagar dados locais','Notas nao sincronizadas, rascunhos, credencial e pacote offline serao removidos deste aparelho. Esta acao nao afeta o PC.','APAGAR LOCAL'))return;await writeQueue.catch(()=>{});await eraseState();state=emptyState();storageReady=true;currentChat=null;connected=false;setView('chat');toast('Dados locais removidos.');};
}
$('composer').onsubmit=e=>{e.preventDefault();const text=$('prompt').value.trim();if(text)sendText(text).catch(e=>toast(e.message));};
$('newChat').onclick=()=>{currentChat=null;setView('chat');};$('settingsOpen').onclick=()=>setView('settings');
$('historyOpen').onclick=()=>{renderHistory();$('historyDialog').showModal();};
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
$('search').oninput=renderLibrary;$('newNote').onclick=()=>editNote();$('syncNotes').onclick=sync;
$('noteForm').onsubmit=async e=>{e.preventDefault();try{const id=editingNote,title=$('noteTitle').value,body=$('noteBody').value;await persist(s=>{const index=s.notes.findIndex(n=>n.id===id),note=newMutation(index<0?{}:s.notes[index],{title,body,deleted:false});if(index<0)s.notes.push(note);else s.notes[index]=note;});$('noteDialog').close();renderNotes();}catch(e){$('noteFeedback').textContent=e.message;}};
$('deleteNote').onclick=async()=>{if(!await confirmAction('Apagar nota','A remocao sera sincronizada como registro de exclusao. Backups e copias externas nao sao apagados.','APAGAR'))return;await persist(s=>{const index=s.notes.findIndex(n=>n.id===editingNote);s.notes[index]=newMutation(s.notes[index],{body:'',title:'',deleted:true});});$('noteDialog').close();renderNotes();};
window.addEventListener('offline',()=>{connected=false;renderChat();});
try{state=await loadState();storageReady=true;for(const c of state.chats)for(const p of c.pending||[])if(p.state==='sending')p.state='uncertain';setView('chat');if(state.connection?.token)void connectStatus();}
catch(e){$('send').disabled=true;$('chatState').textContent=e.message;toast(e.message);}

// GPS opt-in: only one-shot foreground samples. Never transmit coordinates to the PC.
let gpsTrack=[], gpsTimer=null, gpsBusy=false;
function stopGps(){if(gpsTimer){clearInterval(gpsTimer);gpsTimer=null;}if($('gpsStart'))$('gpsStart').disabled=false;if($('gpsStop'))$('gpsStop').disabled=true;}
function renderGps(){if(!$('gpsView'))return;$('gpsCount').textContent=gpsTrack.length+' pontos nesta sessão';$('gpsStart').disabled=!!gpsTimer;$('gpsStop').disabled=!gpsTimer;renderGpsPlot();}
function renderGpsPlot(){
  const svg=$('gpsPlot');if(!svg)return;
  const ns='http://www.w3.org/2000/svg';svg.replaceChildren();
  const add=(tag,attrs)=>{const e=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));svg.append(e);return e;};
  if(!gpsTrack.length){add('text',{x:160,y:130,'text-anchor':'middle',fill:'#a5a8b0','font-size':12}).textContent='Sem pontos registrados';$('gpsPlotInfo').textContent='';return;}
  // Equirectangular projection around the mean latitude, suitable for local track preview.
  const lat0=gpsTrack.reduce((a,p)=>a+p.lat,0)/gpsTrack.length*Math.PI/180;
  const coords=gpsTrack.map(p=>[p.lon*Math.cos(lat0),p.lat]);
  const xs=coords.map(p=>p[0]),ys=coords.map(p=>p[1]);
  const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const span=Math.max(xmax-xmin,ymax-ymin,0.000001);
  const plot=coords.map(([x,y])=>[160+(x-(xmin+xmax)/2)/span*270,130-(y-(ymin+ymax)/2)/span*210]);
  add('polyline',{points:plot.map(p=>p.join(',')).join(' '),fill:'none',stroke:'#cfb779','stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'});
  for(const [point,color] of [[plot[0],'#49d39a'],[plot[plot.length-1],'#e14b4b']])add('circle',{cx:point[0],cy:point[1],r:5,fill:color,stroke:'#101317','stroke-width':2});
  $('gpsPlotInfo').textContent=`${gpsTrack.length} ponto(s) • início verde, fim vermelho • orientação norte para cima`;
}

window.CampanarioGpsResult = function(raw){
  gpsBusy=false;
  try{
    const p=JSON.parse(raw);
    if(p.status!=='ok'){$('gpsStatus').textContent='GPS: '+p.status.replaceAll('_',' ');return;}
    if(!Number.isFinite(p.lat)||!Number.isFinite(p.lon)||Math.abs(p.lat)>90||Math.abs(p.lon)>180)throw Error('Coordenadas inválidas');
    const age=Date.now()-p.timestamp;
    if(age< -60000||age>120000){$('gpsStatus').textContent='Posição desatualizada; tente novamente.';return;}
    const accuracy=Number.isFinite(p.accuracy)?Math.round(p.accuracy)+' m':'não informada';
    $('gpsStatus').textContent='Posição recebida • '+new Date(p.timestamp).toLocaleTimeString()+(p.mock?' • localização simulada':'');
    $('gpsPosition').textContent=`Latitude: ${p.lat.toFixed(6)} | Longitude: ${p.lon.toFixed(6)} | Precisão: ${accuracy}`;
    if(gpsTimer && !p.mock && (!gpsTrack.length || p.timestamp>gpsTrack[gpsTrack.length-1].timestamp)) {
      gpsTrack.push({lat:p.lat,lon:p.lon,accuracy:p.accuracy,timestamp:p.timestamp});
      if(gpsTrack.length>=1000){stopGps();toast('Limite de 1000 pontos atingido. Exporte a trilha.');}
      renderGps();
    }
  }catch(e){$('gpsStatus').textContent='Erro ao ler localização: '+e.message;}
};
function gpsSample(){if(gpsBusy)return;if(!window.CampanarioNative?.requestGpsOnce){$('gpsStatus').textContent='GPS requer o aplicativo Android instalado; indisponível nesta prévia.';return;}gpsBusy=true;$('gpsStatus').textContent='Aguardando posição do Android...';window.CampanarioNative.requestGpsOnce();setTimeout(()=>{if(gpsBusy){gpsBusy=false;$('gpsStatus').textContent='Sem resposta do GPS; verifique permissões e sinal.';}},20000);}
$('gpsGet').onclick=gpsSample;
$('gpsStart').onclick=()=>{if(gpsTimer)return;gpsTimer=setInterval(()=>{if(view==='gps' && !document.hidden)gpsSample();},10000);gpsSample();renderGps();};
$('gpsStop').onclick=()=>{stopGps();renderGps();};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopGps();});
$('gpsClear').onclick=async()=>{if(await confirmAction('Apagar trilha','Os pontos desta sessão serão removidos. Exporte antes se quiser guardar.','APAGAR GPS')){stopGps();gpsTrack=[];renderGps();$('gpsPosition').textContent='';}};
$('gpsExport').onclick=()=>{
  if(!gpsTrack.length){toast('Nenhuma posição registrada.');return;}
  const points=gpsTrack.map(p=>`<trkpt lat="${p.lat}" lon="${p.lon}"><time>${new Date(p.timestamp).toISOString()}</time>${Number.isFinite(p.accuracy)?`<extensions><accuracy>${p.accuracy}</accuracy></extensions>`:''}</trkpt>`).join('');
  const xml=`<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Campanario" xmlns="http://www.topografix.com/GPX/1/1"><trk><name>Campanario GPS</name><trkseg>${points}</trkseg></trk></gpx>`;
  if(window.CampanarioNative?.exportGpx)window.CampanarioNative.exportGpx(xml);else toast('Exportação GPX disponível somente no aplicativo Android.');
};

$('gpsShare').onclick=async()=>{
  if(!gpsTrack.length){toast('Registre uma trilha primeiro.');return;}
  if(!connected||!state.connection?.token){toast('Conecte o celular ao PC pareado para compartilhar.');return;}
  if(gpsTimer){toast('Pare a gravação antes de compartilhar.');return;}
  if(!await confirmAction('Compartilhar GPS','Enviar '+gpsTrack.length+' posições com horários e precisão ao PC pareado. O histórico ficará no PC até ser apagado manualmente.','COMPARTILHAR GPS'))return;
  const id=crypto.randomUUID();$('gpsShare').disabled=true;
  try{
    const result=await request(state.connection,'gps/tracks',{id,name:'Trilha '+new Date().toLocaleString('pt-BR'),points:gpsTrack,confirmation:'COMPARTILHAR GPS'},20000);
    toast(result.stored?'Trilha recebida pelo PC. Você pode apagar a cópia local separadamente.':'Envio não confirmado.');
  }catch(e){toast('Não foi possível confirmar o envio: '+e.message+' Confira no PC antes de tentar novamente.');}
  finally{$('gpsShare').disabled=false;}
};
