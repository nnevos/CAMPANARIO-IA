/* v0.6: accessible destructive confirmation, never a cosmetic-only delete. */
let dangerCallback=null;
function askDanger(title,description,phrase,callback){
 const d=$('dangerDialog');$('dangerTitle').textContent=title;$('dangerDescription').textContent=description;
 const f=$('dangerPhrase'),a=$('dangerAccept');f.value='';a.disabled=true;
 f.oninput=()=>{a.disabled=f.value!==phrase};a.onclick=async()=>{if(f.value!==phrase)return;a.disabled=true;try{await callback();d.close()}catch(e){$('dangerDescription').textContent='Falha: '+e.message+' — nenhuma confirmação adicional foi presumida';a.disabled=false}};
 $('dangerCancel').onclick=()=>d.close();d.showModal();f.focus();
}
async function deleteConversation(s){
 if(busy)return;
 askDanger('Excluir conversa',`A conversa “${s.title||'Sem título'}” e suas mensagens/resumo serão removidos do banco principal. Memórias aprendidas, backups e registros auxiliares NÃO são apagados. Esta ação não pode ser desfeita por esta interface. Digite EXCLUIR CONVERSA.`, 'EXCLUIR CONVERSA',async()=>{
  await api(`/api/v1/sessions/${encodeURIComponent(s.id)}`,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation:'EXCLUIR CONVERSA'})});
  if(sessionId===s.id)newConversation();await refreshSessions();
 });
}
let memoryItems=[];
function setupMemoryManager(){
 const host=$('settingsView');if(!host||!host.querySelector('[data-stab="memoria"].selected'))return;
 const target=host.querySelector('.workspace-card:last-child')||host;
 if(target.querySelector('#memoryManager'))return;
 const box=document.createElement('section');box.id='memoryManager';box.className='memory-manager';box.innerHTML=`<h3>Memórias de experiência</h3><p>Você controla o que o Campanário recupera nesta camada. <strong>Esquecer é uma exclusão lógica:</strong> o registro é marcado como esquecido e removido do índice semântico associado; não equivale a apagar fisicamente registros, utilidades, conversas ou backups.</p><div class="memory-actions"><button type="button" id="memoryReload">↻ Atualizar</button><button type="button" id="memorySelectDelete" class="danger" disabled>Esquecer selecionadas</button><button type="button" id="memoryAllDelete" class="danger" disabled>Esquecer todas</button></div><div id="memoryNotice" class="inline-status"></div><div class="memory-list" id="memoryList"></div><p>Para memórias declaradas na camada de utilidades, utilize <a href="/ferramentas#memoria" style="color:#e2bf76">Ferramentas → Memórias</a>. Os dois armazenamentos são independentes.</p>`;
 target.append(box);$('memoryReload').onclick=loadMemoryManager;$('memorySelectDelete').onclick=forgetSelected;$('memoryAllDelete').onclick=forgetAll;void loadMemoryManager();
}
async function loadMemoryManager(){const el=$('memoryList');if(!el)return;el.textContent='Consultando memórias locais…';try{
 memoryItems=await api('/api/v1/memory?limit=1000');el.replaceChildren();const active=memoryItems.filter(x=>x.status==='active');$('memoryAllDelete').disabled=!active.length;
 if(!active.length){el.textContent='Nenhuma memória ativa nesta camada.';return}
 for(const m of active){const lab=document.createElement('label');lab.className='memory-item';const cb=document.createElement('input');cb.type='checkbox';cb.value=m.id;cb.onchange=()=>{$('memorySelectDelete').disabled=!el.querySelector('input:checked')};const content=document.createElement('div');content.textContent=m.value;const note=document.createElement('span');note.textContent=`${m.subject} · ${m.key} · ${m.source}`;content.append(note);lab.append(cb,content);el.append(lab)}
 $('memorySelectDelete').disabled=true;$('memoryNotice').textContent=`${active.length} memórias ativas exibidas${active.length===1000?' (limite de listagem de 1000)':''}.`;
 }catch(e){el.textContent='Não foi possível listar memórias: '+e.message;}}
function forgetSelected(){const ids=Array.from($('memoryList').querySelectorAll('input:checked')).map(x=>x.value);if(!ids.length)return;
 askDanger('Esquecer memórias selecionadas',`Serão marcadas como esquecidas ${ids.length} memória(s) de experiência. Não apaga backups, conversas ou registros de outras camadas. Digite ESQUECER MEMORIAS.`, 'ESQUECER MEMORIAS',async()=>{
  await api('/api/v1/memory/forget-selected',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation:'ESQUECER MEMORIAS',ids})});await loadMemoryManager();
 });
}
function forgetAll(){askDanger('Esquecer todas as memórias de experiência', 'Esta operação marca TODAS as memórias ativas desta camada como esquecidas, incluindo itens além dos exibidos na listagem. Não apaga conversas, memórias das utilidades, backups ou registros físicos de auditoria. Digite ESQUECER TODAS AS MEMORIAS.', 'ESQUECER TODAS AS MEMORIAS',async()=>{
 await api('/api/v1/memory/forget-all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation:'ESQUECER TODAS AS MEMORIAS'})});await loadMemoryManager();
 });}
$('sidebarClose').onclick=closeSidebar;window.addEventListener('keydown',e=>{if(e.key==='Escape')closeSidebar()});
$('memoryShortcut').onclick=()=>{document.querySelector('[data-view="settings"]')?.click();setTimeout(()=>{document.querySelector('[data-stab="memoria"]')?.click();closeSidebar()},0)};
document.querySelectorAll('[data-suggestion]').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.suggestion;$('prompt').focus()});
// Observe real settings renders without modifying other settings tabs.
const settingsObserver=new MutationObserver(()=>{if($('settingsView').querySelector('[data-stab="memoria"].selected'))setupMemoryManager()});
settingsObserver.observe($('settingsView'),{childList:true,subtree:false});

