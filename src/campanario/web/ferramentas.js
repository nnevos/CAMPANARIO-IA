/* Campanario - local tools, no LLM dependency. All UI action results originate from API. */
(() => {
'use strict';
const modules = [
 ['inicio','⌂','Visão geral','Acesso rápido ao seu espaço local'],
 ['arquivos','▤','Arquivos','Navegue, pesquise e organize com segurança'],
 ['pesquisa','◎','Pesquisa Web','Busque informações atuais e confira suas fontes'],
 ['biblioteca','▣','Biblioteca','Documentos pesquisáveis sem internet'],
 ['documentos','▤','Documentos','Metadados, extração e originais preservados'],
 ['analises','∑','Análises','Cálculos locais e evidências tabulares'],
 ['cerebros','◈','Central de Cérebros','Capacidades instaladas, saúde e execuções reais'],
 ['forja','⚒','Forja de Agentes','Arquétipos e talentos sem mudar personalidades'],
 ['notas','✎','Notas','Anotações que permanecem salvas'],
 ['tarefas','☑','Tarefas','Prioridades, prazos e andamento'],
 ['calculos','∑','Calculadoras','Resultados calculados, sem suposições da IA'],
 ['diagnostico','◈','Diagnóstico','Informações reais desta máquina'],
 ['emergencia','✚','Emergência','Seus contatos, planos e suprimentos offline'],
 ['backups','⟳','Backups','Proteja e recupere seus dados'],
 ['memoria','◇','Memórias','Informações declaradas e sua origem'],
 ['rotinas','⚙','Rotinas','Execução supervisionada'],
 ['historico','≡','Histórico','Auditoria de operações reais'],
 ['avancado','⌘','Avançado','Execução técnica para desenvolvedores']
];
let active='inicio', roots=[], catalog=[], busy=false, currentPath='', editing={}, backupName='', latestResult=null;
let v9Agent='morgana', v9Build=null, v9Imported=null;
const $=sel=>document.querySelector(sel);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const bytes=n=>Number.isFinite(Number(n))?new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1}).format(Number(n)/1024/1024)+' MB':'—';
const date=v=>v?new Date(v).toLocaleString('pt-BR'):'—';
const fmt=v=>typeof v==='number'?new Intl.NumberFormat('pt-BR',{maximumFractionDigits:5}).format(v):String(v??'—');
const btn=(label,action,value,cls='secondary small-btn')=>`<button type="button" class="${cls}" data-action="${esc(action)}" data-value="${esc(value)}">${esc(label)}</button>`;
const box=(title,content,extra='')=>`<section class="card ${extra}"><h2>${title}</h2>${content}</section>`;
const field=(name,label,type='text',value='',extra='')=>`<div class="field"><label for="f-${esc(name)}">${esc(label)}</label>${type==='textarea'?`<textarea id="f-${esc(name)}" name="${esc(name)}" ${extra}>${esc(value)}</textarea>`:`<input id="f-${esc(name)}" name="${esc(name)}" type="${esc(type)}" value="${esc(value)}" ${extra}>`}</div>`;
const select=(name,label,opts,value)=>`<div class="field"><label for="f-${name}">${label}</label><select id="f-${name}" name="${name}">${opts.map(([v,t])=>`<option value="${esc(v)}" ${v===value?'selected':''}>${esc(t)}</option>`).join('')}</select></div>`;
const entry=(name,meta,actions='',preview='')=>`<div class="entry"><div><strong>${esc(name)}</strong><div class="meta">${esc(meta)}</div>${preview?`<div class="preview">${esc(preview)}</div>`:''}</div><div class="actions">${actions}</div></div>`;
const empty=text=>`<div class="empty">${esc(text)}</div>`;
const form=(tool,fields,label='Salvar',warn=false)=>`<form data-tool="${esc(tool)}" class="tool-form">${fields}<div class="row"><button class="primary" type="submit">${esc(label)}</button>${warn?'<span class="hint-block">Será solicitada confirmação antes de alterar dados.</span>':''}</div></form>`;
const result=view=>`<pre class="result">${esc(JSON.stringify(view,null,2))}</pre>`;
function message(text,type='info'){const n=$('#notice');n.className=`notice ${type}`;n.textContent=text; n.scrollIntoView({block:'nearest',behavior:'smooth'});}
function clearMessage(){$('#notice').textContent='';$('#notice').className='';}
async function api(url,options={}) {const res=await fetch(url,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});let data;try{data=await res.json()}catch{throw Error(`Servidor retornou HTTP ${res.status} sem JSON válido`)}if(!res.ok)throw Error(typeof data.detail==='string'?data.detail:`Falha HTTP ${res.status}`);return data;}
async function invoke(tool,arguments_={},ask=true) {
 const spec=catalog.find(i=>i.id===tool);
 if(spec?.requires_confirmation){
  if(ask&&!confirm(`Confirmar operação local: ${spec.description}?\n\nFerramenta: ${tool}\nAs alterações podem afetar os dados persistidos.`))return null;
  arguments_.confirm=true;
 }
 const data=await api('/api/v1/utilities/invoke',{method:'POST',body:JSON.stringify({tool,arguments:arguments_})});latestResult=data;
 if(data.status!=='success')throw Error(data.result?.error||'Operação não concluída');
 return data.result;
}
async function read(tool,args={}){const data=await api('/api/v1/utilities/invoke',{method:'POST',body:JSON.stringify({tool,arguments:args})});if(data.status!=='success')throw Error(data.result?.error||tool);return data.result;}
function nav(){ $('#modules').innerHTML=modules.map(([id,icon,name])=>`<button class="nav-item ${active===id?'active':''}" data-nav="${id}" type="button" ${active===id?'aria-current="page"':''}><span class="symbol">${icon}</span><span>${name}</span></button>`).join('');const m=modules.find(x=>x[0]===active);$('#page-title').textContent=m[2];$('#page-subtitle').textContent=m[3];}
async function go(id){if(!modules.some(m=>m[0]===id))return;active=id;clearMessage();nav();$('#view').innerHTML=empty('Carregando dados locais…');history.replaceState(null,'',`#${id}`);try{await views[id]()}catch(e){$('#view').innerHTML=box('Não foi possível carregar',empty(e.message));message(e.message,'error')}}
const tile=(id,desc)=>{const m=modules.find(x=>x[0]===id);return `<button class="card tile" type="button" data-nav="${id}"><span class="symbol">${m[1]}</span><h2>${m[2]}</h2><p>${desc}</p><span class="badge">Abrir módulo</span></button>`};
const views={};
views.inicio=async()=>{const [notes,tasks,docs,diag]=await Promise.allSettled([read('notes.list'),read('tasks.list'),read('library.list'),read('diagnostics.system')]);const count=(x,key)=>x.status==='fulfilled'?(x.value[key]??x.value.items?.length??'—'):'Indisponível';$('#view').innerHTML=`<div class="hero"><div class="eyebrow">SEU ESPAÇO PESSOAL</div><h2>As coisas importantes, em um só lugar.</h2><p>Organize sua rotina, consulte seus documentos e cuide dos seus arquivos — mesmo sem um modelo de IA em execução.</p><div class="row">${btn('Abrir minhas notas','jump','notas','primary')}${btn('Explorar arquivos','jump','arquivos')}</div></div><div class="grid stat-grid">${[['Notas',count(notes,'count')],['Tarefas',count(tasks,'count')],['Documentos',count(docs,'count')],['CPU lógica',diag.status==='fulfilled'?diag.value.cpu_logical:'—']].map(([name,n])=>`<div class="card"><div class="metric">${esc(n)}</div><div class="metric-label">${esc(name)}</div></div>`).join('')}</div><div class="section-head"><h2>Explorar ferramentas</h2><span class="pill">Sem dependência da IA</span></div><div class="grid">${['pesquisa','arquivos','biblioteca','documentos','analises','cerebros','forja','notas','tarefas','diagnostico','emergencia','backups','calculos','memoria'].map(id=>tile(id,modules.find(x=>x[0]===id)[3])).join('')}</div>`};
views.arquivos=async()=>{if(!currentPath)currentPath=roots[0]||'';const data=await read('files.list',{path:currentPath});const parent=currentPath.replace(/[\\/][^\\/]+[\\/]?$/,'');const canUp=parent && roots.some(r=>parent===r||parent.startsWith(r+'/')||parent.startsWith(r+'\\'));$('#view').innerHTML=`<div class="grid"><div class="card full"><div class="section-head"><h2>Explorador de arquivos</h2><span class="badge">Pasta autorizada</span></div><div class="row breadcrumbs">${canUp?btn('↑ Voltar','folder',parent):''}<span class="path-label">${esc(currentPath)}</span>${btn('↻ Atualizar','refresh','')}</div><div class="row" style="margin-top:16px">${form('files.search',field('query','Pesquisar nomes de arquivos','search','','placeholder="Nome ou parte dele" required')+`<input type="hidden" name="path" value="${esc(currentPath)}">`,'Pesquisar')}<form id="upload-form"><label class="upload-label">Adicionar arquivo <input type="file" id="upload" accept=".txt,.md,.pdf,.docx,.xlsx,.csv,.json,.log" required></label><button class="secondary" type="submit">Enviar para pasta autorizada</button></form></div><div class="items" style="margin-top:16px">${data.items.length?data.items.sort((a,b)=>Number(b.directory)-Number(a.directory)||a.name.localeCompare(b.name)).map(x=>entry((x.directory?'📁 ':'📄 ')+x.name,(x.directory?'Pasta':bytes(x.bytes))+' · '+date(x.modified),x.directory?btn('Abrir','folder',x.path):`${btn('Ler','file-read',x.path)}${btn('Copiar','file-copy',x.path)}${btn('Mover','file-move',x.path)}${btn('Lixeira','file-delete',x.path,'danger small-btn')}`)).join(''):empty('Pasta vazia. Você pode adicionar arquivos acima.')}</div></div><div class="card"> <h2>Nova pasta</h2>${form('files.mkdir',field('name','Nome da pasta','text','','required maxlength="100"'),'Criar pasta',true)}</div><div class="card"><h2>Proteção de arquivos</h2><p>O explorador mostra somente o espaço autorizado. Exclusões são enviadas à lixeira interna, não apagadas definitivamente. Copiar e mover exigem confirmação.</p><p class="hint-block">Arquivos do seu computador fora dessa pasta não ficam acessíveis automaticamente.</p></div></div><div id="detail" class="detail-slot"></div>`};
views.biblioteca=async()=>{
 const data=await read('library.list');
 const hits=data.documents.map(d=>entry(d.name,
  d.category+' · '+date(d.created)+' · '+(d.state||'available'),
  btn('Detalhes','lib-details',d.id)+btn('Markdown','lib-markdown',d.id)+btn('Excluir','lib-delete',d.id,'danger small-btn'),
  'Indexação: '+(d.method||'legacy'))).join('');
 $('#view').innerHTML=`<div class="split"><div class="stack">
 ${box('Buscar com evidências',form('library.retrieve',field('query','Consulta contextual','search','','placeholder="Ex.: Ocultista 20% NEX" required maxlength="500"'),'Recuperar trechos'))}
 ${box('Busca literal',form('library.search',field('query','Palavras no documento ou no nome','search','','required'),'Pesquisar texto'))}
 ${box('Importar documento',`<p>O original é copiado para a biblioteca local. TXT, Markdown, PDF, DOCX, CSV, XLSX e JSON; arquivos complexos podem ficar parcialmente processados.</p><form id="library-upload"><div class="field"><label for="lib-file">Selecionar documento</label><input type="file" id="lib-file" accept=".txt,.md,.pdf,.docx,.csv,.xlsx,.json" required></div>${field('category','Categoria','text','geral','maxlength="100"')}<button type="submit" class="primary">Adicionar à biblioteca</button></form><p class="hint-block">OCR somente se Tesseract e pdftoppm estiverem instalados no computador.</p>`)}
 </div>${box('Biblioteca · '+data.documents.length+' documentos',hits||empty('Nenhum documento importado.'))}</div><div id="detail" class="detail-slot"></div>`;
};
views.documentos=async()=>{
 const data=await read('library.list');
 $('#view').innerHTML=box('Documentos originais e processamento',
  data.documents.length?data.documents.map(d=>entry(d.name,
   (d.state||'available')+' · '+(d.method||'legado')+' · '+bytes(d.bytes),
   btn('Inspecionar','lib-details',d.id)+btn('Markdown','lib-markdown',d.id)+
   `<a class="secondary small-btn" href="/api/v1/utilities/documents/${encodeURIComponent(d.id)}/original" target="_blank" rel="noopener noreferrer">Abrir original</a>`)).join('')
   :empty('Nenhum documento disponível.'))+'<div id="detail" class="detail-slot"></div>';
};
views.analises=async()=>{
 const data=await read('library.list');
 const sheets=data.documents.filter(d=>/\.(csv|xlsx|json)$/i.test(d.name));
 const choice=sheets.map(d=>[d.id,d.name]);
 $('#view').innerHTML=`<div class="split"><div class="stack">
 ${box('Inspecionar tabela',sheets.length?form('data.inspect',select('document_id','Arquivo importado',choice,choice[0]?.[0]),'Ver colunas e ausências'):empty('Importe CSV, XLSX ou JSON na biblioteca.'))}
 ${box('Análise verificável',sheets.length?form('data.analyze',
 select('document_id','Planilha',choice,choice[0]?.[0])+select('operation','Operação',[
 ['describe','Estatísticas descritivas'],['missing','Valores ausentes'],
 ['group','Agrupar e somar'],['trend','Tendência por período'],['growth','Crescimento por produto'],['filter','Filtrar']],'describe')+
 field('column','Coluna numérica ou filtro','text','')+
 field('group_by','Coluna de agrupamento','text','')+
 field('period_column','Coluna de período','text','')+
 select('aggregation','Agregação',[['sum','Soma'],['mean','Média'],['count','Contagem'],['min','Mínimo'],['max','Máximo']],'sum')+
 select('operator','Comparação para filtro',[['eq','Igual'],['ne','Diferente'],['gt','Maior'],['gte','Maior ou igual'],['lt','Menor'],['lte','Menor ou igual']],'eq')+
 field('value','Valor para filtro','text',''),'Executar cálculo'):empty('Importe uma planilha primeiro.'))}
 </div>${box('Confiabilidade',`<p>A análise usa exclusivamente os dados do original importado e operações predefinidas de pandas. Não executa fórmulas das planilhas nem código gerado pelo modelo.</p><p>Escolha as colunas a partir da inspeção e confira tabelas e resultados. Os resultados não são memórias pessoais.</p>`)}
 </div><div id="detail" class="detail-slot"></div>`;
};

