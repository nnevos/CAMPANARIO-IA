/* Desktop administration: local-only API. No credentials in localStorage or logs. */
(() => {
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const request = async (path, body) => api('/api/app/' + path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  function section(card, id, title) {
    if (document.getElementById(id)) return null;
    const node = document.createElement('section'); node.id=id;node.className='app-section';
    node.innerHTML=`<h3>${escape(title)}</h3>`;card.append(node);return node;
  }
  function message(node, text) { const out=node.querySelector('.app-message'); if(out)out.textContent=text; }
  function button(node, selector, run) {
    const element=node.querySelector(selector);
    if (!element) return;
    element.onclick=async()=>{element.disabled=true;try{await run();}catch(e){message(node,e.message);}finally{element.disabled=false;}};
  }
  function renderMobile(card) {
    const node=section(card,'mobileAdmin','Pareamento e acesso');if(!node)return;
    node.innerHTML+=`<div class="notice">O servidor mobile fica desligado por padrao. HTTPS e certificado confiavel sao obrigatorios. Revogar acesso nao apaga copias que ja foram baixadas no celular.</div>
    <details><summary>Configurar listener HTTPS</summary><div class="app-form">
    <label>IP de escuta<input id="remoteHost" value="0.0.0.0"></label><label>Porta<input id="remotePort" type="number" value="8443"></label>
    <label>Certificado PEM (caminho no PC)<input id="remoteCert" placeholder="C:\\certificados\\servidor.pem"></label>
    <label>Chave privada PEM (caminho no PC)<input id="remoteKey" placeholder="C:\\certificados\\servidor-key.pem"></label>
    </div><div class="app-actions"><button class="ui-btn" id="remoteStart">Ativar acesso mobile</button><button class="ui-btn" id="remoteStop">Desligar acesso</button></div></details>
    <p id="remoteState">Consultando listener...</p>
    <div class="app-form"><label>Nome do dispositivo<input id="pairName" maxlength="80" value="Meu celular"></label>
    <label><input type="checkbox" id="pairChat"> Autorizar chat com a IA e as memorias do PC (alem do pacote selecionado)</label></div>
    <div class="app-actions"><button class="ui-btn gold" id="pairCreate">Gerar codigo de pareamento</button><button class="ui-btn" id="devicesReload">Atualizar dispositivos</button></div>
    <div class="app-message" role="status" aria-live="polite"></div><div id="pairedDevices"></div><div id="deviceDetails"></div>`;
    async function refresh(){
      const [remote,devices]=await Promise.all([request('remote'),request('devices')]);
      node.querySelector('#remoteState').textContent=remote.running?'Listener ativo: '+remote.listen:'Listener desligado. O chat local continua disponivel.';
      const list=node.querySelector('#pairedDevices');list.innerHTML=devices.length?devices.map(d=>`<div class="setting-row"><span>${escape(d.name)} <span class="app-badge">${d.revoked?'revogado':'pareado'}</span></span><div class="app-actions"><button class="ui-btn" data-device="${escape(d.id)}" ${d.revoked?'disabled':''}>Conteudo offline</button><button class="ui-btn" data-revoke="${escape(d.id)}" ${d.revoked?'disabled':''}>Revogar</button></div></div>`).join(''):'<p>Nenhum celular pareado.</p>';
      list.querySelectorAll('[data-device]').forEach(b=>b.onclick=()=>details(b.dataset.device).catch(e=>message(node,e.message)));
      list.querySelectorAll('[data-revoke]').forEach(b=>b.onclick=()=>askDanger('Revogar dispositivo','O celular perde acesso ao servidor. Conteudo offline ja baixado nao pode ser apagado remotamente.','REVOGAR',async()=>{await request(`devices/${b.dataset.revoke}/revoke`,{confirmation:'REVOGAR'});await refresh();}));
    }
    async function details(id){
      const [memories,sessions,notes]=await Promise.all([api('/api/v1/memory'),api('/api/v1/sessions'),request(`devices/${id}/notes`)]);
      const host=node.querySelector('#deviceDetails');host.innerHTML=`<h3>Publicar pacote para este dispositivo</h3><p>A selecao substitui o pacote anterior na proxima sincronizacao. Limite: 100 memorias, 30 conversas e 2 MB. Nenhum arquivo ou banco completo e exposto.</p><div class="app-selections">${memories.map(m=>`<label><input type="checkbox" data-memory="${escape(m.id)}"><span>Memoria: ${escape(m.key)} - ${escape(m.value).slice(0,180)}</span></label>`).join('')}${sessions.map(s=>`<label><input type="checkbox" data-session="${escape(s.id)}"><span>Conversa: ${escape(s.title||'Sem titulo')}</span></label>`).join('')}</div><div class="app-actions"><button class="ui-btn gold" id="publishOffline">Publicar selecao</button></div><h3>Notas recebidas do celular</h3><p>Notas sincronizadas nao viram memoria automaticamente.</p><div>${notes.notes.filter(n=>!n.deleted).map(n=>`<details><summary>${escape(n.title||'Nota')}</summary><p style="white-space:pre-wrap">${escape(n.body)}</p></details>`).join('')||'Nenhuma nota sincronizada.'}</div>`;
      host.querySelector('#publishOffline').onclick=()=>askDanger('Compartilhar conteudo','Estes itens ficarao acessiveis offline no celular. Uma selecao vazia publica um pacote vazio.','COMPARTILHAR',async()=>{
        const data={confirmation:'COMPARTILHAR',memory_ids:[...host.querySelectorAll('[data-memory]:checked')].map(e=>e.dataset.memory),session_ids:[...host.querySelectorAll('[data-session]:checked')].map(e=>e.dataset.session)};
        const result=await request(`devices/${id}/snapshot`,data);message(node,`Pacote ${result.revision} publicado: ${result.items} itens. Sincronize no celular.`);
      });
    }
    button(node,'#pairCreate',async()=>{const result=await request('pairing',{name:node.querySelector('#pairName').value,allow_chat:node.querySelector('#pairChat').checked});message(node,`Codigo valido por 5 minutos, uma unica vez:\n${result.code}\nNo celular, informe o endereco HTTPS do PC e este codigo.`);});
    button(node,'#devicesReload',refresh);
    button(node,'#remoteStart',async()=>askDanger('Ativar acesso mobile','O listener expora somente a API mobile autenticada. Configure o firewall e um certificado HTTPS confiavel para o endereco informado no celular.','ATIVAR ACESSO MOBILE',async()=>{await request('remote/start',{host:node.querySelector('#remoteHost').value,port:Number(node.querySelector('#remotePort').value),certificate:node.querySelector('#remoteCert').value,private_key:node.querySelector('#remoteKey').value,confirmation:'ATIVAR ACESSO MOBILE'});message(node,'Inicializacao solicitada. Atualize os dispositivos para consultar o estado.');}));
    button(node,'#remoteStop',async()=>{await request('remote/stop',{});await refresh();});
    refresh().catch(e=>message(node,e.message));
    const gps=section(card,'gpsAdmin','Trilhas GPS recebidas');
    if(gps){
      gps.innerHTML+=`<p>Somente trilhas compartilhadas explicitamente pelo celular. Não são adicionadas à memória da IA.</p><button class="ui-btn" id="gpsReload">Atualizar trilhas</button><div id="gpsTrackList"></div><div class="app-message" role="status"></div>`;
      async function refreshGps(){
        const tracks=await request('gps/tracks');const list=gps.querySelector('#gpsTrackList');list.replaceChildren();
        if(!tracks.length){list.textContent='Nenhuma trilha compartilhada.';return;}
        for(const t of tracks){
          const item=document.createElement('div');item.className='setting-row';
          const summary=document.createElement('span');summary.textContent=`${t.name} • ${t.points.length} pontos • ${new Date(t.created*1000).toLocaleString('pt-BR')} • dispositivo ${t.device_id.slice(0,8)}`;
          const del=document.createElement('button');del.className='ui-btn';del.textContent='Apagar trilha';
          del.onclick=()=>askDanger('Apagar trilha GPS','Esta ação apaga a trilha recebida do PC, não a cópia no celular.','APAGAR GPS',async()=>{await request(`gps/tracks/${t.device_id}/${t.id}/delete`,{confirmation:'APAGAR GPS'});await refreshGps();});
          item.append(summary,del);list.append(item);
        }
      }
      button(gps,'#gpsReload',refreshGps);refreshGps().catch(e=>message(gps,e.message));
    }
  }
  function renderUpdates(card){
    const node=section(card,'updateAdmin','Releases do projeto');if(!node)return;
    node.innerHTML+=`<p>Verificacao manual. O aplicativo nao baixa codigo da branch principal e nao se substitui enquanto esta rodando.</p><div class="app-actions"><button class="ui-btn gold" id="checkUpdates">Verificar no GitHub</button></div><div class="app-message" role="status"></div><div id="releaseLink"></div>`;
    button(node,'#checkUpdates',async()=>{const result=await request('updates');message(node,result.configured?`Instalada: ${result.current}\nRelease: ${result.latest}\n${result.available?'Atualizacao disponivel.':'Nenhuma versao mais nova.'}`:result.message);const target=node.querySelector('#releaseLink');target.replaceChildren();if(result.available){const a=document.createElement('a');a.href=result.url;a.textContent='Abrir release verificada';a.target='_blank';a.rel='noopener noreferrer';a.className='ui-btn';target.append(a);}});
  }
  function renderDiagnostics(card){
    const node=section(card,'componentAdmin','Disponibilidade por componente');if(!node)return;
    node.innerHTML+=`<div class="app-actions"><button class="ui-btn" id="refreshComponents">Verificar agora</button></div><div class="app-message" role="status"></div><div id="components"></div>`;
    async function refresh(){const info=await request('status');node.querySelector('#components').innerHTML=Object.entries(info.components).map(([key,value])=>`<div class="setting-row"><span>${escape(key.toUpperCase())}</span><strong>${escape(value.state)}${value.name?' - '+escape(value.name):''}</strong></div>`).join('');message(node,'Voz e GPS novos ainda nao foram implementados. O indice semantico mostra configuracao; nao e um teste de embeddings.');}
    button(node,'#refreshComponents',refresh);refresh().catch(e=>message(node,e.message));
  }
  const target=document.getElementById('settingsView');
  function enhance(){const card=target.querySelector('.workspace-card');if(!card)return;const tab=target.querySelector('[data-stab].selected')?.dataset.stab;if(tab==='mobile')renderMobile(card);if(tab==='atualizacoes')renderUpdates(card);if(tab==='sistema')renderDiagnostics(card);}
  new MutationObserver(enhance).observe(target,{childList:true});
})();
