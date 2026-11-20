"""UI isolada com APIs e armazenamento nativo simulados; nao e E2E nem teste de Android.
Uso: python tools/diagnostics/render_mock_ui.py --output-dir ./build/ui-qa
Requer playwright e Chromium disponivel (opcional, fora das dependencias de producao).
"""
from pathlib import Path
import re,json,base64
from playwright.sync_api import sync_playwright
import argparse, shutil
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--chromium',default=shutil.which('chromium') or shutil.which('google-chrome'))
args=parser.parse_args()
if not args.chromium: parser.error('Informe --chromium com o executavel instalado')
args.output_dir.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[2];web=root/'src/campanario/web';mobile=root/'apps/mobile/www' 
def inline_images(h,base):
 def repl(m):
  name=m.group(1)
  p=base/name
  return 'src="data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode()+'"'
 return re.sub(r'src="(?:/ui-assets/|assets/)([^"/]+\.svg)"',repl,h)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 h=(web/'index.html').read_text();h=re.sub(r'<script[^>]*src=.*?</script>','',h);h=re.sub(r'<link rel="stylesheet"[^>]*>',lambda m:'<style>'+(web/'static/shell.css').read_text()+'</style>',h);h=inline_images(h,web/'assets')
 page.set_content(h)
 page.evaluate('''() => {const store=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)}});history.replaceState=()=>{};if(!crypto.randomUUID)crypto.randomUUID=()=>Math.random().toString(36).slice(2);window.fetch=async(path,options)=>({ok:true,status:200,json:async()=>path.includes('/remote')?{running:false}:path.includes('/status')?{can_chat:false,components:{runtime:{state:'ready'},model:{state:'unconfigured'},tts:{state:'not_installed'},gps:{state:'not_installed'}}}:path.includes('/runtime')?{release_id:'campanario-0.8.0',default_primary_agent_id:'morgana',model:''}:path.includes('/agents')?[{id:'morgana',name:'Morgana'},{id:'todd',name:'Todd'}]:[]});}''')
 for name in ['chat','workspaces','memory','desktop-settings']:page.add_script_tag(content=(web/f'static/{name}.js').read_text())
 page.wait_for_timeout(1400)
 print('desktop errors',errors)
 page.evaluate('''async (assets) => {for(const img of document.querySelectorAll('img')){const key=(img.getAttribute('src')||'').split('/').pop();if(assets[key])img.src=assets[key];} await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));}''', {f.name:'data:image/svg+xml;base64,'+base64.b64encode(f.read_bytes()).decode() for f in (web/'assets').glob('*.svg')})
 page.screenshot(path=str(args.output_dir/'desktop-inicio.png'))
 page.locator('#settingsIcon').click();page.locator('[data-stab="mobile"]').click();page.wait_for_timeout(200)
 assert page.locator('#mobileAdmin').count()==1
 page.screenshot(path=str(args.output_dir/'desktop-mobile.png'))
 print('desktop settings errors',errors)
 m=browser.new_page(viewport={'width':412,'height':915},is_mobile=True);m.on('pageerror',lambda e:errors.append('mobile: '+str(e)))
 h=(mobile/'index.html').read_text();h=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',h);h=h.replace('<link rel="stylesheet" href="style.css">','<style>'+(mobile/'style.css').read_text()+'</style>');h=re.sub(r'<script.*?</script>','',h);h=inline_images(h,mobile/'assets')
 m.set_content(h)
 m.evaluate('''() => {let raw='';window.CampanarioNative={loadState:()=>raw,saveState:value=>{raw=value;return true},clearState:()=>{raw='';return true},openRelease:()=>{}};if(!crypto.randomUUID)crypto.randomUUID=()=>Math.random().toString(36).slice(2);}''')
 code='\n'.join((mobile/name).read_text().replace('export ','') for name in ['store.mjs','transport.mjs'])+'\n'+re.sub(r'^import .*?;\n','',(mobile/'app.mjs').read_text(),flags=re.M)
 m.add_script_tag(content='(async()=>{'+code+'})()');m.wait_for_timeout(1100)
 print('mobile errors',errors)
 m.screenshot(path=str(args.output_dir/'mobile-inicio.png'))
 m.locator('[data-view="notes"]').click();m.locator('#newNote').click();m.locator('#noteTitle').fill('Projeto offline');m.locator('#noteBody').fill('Revisar o material salvo no aparelho. Funciona sem conexao com o PC.');m.locator('#noteForm button[type="submit"]').click();m.wait_for_timeout(100)
 assert 'Projeto offline' in m.locator('#noteList').inner_text()
 assert 'Projeto offline' in m.evaluate('window.CampanarioNative.loadState()')
 m.screenshot(path=str(args.output_dir/'mobile-notes.png'))
 m.locator('[data-view="chat"]').click();m.locator('#prompt').fill('Lembrar de revisar meu projeto');m.locator('#send').click();m.wait_for_timeout(100)
 assert 'rascunho local' in m.locator('#messages').inner_text()
 assert m.locator('#draftActions button').first.is_disabled()
 print('mobile offline draft preserved; errors',errors)
 assert not errors
 browser.close()