const editor=(kind)=>{const item=editing[kind]||{};const isTask=kind==='tasks';return form(`${kind}.save`,`${item.id?`<input name="id" type="hidden" value="${esc(item.id)}">`:''}${field('title',isTask?'Nome da tarefa':'Título','text',item.title||'','required maxlength="200"')}${isTask?select('status','Estado',[['todo','A fazer'],['doing','Em andamento'],['done','Concluída'],['cancelled','Cancelada']],item.status||'todo')+select('priority','Prioridade',[['baixa','Baixa'],['normal','Normal'],['alta','Alta'],['urgente','Urgente']],item.priority||'normal')+field('due','Prazo','date',item.due||''):field('content','Conteúdo','textarea',item.content||'','rows="8"')}${field('tags','Etiquetas (separadas por vírgula)','text',item.tags||'')}`,item.id?'Salvar alterações':(isTask?'Criar tarefa':'Salvar nota'),true)};
async function records(kind){const data=await read(`${kind}.list`);const isTask=kind==='tasks';$('#view').innerHTML=`<div class="split"><div class="card"><div class="section-head"><h2>${editing[kind]?.id?'Editar':'Criar'} ${isTask?'tarefa':'nota'}</h2>${editing[kind]?.id?btn('Nova','new-record',kind):''}</div>${editor(kind)}</div><div class="card"><div class="section-head"><h2>${isTask?'Minhas tarefas':'Minhas notas'}</h2><span class="badge">${data.items.length} registros</span></div><input class="searchbox" id="local-filter" type="search" placeholder="Filtrar registros..." aria-label="Filtrar registros"><div class="items" id="records-list" style="margin-top:15px">${data.items.length?data.items.map(item=>entry(item.title||'Sem título',(isTask?`${item.status||'todo'} · ${item.priority||'normal'} · `:'')+date(item.updated),btn('Editar','edit-'+kind,item.id)+btn('Excluir','delete-'+kind,item.id,'danger small-btn'),isTask?item.due?`Prazo: ${item.due}`:'':item.content||'')).join(''):empty('Nenhum registro. Crie o primeiro à esquerda.')}</div></div></div>`};
views.notas=()=>records('notes');views.tarefas=()=>records('tasks');
const calculators=[['calc.evaluate','Expressão matemática',[['expression','Expressão','text','(2+3)*4']]],['calc.percent','Porcentagem',[['value','Valor','number','100'],['percent','Percentual (%)','number','15']]],['calc.convert','Converter unidades',[['value','Valor','number','1'],['from','De (ex.: km)','text','km'],['to','Para (ex.: m)','text','m']]],['calc.dates','Intervalo entre datas',[['start','Início','date','2026-01-01'],['end','Fim','date','2026-12-31']]],['calc.electricity','Consumo elétrico',[['watts','Potência (W)','number','100'],['hours_per_day','Horas/dia','number','8'],['days','Dias','number','30']]],['calc.battery','Autonomia da bateria',[['capacity_wh','Capacidade (Wh)','number','500'],['load_watts','Carga (W)','number','100'],['efficiency','Eficiência (0–1)','number','0.85']]],['calc.supplies','Planejar suprimentos',[['people','Pessoas','number','2'],['days','Dias','number','7'],['per_person_per_day','Unidades por pessoa/dia','number','2'],['unit','Unidade','text','litros']]],['calc.storage','Armazenamento digital',[['files','Quantidade de arquivos','number','100'],['size_mb_each','MB por arquivo','number','10']]]];
views.calculos=async()=>{$('#view').innerHTML=`<div class="grid">${calculators.map(([tool,title,fields])=>box(title,form(tool,fields.map(([name,label,type,value])=>field(name,label,type,value,`required ${type==='number'?'step="any"':''}`)).join(''),'Calcular'))).join('')}</div><div id="detail" class="detail-slot"></div>`};
views.diagnostico=async()=>{const [d,c]=await Promise.all([read('diagnostics.system'),read('diagnostics.connection')]);const metrics=[['Processadores lógicos',d.cpu_logical],['Uso de CPU',d.cpu_percent_sample==null?'Indisponível':`${fmt(d.cpu_percent_sample)}%`],['Uso de RAM',d.ram_percent==null?'Indisponível':`${fmt(d.ram_percent)}%`],['RAM utilizada',d.ram_used==null?'Indisponível':bytes(d.ram_used)],['Disco livre',bytes(d.disk.free)],['Disco ocupado',bytes(d.disk.used)]];$('#view').innerHTML=`<div class="section-head"><h2>Este computador</h2>${btn('Atualizar medições','refresh','')}</div><div class="grid stat-grid">${metrics.map(([k,v])=>`<div class="card"><div class="metric">${esc(v)}</div><div class="metric-label">${esc(k)}</div></div>`).join('')}</div><div class="grid" style="margin-top:16px">${box('Sistema',`<p>${esc(d.platform)}</p><p>Python: ${esc(d.python)}</p><p>GPU: ${esc(d.gpu)}</p><p class="hint-block">Métricas indisponíveis são identificadas, não simuladas.</p>`,'wide')}${box('Serviço local de modelo',`<div class="metric">${c.reachable?'Acessível':'Indisponível'}</div><p>127.0.0.1:${esc(c.port)}</p><p class="hint-block">A checagem verifica conexão com uma porta local, não acesso à internet.</p>`)}</div>`};
const emTypes=[['contact','Contato'],['plan','Plano'],['checklist','Checklist'],['supply','Suprimento'],['incident','Ocorrência']];
views.emergencia=async()=>{const d=await read('emergency.list');$('#view').innerHTML=`<div class="hero emergency"><div class="eyebrow">CENTRAL OFFLINE</div><h2>Informações importantes, ao seu alcance.</h2><p>Registros cadastrados por você. Este painel não faz ligações, não rastreia localização e não substitui serviços de emergência.</p></div><div class="split">${box('Adicionar informação',form('emergency.save',field('title','Título','text','','required')+select('category','Tipo',emTypes,'contact')+field('content','Informações, telefone ou instruções de fonte identificável','textarea','','rows="5"')+field('source','Origem da informação','text','Informado pelo usuário'),'Salvar informação',true))}${box(`Registros (${d.items.length})`,d.items.length?`<div class="items">${d.items.map(x=>entry(x.title,x.category||'registro',btn('Remover','delete-emergency',x.id,'danger small-btn'),x.content||'')).join('')}</div>`:empty('Adicione seus contatos, planos ou checklists de emergência.'))}</div>`};
views.backups=async()=>{const b=await read('backup.list');$('#view').innerHTML=`<div class="grid"><div class="card"><h2>Criar uma cópia de segurança</h2><p>Inclui notas, tarefas, biblioteca e outros dados das utilidades. Não inclui automaticamente o banco legado de conversas e memórias.</p>${btn('Criar backup agora','create-backup','','primary')}</div><div class="card wide"><h2>Backups disponíveis</h2>${b.items.length?`<div class="items">${b.items.map(x=>entry(x.filename,bytes(x.bytes)+' · '+date(x.modified),btn('Verificar','verify-backup',x.filename)+btn('Restaurar','restore-backup',x.filename,'danger small-btn'))).join('')}</div>`:empty('Nenhum backup criado nesta instalação.')}</div></div><div id="detail" class="detail-slot"></div>`};
views.memoria=async()=>{const d=await read('memory.list');$('#view').innerHTML=`<div class="split">${box('Registrar informação',form('memory.save',field('value','Informação declarada','textarea','','required')+field('source','Origem (ex.: declarado por mim)','text','','required')+field('title','Título curto','text','Informação pessoal'),'Registrar memória',true)+`<p class="hint-block">Uma informação declarada não é automaticamente um fato comprovado.</p>`)}${box('Memórias declaradas',d.items.length?`<div class="items">${d.items.map(x=>entry(x.value,x.source+' · '+date(x.updated),btn('Excluir','delete-memory',x.id,'danger small-btn'))).join('')}</div>`:empty('Nenhuma memória nesta camada adicional.'))}</div>`};
views.rotinas=async()=>{const d=await read('routines.list');$('#view').innerHTML=`<div class="split">${box('Criar rotina supervisionada',form('routines.save',field('title','Nome da rotina','text','','required')+select('template','Modelo autorizado',[['note','Criar nota'],['diag','Consultar diagnóstico'],['search','Buscar na biblioteca']],'note')+field('text','Texto da nota ou termo de pesquisa','text',''),'Salvar rotina',true)+`<p class="hint-block">As rotinas usam apenas uma lista limitada de ações autorizadas. Execução manual, sem comandos de terminal.</p>`)}${box('Rotinas salvas',d.items.length?`<div class="items">${d.items.map(x=>entry(x.title,'Execução manual',btn('Executar','run-routine',x.id,'primary small-btn'))).join('')}</div>`:empty('Nenhuma rotina cadastrada.'))}</div><div id="detail" class="detail-slot"></div>`};
views.historico=async()=>{const d=await read('operations.history');$('#view').innerHTML=box('Operações recentes',d.items.length?`<div class="items">${d.items.slice(0,100).map(x=>entry(x.action,`${date(x.created)} · ${x.status}`,btn('Detalhes','op-detail',x.id))).join('')}</div>`:empty('Não existem operações registradas.'))+`<div id="detail" class="detail-slot"></div>`;window._ops=d.items};

