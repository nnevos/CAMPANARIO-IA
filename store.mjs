/* Portable state: native Android stores this encrypted; preview uses IndexedDB without credentials. */
export const emptyState = () => ({schema:1, notes:[], chats:[], snapshot:{revision:0,items:[],updated:null}, connection:null, repository:''});
export function validateState(value) {
  if (!value || value.schema!==1 || !Array.isArray(value.notes) || !Array.isArray(value.chats) || !Array.isArray(value.snapshot?.items)) throw new Error('Formato de dados local desconhecido. Nada foi apagado.');
  return value;
}
export function newMutation(note, changes, uuid=()=>crypto.randomUUID()) {
  return {...note,...changes,id:note.id||uuid(),base_revision:note.base_revision||0,mutation_id:uuid(),dirty:true,conflict:null,updated:Date.now()};
}
export function applySync(notes, reply) {
  const result=structuredClone(notes);
  for (const ack of reply.results) {
    const note=result.find(n=>n.id===ack.id);
    if (!note || note.mutation_id!==ack.mutation_id) continue;
    if (ack.status==='accepted') {note.base_revision=ack.revision;note.dirty=false;note.conflict=null;}
    else note.conflict=ack.remote || {revision:0,deleted:true};
  }
  for (const remote of reply.notes) {
    const index=result.findIndex(n=>n.id===remote.id);
    if(index>=0 && (result[index].dirty || result[index].conflict)) continue;
    const note={...remote,base_revision:remote.revision,dirty:false,conflict:null,deleted:!!remote.deleted};
    if(index>=0)result[index]=note;else result.push(note);
  }
  return result;
}
export function outgoing(notes) {
  return notes.filter(n=>n.dirty&&!n.conflict).slice(0,100).map(n=>({id:n.id,mutation_id:n.mutation_id,base_revision:n.base_revision,title:n.title,body:n.body,deleted:!!n.deleted}));
}
export function searchItems(state, query) {
  const normalize=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const terms=normalize(query).split(/\s+/).filter(Boolean);
  return state.snapshot.items.filter(item=>terms.every(t=>normalize(item.title+' '+item.text).includes(t)));
}
let database;
function openDatabase(){return new Promise((resolve,reject)=>{if(database){resolve(database);return;}const request=indexedDB.open('campanario-mobile-v1',1);request.onupgradeneeded=()=>request.result.createObjectStore('state');request.onerror=()=>reject(request.error);request.onsuccess=()=>{database=request.result;resolve(database);};});}
export async function loadState(){
  if(window.CampanarioNative){const raw=window.CampanarioNative.loadState();if(raw==='!ERROR')throw new Error('Falha ao abrir armazenamento protegido. Os dados foram preservados.');return raw?validateState(JSON.parse(raw)):emptyState();}
  const db=await openDatabase();return new Promise((resolve,reject)=>{const req=db.transaction('state').objectStore('state').get('main');req.onsuccess=()=>{const data=req.result?validateState(req.result):emptyState();const temp=readSessionToken();if(data.connection&&temp&&temp.server===data.connection.server&&temp.device_id===data.connection.device_id)data.connection.token=temp.token;resolve(data);};req.onerror=()=>reject(req.error);});
}
export async function saveState(value){
  validateState(value);const encoded=JSON.stringify(value);
  if(new TextEncoder().encode(encoded).length>8_000_000)throw new Error('Armazenamento local excede 8 MB. Exporte ou remova conteudo antes de continuar.');
  if(window.CampanarioNative){if(!window.CampanarioNative.saveState(encoded))throw new Error('Nao foi possivel gravar no armazenamento protegido');return;}
  const safe=structuredClone(value);if(safe.connection){writeSessionToken(safe.connection);safe.connection.token='';}else clearSessionToken();
  const db=await openDatabase();return new Promise((resolve,reject)=>{const tx=db.transaction('state','readwrite');tx.objectStore('state').put(safe,'main');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||new Error('Gravacao cancelada'));});
}
function readSessionToken(){try{const s=JSON.parse(sessionStorage.getItem('campanario-pages-session'));return s&&typeof s.token==='string'?s:null;}catch{return null;}}
function writeSessionToken(c){try{if(c.token)sessionStorage.setItem('campanario-pages-session',JSON.stringify({server:c.server,device_id:c.device_id,token:c.token}));}catch{}}
function clearSessionToken(){try{sessionStorage.removeItem('campanario-pages-session');}catch{}}
export async function eraseState(){
  clearSessionToken();
  if(window.CampanarioNative){if(!window.CampanarioNative.clearState())throw new Error('Nao foi possivel apagar o armazenamento');return;}
  const db=await openDatabase();return new Promise((resolve,reject)=>{const tx=db.transaction('state','readwrite');tx.objectStore('state').clear();tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});
}
