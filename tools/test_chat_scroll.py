from playwright.sync_api import sync_playwright
from pathlib import Path
import os
p=Path(__file__).resolve().parents[1]/'src/campanario/web/index.html'
html=p.read_text().replace("const $=id=>","const localStorage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};const $=id=>").replace("crypto.randomUUID()","'test-client'")
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
 for width,height in [(1440,900),(390,844)]:
  page=b.new_page(viewport={'width':width,'height':height})
  errs=[]
  page.on('pageerror', lambda err: errs.append(str(err)))
  page.route('**/api/v1/**',lambda r:r.fulfill(status=404,content_type='application/json',body='{}'))
  page.set_content(html,wait_until='load')
  page.evaluate('''() => { for(let i=0;i<32;i++)addTurn(i%2?'assistant':'user','linha de conversa '.repeat(40),'morgana');goLatest() }''')
  page.wait_for_timeout(80)
  state=page.evaluate('''() => {let s=stage;return {h:s.clientHeight,total:s.scrollHeight,top:s.scrollTop,bottom:atLatest(),outer:document.body.scrollHeight}}''')
  assert state['total']>state['h']*2, state
  assert state['bottom'],state
  page.locator('#stage').hover()
  page.mouse.wheel(0,-1800)
  page.wait_for_timeout(130)
  before=page.evaluate('stage.scrollTop')
  assert before<state['top']-300,(before,state)
  assert page.locator('#jumpLatest').is_visible()
  page.evaluate("handleRuntimeEvent({sequence:1,event_type:'AGENT_RESPONSE_STARTED',payload:{agent_id:'morgana'}})")
  page.evaluate("handleRuntimeEvent({sequence:2,event_type:'AGENT_RESPONSE_CHUNK',payload:{agent_id:'morgana',text:'conteudo de resposta '.repeat(35)}})")
  page.wait_for_timeout(75)
  now=page.evaluate('stage.scrollTop')
  assert abs(now-before)<5, (before,now)
  page.locator('#jumpLatest').click()
  page.wait_for_timeout(75)
  assert page.evaluate('atLatest()')
  assert page.locator('#jumpLatest').is_hidden()
  page.evaluate("handleRuntimeEvent({sequence:3,event_type:'AGENT_RESPONSE_CHUNK',payload:{agent_id:'morgana',text:'fim de resposta '.repeat(50)}})")
  page.wait_for_timeout(75)
  assert page.evaluate('atLatest()')
  assert not errs, errs
  print('PASS',width,height,'manual_scroll','preserve_read_position','stream_autoscroll','jump_to_latest','js_errors=0')
  page.close()
 b.close()