let webSearchState=null,webPageState=null;
function webCards(data){
 return `<div class="stack">${(data?.results||[]).map((r,i)=>`<article class="web-hit"><div class="web-number">${String(i+1).padStart(2,'0')}</div><div class="web-hit-content"><h3>${esc(r.title||'Resultado sem título')}</h3><div class="web-url">${esc(r.url)}</div>${r.snippet?`<p>${esc(r.snippet)}</p>`:''}<div class="row"><button class="secondary small-btn" type="button" data-action="web-read" data-value="${esc(r.url)}">Ler página e conferir</button><a class="secondary small-btn" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">Abrir no navegador ↗</a></div></div></article>`).join('')}</div>`;
}
views.pesquisa=async()=>{
 const state=webSearchState;
 $('#view').innerHTML=`<div class="web-hero"><div class="eyebrow">CONHECIMENTO CONECTADO</div><h2>Explore a internet.<br><span>Guarde o que importa.</span></h2><p>Pesquisas iniciadas por você. Fontes abertas e registradas, com opção de salvar conteúdo na sua biblioteca offline.</p><div class="web-online">◉ &nbsp; Requer conexão com a internet para novas pesquisas</div></div>
 <div class="web-searchbox card"><form id="web-form" class="web-query-form"><label for="web-query">O que você quer descobrir?</label><div class="web-search-row"><input id="web-query" name="query" required maxlength="300" placeholder="Ex.: modelos locais de IA com 16 GB de VRAM" value="${esc(state?.query||'')}"><button type="submit" class="primary">⌕ Pesquisar</button></div><div class="row web-options"><label for="web-limit">Resultados</label><select id="web-limit" name="limit"><option value="5">5 fontes</option><option value="8">8 fontes</option></select><label for="web-depth">Modo</label><select name="mode" id="web-depth"><option value="web.search">Rápido</option><option value="web.research">Aprofundado (ler até 3 páginas)</option></select><span>Uma pesquisa real; resultados podem variar conforme o buscador disponível.</span></div></form></div>
 <div id="web-results">${state?`<div class="section-head"><h2>${state.count} resultados encontrados</h2><span class="badge">${esc(state.provider)}</span></div>${state.count?webCards(state):empty('Nenhuma fonte encontrada. Refine os termos e pesquise novamente.')}${state.sources?.length?box('Leitura aprofundada · fontes consultadas',`<div class="stack">${state.sources.map(x=>x.status==='read'?entry(x.title,`Origem: ${x.url} · ${date(x.read_at)}`,btn('Ver página','web-read',x.url),x.excerpt):entry('Não foi possível ler a fonte',x.url,'',x.reason)).join('')}</div>`):''}<p class="muted">${esc(state.note||'')}</p>`:box('Como funciona',`<div class="web-steps"><div><strong>01 · Pesquise</strong><p>Consulte um mecanismo de busca real.</p></div><div><strong>02 · Confira</strong><p>Abra páginas e leia o texto extraído.</p></div><div><strong>03 · Salve</strong><p>Adicione somente o conteúdo escolhido à biblioteca offline.</p></div></div>`)}</div><div id="web-page" class="detail-slot"></div>`;
 if(webPageState)renderWebPage(webPageState);
};
function renderWebPage(page){
 webPageState=page;
 const el=$('#web-page');if(!el)return;
 el.innerHTML=`<section class="card web-reading"><div class="section-head"><div><div class="eyebrow">PÁGINA CONSULTADA E REGISTRADA</div><h2>${esc(page.title)}</h2></div><span class="badge">Leitura real</span></div><div class="web-url">${esc(page.url)}</div><div class="meta">Consultada em ${esc(date(page.read_at))}${page.truncated?' · conteúdo truncado pelo limite de segurança':''}</div><div class="row web-save-row"><button type="button" class="primary" data-action="web-save" data-value="${esc(page.source_id)}">＋ Salvar na biblioteca offline</button><a href="${esc(page.url)}" class="secondary" target="_blank" rel="noopener noreferrer">Ver original ↗</a></div><div class="web-excerpt">${esc(page.content)}</div><p class="muted">Texto extraído do site; não é verificação independente da veracidade do conteúdo. A origem foi registrada.</p></section>`;
 el.scrollIntoView({behavior:'smooth',block:'start'});
}
// V9: functional local-only brain and build controls, using actual backend state.
function p0EnvironmentPanel(audit){
 const checks=audit.checks.map(x=>entry(x.id,`${x.status.toUpperCase()} · ${x.message}`)).join('');
 return box('P0 · Diagnóstico das três pastas (somente leitura)',
 `<p><strong>Estado observado: ${esc(audit.status)}</strong>. Nenhum arquivo é copiado ou modificado nesta verificação.</p>
 <p class="hint-block">${esc(audit.note)}</p>
 <div class="meta">IA: ${esc(audit.folders.ia)}<br>Venv externa: ${esc(audit.folders.venv)}<br>Database: ${esc(audit.folders.database)}<br>Dados ativos: ${esc(audit.folders.data)}<br>SQLite esperado: ${esc(audit.folders.sqlite)}<br>Ambiente: ${esc(audit.memory_environment)}</div>
 <div class="items">${checks}</div><p>${btn('Verificar novamente','refresh','')}</p>`,'wide');
}
views.cerebros=async()=>{
 const [audit,data]=await Promise.all([api('/api/v1/brains/environment'),api('/api/v1/brains/catalog')]);
 const preflight=p0EnvironmentPanel(audit);
 if(!data.enabled){$('#view').innerHTML=preflight+box('V9 desativada', '<p>Habilite CAMPANARIO_BRAINS_V9_ENABLED=true e reinicie. O chat V9.1 existente permanece intacto.</p>');return;}
 const logs=await api('/api/v1/brains/runs?limit=20');
 $('#view').innerHTML=preflight+`<div class="grid">${data.brains.map(b=>box(esc(b.display_name),`<p><strong>${esc(b.status)}</strong> · ${esc(b.health)}</p><div class="meta">${esc(b.brain_id)} · ${esc((b.capabilities||[]).join(', ')||'sem executor')} · ${esc(b.version||'não instalado')}</div>`)).join('')}</div>
 <div class="grid v9-panels" style="margin-top:16px">
 ${box('Teste real de capacidade',`<form id="v9-test-form" class="tool-form">${select('brain_id','Cérebro',[['knowledge','Conhecimento — consulta à biblioteca'],['analysis','Análise — cálculo na planilha']],'knowledge')}${field('query','Pergunta','textarea','','required maxlength="1200" rows="3"')}${field('document_hint','Documento (opcional)','text','','maxlength="85"')}<button class="primary" type="submit">Executar consulta</button></form><p class="hint-block">Este teste realiza leitura real, sem calcular no LLM. Resultados sem fonte são marcados como indisponíveis.</p>`,'wide')}
 ${box('Últimas execuções',logs.items.length?logs.items.map(r=>entry(r.brain_id,`${r.status} · ${r.latency_ms} ms · ${r.evidence_count} evidências · ${date(r.created_at)}`,'',`Operações: ${r.operations.join(', ')}`)).join(''):empty('Nenhuma execução registrada.'),'wide')}
 </div><div id="detail" class="detail-slot"></div>`;
};
views.forja=async()=>{
 const data=await api('/api/v1/brains/catalog');
 if(!data.enabled){$('#view').innerHTML=box('V9 desativada','<p>Ative CAMPANARIO_BRAINS_V9_ENABLED=true para configurar fichas heroicas.</p>');return;}
 if(!data.agents.some(a=>a.id===v9Agent))v9Agent='morgana';
 v9Build=await api(`/api/v1/brains/builds/${encodeURIComponent(v9Agent)}`);
 const archetypes=[['','Livre / sem arquétipo'],...Object.entries(data.archetypes).map(([id,name])=>[id,`${id} · ${name}`])];
 const b=v9Build;
 $('#view').innerHTML=`<div class="grid v9-panels">
 ${box('Agente e ficha',`<div class="row">${data.agents.map(a=>btn(a.name,'v9-agent',a.id,a.id===v9Agent?'primary small-btn':'secondary small-btn')).join('')}</div><div class="meta">Ficha revisão ${b.revision} · ${esc(b.agent_id)} · Personalidade original preservada</div>
 <form id="v9-build-form" class="tool-form">${select('primary','Arquétipo principal',archetypes,b.primary_archetype||'')}${select('secondary','Arquétipo secundário',[['','Nenhum'],...archetypes.slice(1)],b.secondary_archetype||'')}
 <div class="field"><label>Talentos equipados (máximo 2 ativos por turno)</label><div class="v9-talent-list">${data.talents.map(t=>`<label><input type="checkbox" name="talent" value="${esc(t.id)}" ${b.talents.includes(t.id)?'checked':''}><span>${esc(t.title)} <small>· ${esc(t.trigger)} · ${esc(t.effect)}</small></span></label>`).join('')}</div></div>
 <button class="primary" type="submit">Salvar ficha sem alterar memórias</button><a class="secondary" href="/api/v1/brains/builds/${encodeURIComponent(v9Agent)}/export" download="${esc(v9Agent)}.campagent">Exportar .campagent</a></form>`,'wide')}
 ${box('Novo agente local',`<form id="v9-create-form" class="tool-form">${field('agent_id','Identificador único','text','','required pattern="[a-z0-9_-]+" maxlength="64"')}${field('display_name','Nome de exibição','text','','required maxlength="64"')}${field('identity_description','Descrição da nova identidade','textarea','','maxlength="400" rows="3"')}<button class="primary" type="submit">Criar agente com modelo compartilhado</button></form><p class="hint-block">Não copia Morgana, Todd, memórias nem permissões.</p>`)}
 ${box('Importar .campagent',`<form id="v9-import-form" class="tool-form"><input type="file" name="package" accept=".campagent" required><button class="secondary" type="submit">Inspecionar pacote sem aplicar</button></form><p class="hint-block">A importação verifica o manifesto e rejeita scripts, executáveis e caminhos perigosos.</p>`)}
 </div><div id="detail" class="detail-slot"></div>`;
};
views.avancado=async()=>{const allowed=catalog.map(x=>[x.id,x.id+' · '+x.description]);$('#view').innerHTML=`<div class="split">${box('Executor técnico',`<p>Para testes e manutenção. O uso normal do Campanario não exige JSON.</p>${form('advanced',select('tool','Ferramenta',allowed,allowed[0]?.[0])+field('json','Parâmetros JSON','textarea','{}','rows="9"'),'Executar ferramenta')}`)}${box('Registro de capacidades',`<p>${catalog.length} ferramentas registradas. Cada ação é executada no backend e retorna um resultado estruturado.</p><p>Este painel não realiza ações inventadas pela IA.</p>`)}</div><div id="detail" class="detail-slot"></div>`};
function showDetail(content){let el=$('#detail');if(!el){el=document.createElement('div');el.id='detail';el.className='detail-slot';$('#view').appendChild(el)}el.innerHTML=box('Resultado da operação',content);el.scrollIntoView({behavior:'smooth',block:'nearest'})}
function renderEvidence(res){
 if(!res.evidence?.length)return empty('Nenhum trecho relevante encontrado. O sistema não confirmou a informação.');
 return res.evidence.map(e=>entry(e.document,
  (e.page?'Página '+e.page:'Sem página')+(e.section?' · '+e.section:'')+' · '+e.method,
  btn('Ver documento','lib-details',e.document_id),
  `Evidência ${e.evidence_id}\n${e.excerpt}`)).join('');
}
function renderAnalysis(res){
 if(!Array.isArray(res.result))return `<pre class="result">${esc(JSON.stringify(res,null,2))}</pre>`;
 const keys=Array.from(new Set(res.result.flatMap(row=>Object.keys(row)))).slice(0,15);
 const table=`<div style="overflow:auto"><table class="result-table"><thead><tr>${keys.map(k=>`<th>${esc(k)}</th>`).join('')}</tr></thead><tbody>${res.result.map(row=>`<tr>${keys.map(k=>`<td>${esc(row[k]??'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
 const numericKey=keys.find(k=>res.result.some(row=>typeof row[k]==='number')&&!['change_percent','change_absolute'].includes(k));
 const labelKey=keys.find(k=>k!==numericKey);
 const points=res.result.slice(0,18);
 const max=Math.max(0,...points.map(row=>Number(row[numericKey])||0));
 const chart=(res.operation==='group'||res.operation==='trend')&&numericKey&&labelKey&&max>0?
  `<div class="v8-bars">${points.map(row=>`<div class="v8-bar"><span>${esc(row[labelKey])}</span><div><i style="width:${Math.max(0,Math.min(100,100*Number(row[numericKey])/max))}%"></i></div><b>${esc(fmt(row[numericKey]))}</b></div>`).join('')}</div>`:'';
 return `<div class="meta">Arquivo: ${esc(res.source?.filename||'—')} · ${esc(res.status||'computed')} · ${esc(res.operation)}</div>${table}${chart}`;
}
async function uploadFile(file){
 if(!file)throw Error('Selecione um arquivo');
 if(file.size>200_000_000)throw Error('Limite de envio: 200 MB. Copie PDFs maiores diretamente para a pasta autorizada e importe pela biblioteca (até 500 MB).');
 const res=await fetch('/api/v1/utilities/upload-stream?filename='+encodeURIComponent(file.name),{
  method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file
 });
 const data=await res.json();
 if(!res.ok)throw Error(data.detail||`HTTP ${res.status}`);
 return data;
}
function values(formEl){const obj={};for(const [k,v] of new FormData(formEl)){if(k==='confirm')continue;obj[k]=v}for(const input of formEl.querySelectorAll('input[type="number"]')){if(input.name)obj[input.name]=Number(input.value)}return obj;}
async function onSubmit(ev){const formEl=ev.target;if(!(formEl instanceof HTMLFormElement))return;ev.preventDefault();if(busy)return;busy=true;const submit=formEl.querySelector('[type="submit"]');if(submit)submit.disabled=true;try{
 if(formEl.id==='v9-test-form'){
  const args=values(formEl);args.agent_id=v9Agent;
  const r=await api('/api/v1/brains/preview',{method:'POST',body:JSON.stringify(args)});
  showDetail(result(r));message(r.evidence.length?'Consulta concluída com evidências.':'Nenhuma evidência recuperada.','info');return;
 }
 if(formEl.id==='v9-build-form'){
  if(!v9Build)throw Error('Ficha não carregada');
  const fd=new FormData(formEl);const primary=String(fd.get('primary')||'');const secondary=String(fd.get('secondary')||'');
  const build={...v9Build,mode:primary?'archetype':'free',primary_archetype:primary||null,
   secondary_archetype:primary?(secondary||null):null,talents:fd.getAll('talent')};
  const saved=await api(`/api/v1/brains/builds/${encodeURIComponent(v9Agent)}`,
   {method:'PUT',body:JSON.stringify({build,expected_revision:v9Build.revision})});
  v9Build=saved;await views.forja();message('Ficha salva. Memórias, conversas e personalidade mantidas.','success');return;
 }
 if(formEl.id==='v9-create-form'){
  if(!confirm('Criar novo agente local, sem copiar memórias nem permissões de Morgana ou Todd?'))return;
  const x=values(formEl);const build={agent_id:String(x.agent_id).trim(),display_name:x.display_name,
   identity_description:x.identity_description,mode:'free'};
  const created=await api('/api/v1/brains/agents',{method:'POST',body:JSON.stringify(build)});
  v9Agent=created.agent_id;await views.forja();message('Agente criado usando o modelo compartilhado.','success');return;
 }
 if(formEl.id==='v9-import-form'){
  const blob=formEl.querySelector('input[type="file"]').files[0];if(!blob)throw Error('Selecione o arquivo');
  if(blob.size>4_000_000)throw Error('Máximo 4 MB');
  const response=await fetch('/api/v1/brains/package/inspect',{
   method:'POST',headers:{'Content-Type':'application/octet-stream'},body:blob});
  const parsed=await response.json();if(!response.ok)throw Error(parsed.detail||'Pacote inválido');
  v9Imported=parsed.build;showDetail(`${result(parsed)}<div class="row">${btn('Aplicar ficha após confirmação','v9-import-apply',v9Imported.agent_id,'primary')}</div>`);
  message('Pacote validado. Ainda não foi aplicado.','info');return;
 }
 if(formEl.id==='web-form'){const data=await read(formEl.querySelector('[name="mode"]').value,{query:formEl.querySelector('[name="query"]').value,limit:Number(formEl.querySelector('[name="limit"]').value)});webSearchState=data;webPageState=null;await views.pesquisa();message(`${data.count} resultados de ${data.provider}. Abra páginas para verificar.`,data.count?'success':'info');return}
 if(formEl.id==='upload-form'||formEl.id==='library-upload'){const file=formEl.querySelector('input[type="file"]').files[0];const up=await uploadFile(file);if(formEl.id==='library-upload'){const cat=formEl.querySelector('[name="category"]').value;const res=await invoke('library.import',{path:up.path,category:cat});if(res?.duplicate_id)message('Este documento já está na biblioteca.','info');else if(res?.state==='error')message('Original salvo, mas ocorreu um erro de processamento. Consulte detalhes.','error');else if(res?.state==='partial')message('Original salvo; processamento parcial. Consulte os avisos.','info');else message('Documento importado e indexado.','success')}else message('Arquivo enviado para a pasta autorizada.','success');await views[active]();return}
 const tool=formEl.dataset.tool;if(!tool)return;let args=values(formEl);if(tool==='files.mkdir'){args={path:currentPath.replace(/[\\/]$/,'')+'/'+args.name};}
 if(tool==='routines.save'){let step=args.template==='diag'?{tool:'diagnostics.system',arguments:{}}:args.template==='search'?{tool:'library.search',arguments:{query:args.text||' '}}:{tool:'notes.save',arguments:{title:args.text||args.title}};args={title:args.title,steps:[step]};}
 if(tool==='advanced'){try{args=JSON.parse(args.json)}catch{throw Error('JSON inválido. Confira a sintaxe.')}if(!args||Array.isArray(args)||typeof args!=='object')throw Error('Os parâmetros precisam ser um objeto JSON');const chosen=formEl.querySelector('[name="tool"]').value;const data=await invoke(chosen,args);if(data!==null)showDetail(result(data));return}
 const res=await invoke(tool,args);if(res===null)return;if(tool==='files.search')showDetail(res.items?.length?res.items.map(x=>entry(x,'Arquivo encontrado')).join(''):empty('Nenhum arquivo encontrado.'));else if(tool==='library.search')showDetail(res.documents?.length?res.documents.map(x=>entry(x.name,`Origem: ${x.source}`,'',x.matches?.map(hit=>`${hit.page?'Página '+hit.page+': ':''}${hit.excerpt}`).join('\n\n'))).join(''):empty('Nenhum trecho encontrado.'));else if(tool==='library.retrieve')showDetail(renderEvidence(res));else if(tool==='data.inspect')showDetail(result(res));else if(tool==='data.analyze')showDetail(renderAnalysis(res));else if(tool.startsWith('calc.'))showDetail(result(res));else{if(tool==='notes.save')editing.notes={};if(tool==='tasks.save')editing.tasks={};await views[active]();message('Operação realizada e registrada.','success')}
 }catch(e){message(e.message,'error')}finally{busy=false;if(submit)submit.disabled=false}}
async function onClick(ev){const el=ev.target.closest('[data-nav],[data-action]');if(!el)return;const id=el.dataset.nav;if(id){await go(id);return}const action=el.dataset.action,value=el.dataset.value;try{
 if(action==='v9-agent'){v9Agent=value;return go('forja')}
 if(action==='v9-import-apply'){
  if(!v9Imported||v9Imported.agent_id!==value)throw Error('Inspecione o pacote primeiro');
  if(!confirm(`Aplicar a ficha de ${value}? Não haverá transferência de memórias ou permissões.`))return;
  const list=await api('/api/v1/brains/catalog');
  if(list.agents.some(a=>a.id===value)){
   const old=await api(`/api/v1/brains/builds/${encodeURIComponent(value)}`);
   await api(`/api/v1/brains/builds/${encodeURIComponent(value)}`,{method:'PUT',
    body:JSON.stringify({build:{...v9Imported,revision:old.revision},expected_revision:old.revision})});
  }else{await api('/api/v1/brains/agents',{method:'POST',body:JSON.stringify(v9Imported)})}
  v9Agent=value;v9Imported=null;await go('forja');message('Ficha importada. Permissões não alteradas.','success');return;
 }
 if(action==='web-read'){message('Consultando página externa…','info');const data=await read('web.read',{url:value});renderWebPage(data);message('Página consultada; fonte e data registradas.','success');return}
 if(action==='web-save'){const r=await invoke('web.save',{source_id:value,category:'pesquisa-web'});if(r){message(r.saved?'Fonte salva na biblioteca offline.':'A biblioteca não importou a fonte. Confira o resultado.','success')}return}
 if(action==='jump')return go(value);if(action==='refresh')return go(active);if(action==='folder'){currentPath=value;return go('arquivos')}
 if(action==='new-record'){editing[value]={};return go(value==='notes'?'notas':'tarefas')}
 if(action.startsWith('edit-')){const kind=action.slice(5);const all=await read(kind+'.list');editing[kind]=all.items.find(x=>x.id===value)||{};return go(kind==='notes'?'notas':'tarefas')}
 if(action.startsWith('delete-')){const kind=action.slice(7);const tool=kind==='emergency'?'emergency.delete':kind+'.delete';const res=await invoke(tool,{id:value});if(res){await go(active);message('Registro excluído.','success')}return}
 if(action==='file-read'){const r=await read('files.read',{path:value});showDetail(`<div class="meta">${esc(value)}</div><pre class="result">${esc(r.content)}</pre>`);return}
 if(action==='file-copy'||action==='file-move'){const dest=prompt('Caminho completo do destino (dentro da pasta autorizada):',value);if(!dest)return;const r=await invoke(action==='file-copy'?'files.copy':'files.move',{source:value,destination:dest});if(r){await go('arquivos');message('Operação concluída.','success')}return}
 if(action==='file-delete'){const r=await invoke('files.delete',{path:value});if(r){await go('arquivos');message('Arquivo transferido para a lixeira interna.','success')}return}
 if(action==='lib-details'){
  const res=await read('library.document',{document_id:value});
  showDetail(`<div class="meta">${esc(res.name)} · ${esc(res.state)} · ${esc(res.method)} · ${bytes(res.bytes)}</div><pre class="result">${esc(JSON.stringify({sha256:res.sha256,errors:res.errors,processor:res.version,category:res.category},null,2))}</pre><a class="secondary" href="/api/v1/utilities/documents/${encodeURIComponent(value)}/original" target="_blank" rel="noopener noreferrer">Abrir original</a>`);return;
 }
 if(action==='lib-markdown'){
  const res=await read('library.document',{document_id:value,include_markdown:true});
  showDetail(`<div class="meta">${esc(res.name)} · ${esc(res.state)}</div><pre class="result">${esc(res.markdown||'Sem texto extraído.')}</pre>`);return;
 }
 if(action==='lib-delete'){const r=await invoke('library.delete',{id:value});if(r){await go('biblioteca');message('Documento removido.','success')}return}
 if(action==='create-backup'){const r=await invoke('backup.create');if(r){await go('backups');message(`Backup criado: ${r.path}`,'success')}return}
 if(action==='verify-backup'){const r=await read('backup.verify',{filename:value});showDetail(result(r));message('Integridade do backup verificada.','success');return}
 if(action==='restore-backup'){if(!confirm(`ATENÇÃO: restaurar ${value} substituirá os dados atuais das utilidades. Uma cópia de rollback será criada. Continuar?`))return;const r=await invoke('backup.restore',{filename:value},false);if(r){await go('backups');message(`Dados restaurados. Backup de segurança anterior: ${r.rollback_backup}`,'success')}return}
 if(action==='run-routine'){const r=await invoke('routines.run',{id:value});if(r)showDetail(result(r));return}
 if(action==='op-detail'){const op=window._ops?.find(x=>x.id===value);if(op)showDetail(result(JSON.parse(op.detail)));return}
 }catch(e){message(e.message,'error')}}
async function boot(){try{const [cat,status]=await Promise.all([api('/api/v1/utilities/catalog'),api('/api/v1/utilities/status')]);catalog=cat;roots=status.authorized_roots||[];currentPath=roots[0]||'';$('#workspace-label').textContent='Pasta autorizada: '+(roots[0]||'não configurada');$('#agent-status').textContent=`${catalog.length} operações · IA não necessária`;document.addEventListener('submit',onSubmit);document.addEventListener('click',onClick);$('#reload').addEventListener('click',()=>go(active));await go(modules.some(m=>m[0]===location.hash.slice(1))?location.hash.slice(1):'inicio');}catch(e){message('Não foi possível conectar às ferramentas: '+e.message,'error');$('#view').innerHTML=empty('Confira se o servidor Campanario está em execução e recarregue a página.')}}
boot();
})();
