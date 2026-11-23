/* R3.3: Casework mounted INSIDE the native Database workspace. No new tab/program.
 * PF6 credentials and session tokens live only in this closure's memory.
 * All untrusted text rendered via textContent, never innerHTML.
 */
(function(){
 'use strict';
 let token='',current='',host=null,soloLocal=false;
 const root='/api/v1/cases';
 const el=(tag,text,attrs={})=>{const node=document.createElement(tag);if(text!==undefined&&text!==null)node.textContent=String(text);for(const[k,v]of Object.entries(attrs)){if(k==='class')node.className=v;else node.setAttribute(k,v)}return node};
 const btn=(text,fn)=>{const b=el('button',text,{type:'button',class:'ui-btn'});b.addEventListener('click',fn);return b};
 const field=(placeholder,type='text')=>el('input',null,{class:'workspace-input',type,placeholder,'aria-label':placeholder});
 const block=(...nodes)=>{const div=el('div',null,{class:'workspace-toolbar'});for(const n of nodes)div.appendChild(n);return div};
 function panel(){if(!host||!host.isConnected)return null;host.replaceChildren();return host}
 function note(text){const p=el('p',text,{class:'inline-status',role:'status'});host?.appendChild(p);return p}
 async function request(path,opts={}){
   const headers={...(token?{'Authorization':'Bearer '+token}:{}),...(opts.headers||{})};
   const response=await fetch(root+path,{...opts,headers,cache:'no-store',credentials:'same-origin'});
   const body=await response.json().catch(()=>({detail:'Resposta inválida do servidor'}));
   if(!response.ok){const e=new Error(typeof body.detail==='string'?body.detail:body.detail?.message||'Operação não autorizada');e.code=response.status;e.confirmation=body.detail?.confirmation_id;throw e;}
   return body;
 }
 async function write(path,content,description,headers={}){
  // Personal local mode: one deliberate click is enough; no PF6 dialog.
  const opts={method:'POST',body:content,headers};
  if(soloLocal)return await request(path,opts);
  try{return await request(path,opts)}catch(e){
   if(e.code!==428||!e.confirmation)throw e;
   return await new Promise((resolve,reject)=>{
    const modal=el('div',null,{class:'workspace-card',role:'group','aria-label':'Consentimento PF6'});
    modal.append(el('h3','Confirmar operação no caso'),el('p',description),el('p','Autorizar somente esta operação e seu conteúdo exato? A permissão expira e só vale uma vez.'));
    const controls=block(btn('Cancelar',()=>{modal.remove();reject(new Error('Operação cancelada'))}),btn('Autorizar esta operação',async()=>{
     try{
      const approval=await request('/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation_id:e.confirmation})});
      const output=await request(path,{...opts,headers:{...headers,'x-case-confirmation':approval.confirmation_token}});
      modal.remove();resolve(output);
     }catch(err){modal.remove();reject(err)}
    }));modal.appendChild(controls);host?.prepend(modal);
   });
  }
 }
 function error(e){note(e?.message||'Não foi possível concluir.');}
 function jsonWrite(path,obj,description){return write(path,JSON.stringify(obj),description,{'Content-Type':'application/json'});}
 async function mount(target){host=target;if(!panel())return;
  try{const r=await request('/mode');soloLocal=!!r.solo_local;
    if(soloLocal||token){await listing();return;}login();
  }catch(e){login();error(e)}
 }
 function login(){if(!panel())return;host.append(el('h2','Central de Casos · sessão segura'),el('p','Acesse usando uma identidade PF6 local configurada. Sem autenticação, não é possível consultar casos privados.'));
  const username=field('Usuário PF6 (vazio no modo proprietário)');const pass=field('Credencial PF6','password');
  host.append(block(username,pass),btn('Entrar na Central',async()=>{
   try{const body={credential:pass.value};if(username.value.trim())body.username=username.value.trim();
    const response=await fetch('/api/v1/utilities/sessions/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'same-origin'});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||'Falha de autenticação');token=data.session_token;pass.value='';await listing();
   }catch(e){error(e)}
  }));note('O modo com identidades PF6 configuradas requer autenticação. No modo pessoal local, o acesso é direto.');
 }
 function controls(){if(soloLocal){host.appendChild(block(btn('Casos',()=>listing())));return;}
  const div=block(btn('Casos',()=>listing()),btn('Sair da Central',async()=>{
  try{await fetch('/api/v1/utilities/sessions/logout',{method:'POST',headers:{Authorization:'Bearer '+token}})}catch(e){}token='';current='';login();
 }));host.appendChild(div);}
 async function listing(){try{const data=await request('');if(!panel())return;host.append(el('h2','Casos de investigação'));controls();
  const title=field('Título do caso'),objective=field('Objetivo do caso');host.append(block(title,objective),btn('Criar caso',async()=>{
   try{const output=await jsonWrite('',{title:title.value,objective:objective.value},'Criar novo caso: '+title.value);await showCase(output.case_id)}catch(e){error(e)}
  }));
  const list=el('div');for(const item of data.items||[]){const b=btn(item.title,()=>showCase(item.case_id));list.append(b,el('small',' '+item.created_at),el('hr'));}host.append(list);
  if(!data.items?.length)note('Nenhum caso cadastrado no Database externo.');
 }catch(e){if(e.code===401&&!soloLocal){token='';login()}else{panel();note('Central indisponível: '+e.message)}}}
 async function showCase(id){try{current=id;const data=await request('/'+id),review=await request('/'+id+'/review');if(!panel())return;
  host.append(el('h2',data.title),el('p',data.objective));controls();
  host.append(el('p',`Evidências: ${data.evidence.length} · Eventos: ${data.events.length} · Hipóteses: ${data.hypotheses.length} · Integridade: ${review.integrity_ok?'OK':'FALHA'}`));
  host.append(el('h3','Importar evidência (cópia preservada)'));
  const file=field('Escolher arquivo','file');file.accept='.csv,.json,.txt,.log,.pdf,.xlsx,.jpg,.jpeg,.png,.zip,.md,.docx,.html,.htm';
  const origin=field('Origem declarada da evidência');host.append(block(file,origin),btn('Importar evidência',async()=>{
   try{const f=file.files?.[0];if(!f)throw new Error('Selecione um arquivo');if(f.size>1024*1024*1024)throw new Error('Arquivo excede capacidade de 1 GiB');
    await write('/'+id+'/evidence',f,'Importar '+f.name+' com origem: '+origin.value,
     {'Content-Type':'application/octet-stream','x-case-filename':encodeURIComponent(f.name),'x-case-origin':encodeURIComponent(origin.value)});await showCase(id)
   }catch(e){error(e)}
  }));
  host.append(el('h3','Evidências'));for(const e of data.evidence){host.append(el('p',`${e.id} · ${e.filename} · ${e.status} · SHA-256: ${e.sha256}`));
   if(/\.(csv|json)$/i.test(e.filename)){const proposals=el('div');host.append(btn('Revisar registros propostos de '+e.id,async()=>{
     try{const answer=await request('/'+id+'/evidence/'+e.id+'/proposed-events');proposals.replaceChildren();
      for(const event of answer.items||[]){const item=el('div',null,{class:'workspace-card'});
       item.append(el('p',event.date_time+' — '+event.description+' (proposta, não verificada)'),btn('Registrar somente este evento',async()=>{
        try{await jsonWrite('/'+id+'/events',{date_time:event.date_time,description:event.description,evidence_ids:[e.id],classification:'reported'},'Registrar evento proposto de '+e.id+' linha '+event.row);await showCase(id)}catch(err){error(err)}
       }));proposals.append(item)}if(!answer.items?.length)proposals.append(el('p','Nenhum registro estruturado reconhecido'));
     }catch(err){error(err)}}),proposals)}
  }
  host.append(el('h3','Cronologia'));for(const event of data.events)host.append(el('p',`${event.date_time} — ${event.description} [${event.evidence_ids.join(', ')}]`));
  const stamp=field('Data/hora ISO 8601 com fuso'),description=field('Descrição declarada'),refs=field('IDs das evidências (separados por vírgula)');
  host.append(block(stamp,description,refs),btn('Registrar evento',async()=>{
   try{await jsonWrite('/'+id+'/events',{date_time:stamp.value,description:description.value,evidence_ids:refs.value.split(',').map(s=>s.trim()).filter(Boolean),classification:'reported'},'Registrar evento '+description.value);await showCase(id)}catch(e){error(e)}
  }));
  host.append(el('h3','Hipóteses não confirmadas'));for(const h of data.hypotheses)host.append(el('p',`${h.statement} · Próxima verificação: ${h.next_check}`));
  const hypothesis=field('Hipótese a verificar'),pro=field('IDs a favor (separados por vírgula)'),con=field('IDs contra (separados por vírgula)'),check=field('Próxima verificação');
  host.append(block(hypothesis,pro,con,check),btn('Registrar hipótese',async()=>{
   try{await jsonWrite('/'+id+'/hypotheses',{statement:hypothesis.value,supporting:pro.value.split(',').map(x=>x.trim()).filter(Boolean),opposing:con.value.split(',').map(x=>x.trim()).filter(Boolean),next_check:check.value},'Registrar hipótese '+hypothesis.value);await showCase(id)}catch(e){error(e)}
  }));
  host.append(el('h3','Conversa factual sobre este caso'));
  const q=field('Pergunte sobre contratos, logs, conteúdos, divergências, cronologia ou hipóteses');
  const who=el('select',null,{class:'workspace-input','aria-label':'Agente que apresenta'});
  for(const [id,label] of [['morgana','Morgana'],['todd','Todd']]){const op=el('option',label);op.value=id;who.append(op)}
  const transcript=el('div',null,{class:'workspace-card','aria-live':'polite'});
  host.append(block(q,who,btn('Perguntar no Campanário',async()=>{
    try{const value=q.value.trim();if(!value)throw Error('Digite uma pergunta');
      const result=await request('/'+id+'/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:value,agent_id:who.value})});
      transcript.append(el('p','Você: '+value),el('pre',result.answer,{style:'white-space:pre-wrap;overflow-wrap:anywhere'}));q.value='';
    }catch(e){error(e)}
  })),el('p','Para usar no chat principal: mantenha este caso selecionado e escreva “Caso: qual a cronologia?” ou “Todd, no caso, quais as hipóteses?”. Os trechos dos originais são citados por evidência e linha quando recuperáveis; respostas são somente leitura e não são gravadas no histórico geral.'),transcript);
  host.append(el('h3','Revisão e dossiê'));const report=el('pre',null,{style:'white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow:auto'});
  host.append(block(btn('Ver análise',()=>{report.textContent=JSON.stringify(review,null,2)}),btn('Ver dossiê',async()=>{try{report.textContent=(await request('/'+id+'/dossier')).markdown}catch(e){error(e)}}),btn('Baixar dossiê',async()=>{
   try{const content=(await request('/'+id+'/dossier')).markdown;const blob=new Blob([content],{type:'text/markdown;charset=utf-8'});const url=URL.createObjectURL(blob);const a=el('a');a.href=url;a.download='caso-'+id+'.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}catch(e){error(e)}
  })),report);
 }catch(e){error(e)}}
 async function tryChat(text){
  // The operator must authenticate and select a case first. No implicit access.
  if(!/\bcaso\b/i.test(text)||!(/^(?:\s*(?:(?:morgana|todd)[,:]?\s*)?(?:no|sobre|do|deste|nesse)?\s*caso\b)|^\s*caso\s*:/i.test(text)))return null;
  if((!soloLocal&&!token)||!current)throw Error('Abra Database → Casos e selecione um caso antes de consultar pelo chat.');
  const agent_id=/\btodd\b/i.test(text)?'todd':'morgana';
  return await request('/'+current+'/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text,agent_id})});
 }
 window.CampanarioCases={mount,tryChat};
})();
