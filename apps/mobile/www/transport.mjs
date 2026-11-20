export const VERSION='0.8.0';
export function normalizeServer(value){
  const url=new URL(value);
  if(url.protocol!=='https:' || url.username || url.password || url.search || url.hash || !['','/'].includes(url.pathname))throw new Error('Use somente o endereco HTTPS do PC, com a porta. Sem usuario, senha ou caminho.');
  return url.origin;
}
export function versionTuple(value){const m=/^v?(\d+)\.(\d+)\.(\d+)$/.exec(value);if(!m)throw new Error('Versao de release invalida');return m.slice(1).map(Number);}
export function isNewer(value,current=VERSION){const a=versionTuple(value),b=versionTuple(current);for(let i=0;i<3;i++){if(a[i]>b[i])return true;if(a[i]<b[i])return false;}return false;}
export async function request(connection,path,body,timeout=12000){
  if(!connection?.server)throw new Error('Configure o endereco do PC em Conexao');
  const base=normalizeServer(connection.server);
  const headers={'Content-Type':'application/json'};
  if(connection.token)headers.Authorization='Bearer '+connection.token;
  let response;
  try{response=await fetch(base+'/api/companion/v1/'+path,{method:body===undefined?'GET':'POST',headers,body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(timeout),credentials:'omit',redirect:'error',cache:'no-store'});}
  catch{throw new Error('PC indisponivel, certificado nao confiavel ou tempo esgotado. Dados locais preservados.');}
  const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Falha na requisicao: '+response.status);return data;
}
export async function checkRelease(repository){
  if(!/^[A-Za-z0-9][\w.-]{0,99}\/[A-Za-z0-9][\w.-]{0,99}$/.test(repository))throw new Error('Informe dono/repositorio do GitHub');
  const response=await fetch('https://api.github.com/repos/'+repository+'/releases/latest',{headers:{Accept:'application/vnd.github+json'},signal:AbortSignal.timeout(10000),credentials:'omit',redirect:'error'});
  if(!response.ok)throw new Error('Release publica nao encontrada ou limite de consultas atingido');
  const data=await response.json(),url=new URL(data.html_url);
  if(data.draft||data.prerelease||url.protocol!=='https:'||url.hostname!=='github.com'||!url.pathname.startsWith('/'+repository+'/releases/'))throw new Error('Release inesperada');
  return {version:data.tag_name,available:isNewer(data.tag_name),url:url.href};
}
