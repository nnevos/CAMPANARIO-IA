"""Local deterministic utilities; no language model or network service required."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import mimetypes
import os
import platform
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

WRITE = {'notes.save','notes.delete','tasks.save','tasks.delete','library.import','library.rename','library.reindex','library.delete','emergency.save','emergency.delete','memory.save','memory.delete','routines.save','routines.run','files.mkdir','files.copy','files.move','files.delete','backup.restore','planning.import','web.save'}
OPERATIONS = {
 'web.search':'Pesquisar na web (acesso autorizado)','web.read':'Ler página pública e guardar fonte','web.research':'Pesquisa multirresultados com fontes','web.save':'Salvar página consultada na biblioteca offline','web.history':'Histórico de fontes lidas',
 'files.list':'Listar arquivos autorizados','files.search':'Buscar nomes de arquivos','files.read':'Ler arquivo textual','files.find_text':'Pesquisar texto em arquivos','files.duplicates':'Detectar duplicados por SHA-256','files.mkdir':'Criar pasta','files.copy':'Copiar arquivo','files.move':'Mover arquivo','files.delete':'Mover arquivo para lixeira interna',
 'library.import':'Importar documentos suportados','library.rename':'Renomear documento da biblioteca','library.reindex':'Reprocessar documento original','library.search':'Pesquisar biblioteca offline','library.list':'Listar documentos','library.delete':'Remover documento','library.export':'Exportar biblioteca em ZIP',
 'library.retrieve':'Recuperar trechos documentais com evidências de página ou seção',
 'library.document':'Inspecionar metadados e Markdown de documento importado',
 'library.compare':'Comparar duas versões importadas sem inventar divergências',
 'data.inspect':'Inspecionar colunas, tipos e ausências de planilha importada',
 'data.analyze':'Calcular estatísticas, agrupamentos, tendências e filtros de planilha',
 'notes.save':'Criar ou editar nota','notes.list':'Listar ou pesquisar notas','notes.delete':'Excluir nota','tasks.save':'Criar ou editar tarefa','tasks.list':'Listar tarefas','tasks.delete':'Excluir tarefa','planning.export':'Exportar notas e tarefas','planning.import':'Importar notas e tarefas',
 'calc.evaluate':'Calcular expressão aritmética','calc.percent':'Calcular porcentagem','calc.convert':'Converter unidades','calc.dates':'Intervalo de datas','calc.electricity':'Estimar consumo elétrico','calc.battery':'Estimar autonomia de bateria','calc.supplies':'Calcular suprimentos','calc.storage':'Calcular armazenamento',
 'diagnostics.system':'Diagnóstico local','diagnostics.connection':'Verificar conectividade local','emergency.save':'Salvar contato, plano, checklist, suprimento ou ocorrência','emergency.list':'Consultar central de emergência','emergency.delete':'Excluir registro de emergência',
 'backup.list':'Listar backups locais','backup.create':'Criar backup de dados de utilidades','backup.verify':'Verificar integridade do backup','backup.restore':'Restaurar backup com confirmação',
 'routines.save':'Salvar rotina de operações permitidas','routines.list':'Listar rotinas e execuções','routines.run':'Executar rotina com confirmação', 'memory.save':'Salvar memória declarada pelo usuário','memory.list':'Listar memórias estruturadas','memory.delete':'Excluir memória estruturada','operations.history':'Consultar operações',
}
SCHEMA = '''CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL, PRIMARY KEY(kind,id));
CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, sha256 TEXT UNIQUE NOT NULL, content TEXT NOT NULL, pages TEXT NOT NULL, source TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, action TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);'''

# Maxima para importacao LOCAL; a interface faz upload incremental e o
# indexador aplica limites independentes ao texto extraido dos PDFs grandes.
# Arquivos copiados MANUALMENTE ao workspace podem exceder o teto de
# transferencia HTTP, mas continuam limitados para proteger o equipamento.
MAX_LIBRARY_FILE_BYTES = 500_000_000
MAX_LIBRARY_TEXT_CHARS = 8_000_000
MAX_LIBRARY_PAGES = 3_000

def now():return datetime.now(timezone.utc).isoformat()
def required(args, key, limit=10000):
 v=args.get(key)
 if not isinstance(v,str) or not v.strip() or len(v)>limit:raise ValueError(f'{key}: texto obrigatório (máx. {limit} caracteres)')
 return v.strip()
def number(args,key,positive=False):
 v=args.get(key)
 if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or (positive and v<=0):raise ValueError(f'{key}: número inválido')
 return float(v)

def safe_math(expression):
 ops={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.Pow:lambda a,b:a**b,ast.Mod:lambda a,b:a%b}
 def visit(n):
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return float(n.value)
  if isinstance(n,ast.UnaryOp) and type(n.op) in (ast.USub,ast.UAdd):return -visit(n.operand) if isinstance(n.op,ast.USub) else visit(n.operand)
  if isinstance(n,ast.BinOp) and type(n.op) in ops:
   a,b=visit(n.left),visit(n.right)
   if isinstance(n.op,ast.Pow) and abs(b)>12:raise ValueError('Expoente muito grande')
   return ops[type(n.op)](a,b)
  raise ValueError('Expressão não permitida')
 if len(expression)>180:raise ValueError('Expressão longa demais')
 result=visit(ast.parse(expression,mode='eval').body)
 if not math.isfinite(result) or abs(result)>1e18:raise ValueError('Resultado fora dos limites')
 return result

class UtilityService:
 def __init__(self,base:Path,roots:list[Path]|None=None):
  self.base=Path(base).resolve();self.base.mkdir(parents=True,exist_ok=True)
  self.roots=[Path(x).resolve() for x in (roots or [self.base/'arquivos'])]
  for root in self.roots:root.mkdir(parents=True,exist_ok=True)
  from campanario.utilities.web_research import WebResearch
  self.web=None
  self.db=self.base/'utilidades.sqlite3';self.docs=self.base/'documentos';self.docs.mkdir(exist_ok=True)
  with self.connect() as db:
   db.executescript(SCHEMA)
   from campanario.utilities.document_v8 import ensure_schema
   ensure_schema(db)
  self.web=WebResearch(self)
 def connect(self):
  db=sqlite3.connect(self.db,timeout=15);db.row_factory=sqlite3.Row;return db
 def path(self,s,existing=False):
  if not isinstance(s,str) or not s or '\x00' in s:raise ValueError('Caminho inválido')
  p=Path(s).expanduser().resolve(strict=False)
  if not any(p.is_relative_to(root) for root in self.roots):raise PermissionError('Fora das pastas autorizadas')
  if existing and not p.exists():raise FileNotFoundError(str(p))
  return p
 def record(self,kind,arguments):
  uid=arguments.get('id') or str(uuid4())
  if not isinstance(uid,str) or len(uid)>100 or '/' in uid or '\\' in uid:raise ValueError('ID inválido')
  with self.connect() as db:
   prior=db.execute('SELECT created FROM records WHERE kind=? AND id=?',(kind,uid)).fetchone()
   if prior and not arguments.get('id'):raise ValueError('Identificador em uso')
   body={k:v for k,v in arguments.items() if k not in ('confirm','id')}
   db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?)',(kind,uid,json.dumps(body,ensure_ascii=False),prior['created'] if prior else now(),now()))
  return {'id':uid,'kind':kind,'saved':True}
 def list_records(self,kind,a):
  term=str(a.get('query','')).casefold()[:200];rows=[]
  with self.connect() as db:
   for x in db.execute('SELECT * FROM records WHERE kind=? ORDER BY updated DESC LIMIT 1000',(kind,)):
    item={'id':x['id'],**json.loads(x['body']),'created':x['created'],'updated':x['updated']}
    if term in json.dumps(item,ensure_ascii=False).casefold():rows.append(item)
  return {'items':rows[:200],'count':len(rows)}
 def delete_record(self,kind,a):
  uid=required(a,'id',100)
  with self.connect() as db:r=db.execute('DELETE FROM records WHERE kind=? AND id=?',(kind,uid))
  return {'deleted':r.rowcount==1,'id':uid}
 def run(self,op,a,depth=0):
  if op not in OPERATIONS:raise ValueError('Ferramenta não registrada')
  if not isinstance(a,dict):raise ValueError('Parâmetros devem ser objeto JSON')
  status='success';result={}
  try:
   if op in WRITE and a.get('confirm') is not True:raise PermissionError('Confirmação explícita obrigatória: confirm=true')
   if depth>0 and op in ('routines.run','backup.restore','files.delete'):raise PermissionError('Operação não permitida dentro de rotina')
   result=self._execute(op,a,depth)
  except Exception as exc:
   status='failed';result={'error':str(exc),'error_type':type(exc).__name__}
  finally:
   with self.connect() as db:db.execute('INSERT INTO operations VALUES (?,?,?,?,?)',(str(uuid4()),op,status,json.dumps({'arguments':{k:('[redacted]' if any(t in k.lower() for t in ('token','password','secret')) else (str(v)[:300] if k=='content' else v)) for k,v in a.items()},'result':result},ensure_ascii=False,default=str)[:20000],now()))
  return {'tool':op,'status':status,'result':result}
 def _execute(self,op,a,depth):
  if op.startswith('web.'):
   return self.web.execute(op,a)
  if op=='operations.history':
   with self.connect() as db:return {'items':[dict(r) for r in db.execute('SELECT * FROM operations ORDER BY created DESC LIMIT 100')]}
  if op.startswith('notes.') or op.startswith('tasks.') or op.startswith('memory.') or op.startswith('emergency.') or op.startswith('routines.'):
   kind=op.split('.')[0];action=op.split('.')[1]
   if action=='save':
    required(a,'title' if kind!='memory' else 'value')
    if kind=='memory':
     required(a,'source');a={**a,'verification':'user_claim','updated_by':'user'}
    if kind=='tasks' and a.get('status','todo') not in ('todo','doing','done','cancelled'):raise ValueError('Estado de tarefa inválido')
    return self.record(kind,a)
   if action=='list':return self.list_records(kind,a)
   if action=='delete':return self.delete_record(kind,a)
   if op=='routines.run':
    uid=required(a,'id',100)
    with self.connect() as db:r=db.execute('SELECT body FROM records WHERE kind=? AND id=?',('routines',uid)).fetchone()
    if not r:raise ValueError('Rotina não encontrada')
    actions=json.loads(r['body']).get('steps',[])
    if not isinstance(actions,list) or len(actions)>20:raise ValueError('Rotina inválida')
    results=[]
    for step in actions:
     if not isinstance(step,dict) or step.get('tool') not in ('notes.save','tasks.save','diagnostics.system','calc.evaluate','emergency.list','library.search'):
      raise PermissionError('Rotina contém ferramenta fora da lista de autorização')
     args=step.get('arguments',{})
     if not isinstance(args,dict):raise ValueError('Argumentos inválidos na rotina')
     results.append(self.run(step['tool'],{**args,'confirm':True},depth+1))
     if results[-1]['status']!='success':break
    return {'steps':results,'completed':len(results)==len(actions) and all(x['status']=='success' for x in results)}
  if op.startswith('files.'):
   if op in ('files.list','files.search','files.duplicates','files.find_text'):
    root=self.path(a.get('path',str(self.roots[0])),True)
    if not root.is_dir():raise ValueError('Diretório requerido')
    if op=='files.list':
     offset=min(1_000_000,max(0,int(a.get('offset',0))))
     entries=sorted((p for p in root.iterdir() if not p.is_symlink()),
                    key=lambda p:(not p.is_dir(),p.name.casefold()))
     total=len(entries)
     return {'items':[{'name':p.name,'path':str(p),'directory':p.is_dir(),
                      'bytes':p.stat().st_size,
                      'modified':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()}
                      for p in entries[offset:offset+100]],
             'total':total,'offset':offset,'page_size':100,
             'has_more':offset+100<total}
    candidates=(p for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    if op=='files.search':return {'items':[str(p) for p in candidates if str(a.get('query','')).casefold() in p.name.casefold() and (not a.get('extension') or p.suffix.lower()==str(a['extension']).lower())][:200]}
    if op=='files.duplicates':
     matches={};count=0
     for p in candidates:
      if count>=1000:break
      if p.stat().st_size>100_000_000:continue
      hashval=hashlib.sha256(p.read_bytes()).hexdigest();matches.setdefault(hashval,[]).append(str(p));count+=1
     return {'duplicates':{k:v for k,v in matches.items() if len(v)>1},'scanned':count}
    found=[];q=required(a,'query',200).casefold()
    for p in candidates:
     if len(found)>=100:break
     if p.suffix.lower() not in ('.txt','.md','.json','.csv','.log') or p.stat().st_size>2_000_000:continue
     try:
      for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
       if q in line.casefold():found.append({'file':str(p),'line':n,'excerpt':line[:400]})
       if len(found)>=100:break
     except (UnicodeError,OSError):continue
    return {'matches':found}
   if op=='files.read':
    p=self.path(required(a,'path'),True)
    if p.suffix.lower() not in ('.txt','.md','.json','.csv','.log') or p.stat().st_size>2_000_000:raise ValueError('Formato ou tamanho não permitido')
    return {'path':str(p),'content':p.read_text(encoding='utf-8')[:100000]}
   if op=='files.mkdir':
    p=self.path(required(a,'path'));p.mkdir(parents=True,exist_ok=False);return {'created':str(p)}
   if op in ('files.copy','files.move'):
    src=self.path(required(a,'source'),True);dst=self.path(required(a,'destination'))
    if not src.is_file() or dst.exists() or not dst.parent.is_dir():raise ValueError('Origem inválida, destino existente ou diretório pai ausente')
    if op=='files.copy':shutil.copy2(src,dst)
    else:shutil.move(str(src),str(dst))
    return {'source':str(src),'destination':str(dst)}
   if op=='files.delete':
    src=self.path(required(a,'path'),True)
    if not src.is_file():raise ValueError('Somente arquivos comuns')
    trash=self.base/'lixeira';trash.mkdir(exist_ok=True);dst=trash/(str(uuid4())+'_'+src.name);shutil.move(str(src),dst)
    return {'reversible':True,'trash_path':str(dst),'original':str(src)}
  if op.startswith('library.'):
   if op=='library.import':
    from campanario.utilities.document_v8 import import_file
    return import_file(self,a)
   if op in ('library.search','library.list'):
    found=[];term=required(a,'query',200).casefold() if op=='library.search' else ''
    offset=min(1_000_000,max(0,int(a.get('offset',0))))
    page_size=100
    with self.connect() as db:
     # Count real indexed/imported records, not only the first 100 shown.
     total=db.execute('SELECT count(*) FROM documents').fetchone()[0]
     if term:
      # Search is exhaustive across indexed records, rather than silently
      # dropping matches because a file was not among the newest 1000.
      docs=db.execute('SELECT d.*, x.state, x.method, x.errors, x.byte_size FROM documents d '
                      'LEFT JOIN document_details x ON d.id=x.document_id ORDER BY d.created DESC').fetchall()
     else:
      docs=db.execute('SELECT d.*, x.state, x.method, x.errors, x.byte_size FROM documents d '
                      'LEFT JOIN document_details x ON d.id=x.document_id ORDER BY d.created DESC LIMIT ? OFFSET ?',
                      (page_size+1,offset)).fetchall()
     for doc in docs:
      item={'id':doc['id'],'name':doc['name'],'category':doc['category'],
            'source':doc['source'],'sha256':doc['sha256'],'created':doc['created'],
            'state':doc['state'] or 'legacy','method':doc['method'] or 'legacy',
            'bytes':doc['byte_size'], 'errors':json.loads(doc['errors']) if doc['errors'] else []}
      if term:
       hits=[]
       try: pages=json.loads(doc['pages'])
       except (TypeError,ValueError):pages=[]
       for page in pages:
        text=str(page.get('text') or '');loc=text.casefold().find(term)
        if loc>=0:hits.append({'page':page.get('page'),'excerpt':text[max(0,loc-100):loc+len(term)+180]})
        if len(hits)>=10:break
       if not hits and term not in doc['name'].casefold():continue
       item['matches']=hits
      found.append(item)
    if term:
     matched=len(found)
     result=found[offset:offset+page_size]
    else:
     matched=total
     result=found[:page_size]
    return {'documents':result,'count':matched,'total':total,'offset':offset,
            'page_size':page_size,'has_more':offset+len(result)<matched}
   if op=='library.rename':
    uid=required(a,'id',100)
    name=required(a,'name',200)
    if (name in ('.','..') or '/' in name or '\\' in name or '\x00' in name
        or name.strip(' .')!=name or any(ord(c)<32 for c in name)):
     raise ValueError('Nome de documento inválido')
    with self.connect() as db:
     prior=db.execute('SELECT name FROM documents WHERE id=?',(uid,)).fetchone()
     if not prior:raise ValueError('Documento não encontrado')
     if Path(prior['name']).suffix.lower()!=Path(name).suffix.lower():
      raise ValueError('Mantenha a extensão original; o arquivo preservado não será convertido')
     db.execute('UPDATE documents SET name=? WHERE id=?',(name,uid))
    return {'renamed':True,'id':uid,'name':name}
   if op=='library.reindex':
    from campanario.utilities.document_v8 import reindex_document
    return reindex_document(self,required(a,'id',100))
   if op=='library.retrieve':
    from campanario.utilities.document_v8 import retrieve
    return retrieve(self,required(a,'query',500),
                    document_id=str(a.get('document_id') or '')[:100],
                    document_hint=str(a.get('document_hint') or '')[:160],
                    limit=a.get('limit',6))
   if op=='library.document':
    from campanario.utilities.document_v8 import document_info
    return document_info(self,required(a,'document_id',100),
                         markdown=a.get('include_markdown') is True)
   if op=='library.compare':
    from campanario.utilities.document_v8 import compare
    return compare(self,required(a,'document_a',100),required(a,'document_b',100))
   if op=='library.delete':
    uid=required(a,'id',100)
    with self.connect() as db:
     d=db.execute('SELECT name FROM documents WHERE id=?',(uid,)).fetchone()
     if not d:return {'deleted':False}
     try:db.execute('DELETE FROM document_fts WHERE document_id=?',(uid,))
     except sqlite3.OperationalError:pass
     db.execute('DELETE FROM document_sections WHERE document_id=?',(uid,))
     db.execute('DELETE FROM document_details WHERE document_id=?',(uid,))
     db.execute('DELETE FROM documents WHERE id=?',(uid,))
    (self.docs/(uid+Path(d['name']).suffix.lower())).unlink(missing_ok=True)
    return {'deleted':True}
   if op=='library.export':
    dest=self.base/'exports';dest.mkdir(exist_ok=True);path=dest/f'biblioteca-{uuid4().hex}.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
     with self.connect() as db:docs=[dict(x) for x in db.execute('SELECT * FROM documents')]
     z.writestr('metadata.json',json.dumps(docs,ensure_ascii=False))
     for f in self.docs.iterdir():
      if f.is_file():z.write(f,'documents/'+f.name)
    return {'path':str(path),'documents':len(docs)}
  if op.startswith('data.'):
   from campanario.utilities.data_v8 import inspect, analyze
   if op=='data.inspect':return inspect(self,a)
   if op=='data.analyze':return analyze(self,a)
  if op.startswith('calc.'):
   if op=='calc.evaluate':
    expression=required(a,'expression',180);return {'expression':expression,'result':safe_math(expression)}
   if op=='calc.percent':
    val=number(a,'value');pct=number(a,'percent');return {'formula':'value * percent / 100','result':val*pct/100,'unit':a.get('unit','')}
   if op=='calc.convert':
    units={'m':('length',1),'km':('length',1000),'cm':('length',.01),'mm':('length',.001),'ft':('length',.3048),'mi':('length',1609.344),'kg':('mass',1),'g':('mass',.001),'lb':('mass',.45359237),'L':('volume',1),'mL':('volume',.001),'h':('time',3600),'min':('time',60),'s':('time',1),'B':('storage',1),'KB':('storage',1000),'MB':('storage',1e6),'GB':('storage',1e9),'KiB':('storage',1024),'MiB':('storage',1048576),'GiB':('storage',1073741824)}
    origin=required(a,'from',10);target=required(a,'to',10);val=number(a,'value')
    if origin not in units or target not in units or units[origin][0]!=units[target][0]:raise ValueError('Unidades incompatíveis')
    return {'result':val*units[origin][1]/units[target][1],'formula':'value * from_factor / to_factor','unit':target}
   if op=='calc.dates':
    start=date.fromisoformat(required(a,'start',10));end=date.fromisoformat(required(a,'end',10));return {'days':(end-start).days,'start':start.isoformat(),'end':end.isoformat()}
   if op=='calc.electricity':
    w=number(a,'watts',True);hours=number(a,'hours_per_day',True);days=number(a,'days',True)
    return {'kwh':w*hours*days/1000,'formula':'watts * hours_per_day * days / 1000','unit':'kWh'}
   if op=='calc.battery':
    wh=number(a,'capacity_wh',True);w=number(a,'load_watts',True);eff=float(a.get('efficiency',.85))
    if not 0<eff<=1:raise ValueError('Eficiência deve estar entre 0 e 1')
    return {'hours':wh*eff/w,'formula':'capacity_wh * efficiency / load_watts','assumption_efficiency':eff}
   if op=='calc.supplies':
    persons=number(a,'people',True);days=number(a,'days',True);per=number(a,'per_person_per_day',True)
    return {'quantity':persons*days*per,'unit':a.get('unit','unidades'),'formula':'people * days * per_person_per_day','assumption':'consumo informado pelo usuário'}
   if op=='calc.storage':
    count=number(a,'files',True);size=number(a,'size_mb_each',True);return {'total_mb':count*size,'total_gb':count*size/1000,'formula':'files * size_mb_each','assumption':'MB/GB decimais'}
  if op.startswith('diagnostics.'):
   if op=='diagnostics.connection':
    import socket
    try:
     with socket.create_connection(('127.0.0.1',int(a.get('port',11434))),timeout=.5):reachable=True
    except OSError:reachable=False
    return {'host':'127.0.0.1','port':int(a.get('port',11434)),'reachable':reachable,'internet_tested':False}
   info={'platform':platform.platform(),'python':platform.python_version(),'cpu_logical':os.cpu_count(),'disk':{'total':shutil.disk_usage(self.base).total,'used':shutil.disk_usage(self.base).used,'free':shutil.disk_usage(self.base).free},'gpu':'indisponível sem provedor local','sensors':'não consultados'}
   try:
    import psutil
    mem=psutil.virtual_memory();info.update({'ram_total':mem.total,'ram_used':mem.used,'ram_percent':mem.percent,'cpu_percent_sample':psutil.cpu_percent(interval=.1)})
   except ImportError:info['ram']='psutil não instalado'
   return info
  if op=='planning.export':return {'notes':self.list_records('notes',{}),'tasks':self.list_records('tasks',{})}
  if op=='planning.import':
   imported={'notes':0,'tasks':0,'skipped':0}
   for kind in ('notes','tasks'):
    items=a.get(kind,[])
    if not isinstance(items,list) or len(items)>1000:raise ValueError('Lista inválida')
    for item in items:
     if not isinstance(item,dict) or not isinstance(item.get('title'),str):raise ValueError('Item inválido')
     uid=item.get('id')
     if uid:
      with self.connect() as db:exists=db.execute('SELECT 1 FROM records WHERE kind=? AND id=?',(kind,uid)).fetchone()
      if exists:imported['skipped']+=1;continue
     clean={k:v for k,v in item.items() if k not in ('created','updated')}
     self.record(kind,clean);imported[kind]+=1
   return imported
  if op.startswith('backup.'):
   if op=='backup.list':
    folder=self.base/'backups'
    return {'items':[{'filename':p.name,'bytes':p.stat().st_size,'modified':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()} for p in sorted(folder.glob('*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]] if folder.exists() else []}
   if op=='backup.create':
    dest=self.base/'backups';dest.mkdir(exist_ok=True);p=dest/f'campanario-utilidades-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid4().hex[:8]}.zip'
    files=[self.db]+[x for x in self.docs.iterdir() if x.is_file()]
    manifest={'version':1,'created':now(),'files':{('utilidades.sqlite3' if f==self.db else 'documents/'+f.name):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'utilidades somente; não contém banco de chat/memória legada'}
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
     for f in files:z.write(f,'utilidades.sqlite3' if f==self.db else 'documents/'+f.name)
     z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
    return {'path':str(p),'manifest':manifest}
   p=(self.base/'backups'/Path(required(a,'filename')).name).resolve()
   if not p.is_relative_to(self.base/'backups') or not p.is_file():raise ValueError('Backup não encontrado na pasta de backups')
   with zipfile.ZipFile(p) as z:
    names=z.namelist()
    if 'manifest.json' not in names:raise ValueError('Manifesto ausente')
    manifest=json.loads(z.read('manifest.json'))
    if manifest.get('version')!=1:raise ValueError('Versão desconhecida')
    files=manifest.get('files',{})
    if not isinstance(files,dict) or 'utilidades.sqlite3' not in files or len(files)>10000:raise ValueError('Manifesto inválido')
    for name,h in files.items():
     parts=Path(name).parts
     if (name!='utilidades.sqlite3' and (len(parts)!=2 or parts[0]!='documents' or parts[1] in ('.','..'))) or name not in names:
      raise ValueError('Nome de arquivo inválido no backup')
     if z.getinfo(name).file_size>100_000_000 or sum(z.getinfo(f).file_size for f in files)>500_000_000:
      raise ValueError('Backup excede limites de tamanho')
     if not isinstance(h,str) or hashlib.sha256(z.read(name)).hexdigest()!=h:raise ValueError('Integridade inválida')
    if op=='backup.verify':return {'valid':True,'created':manifest['created'],'files':len(files)}
    # never overwrite current data without a preserved rollback copy
    rollback=self._execute('backup.create',{},depth)['path']
    with self.connect() as db:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    temp=self.base/'restore_temp';temp.mkdir(exist_ok=True)
    try:
     for name in files:
      target=temp/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
     with sqlite3.connect(f'file:{temp / "utilidades.sqlite3"}?mode=ro',uri=True) as check:
      if check.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Banco do backup corrompido')
     os.replace(temp/'utilidades.sqlite3',self.db)
     if self.docs.exists():shutil.rmtree(self.docs)
     (temp/'documents').rename(self.docs) if (temp/'documents').exists() else self.docs.mkdir()
    finally:shutil.rmtree(temp,ignore_errors=True)
    return {'restored':True,'rollback_backup':rollback}
  raise ValueError('Operação ainda não implementada')
