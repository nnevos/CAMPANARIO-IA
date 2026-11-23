import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const script=readFileSync(new URL('../../src/campanario/web/static/navigation-v2.js',import.meta.url),'utf8');
function session({gps=null}={}){
  const listeners={};const payloads=[];const elements={};
  const getEl=id=>elements[id]??(elements[id]={value:'',textContent:'',disabled:false,checked:false,hidden:false,
    replaceChildren(){this.textContent=''},append(){}});
  const document={getElementById:getEl,createElement:tag=>({type:'',className:'',style:{},textContent:'',hidden:false,
    addEventListener(){},append(){}}),body:{appendChild(){}},querySelector(){return null;}};
  const window={addEventListener:(name,cb)=>{listeners[name]=cb;},dispatchEvent(){},speechSynthesis:{cancel(){}}};
  const navigator=gps?{geolocation:{getCurrentPosition:(ok,fail)=>ok({coords:{latitude:-25.4,longitude:-49.2,accuracy:gps},timestamp:Date.now()})}}:{};
  const fetch=async(url,options={})=>{
    if(String(url).endsWith('/status'))return {ok:true,json:async()=>({state:'IDLE'})};
    if(String(url).endsWith('/resolve')){
      const data=JSON.parse(options.body);payloads.push(data);
      return {ok:true,json:async()=>({selected:{name:'Rua das Flores, Curitiba',lat:-25.43,lon:-49.27},candidates:[]})};
    }
    throw new Error('unexpected endpoint '+url);
  };
  vm.runInNewContext(script,{window,document,navigator,fetch,localStorage:{getItem:()=>null,setItem(){}},
    CustomEvent:class{},Date,Number,String,Math,Error,Promise,RegExp,encodeURIComponent,console,Intl});
  return {api:window.CampanarioNavigationV2,payloads,elements};
}
test('busca de endereco funciona sem GPS ou origem manual',async()=>{
  const s=session();await s.api.resolve('Rua das Flores, Curitiba');
  assert.equal(s.payloads.length,1);assert.equal(s.payloads[0].query,'Rua das Flores, Curitiba');
  assert.equal(Object.hasOwn(s.payloads[0],'near_lat'),false);
});
test('GPS aproximado informa contexto sem bloquear pesquisa',async()=>{
  const s=session({gps:2500});await s.api.resolve('Rua das Flores, Curitiba');
  assert.equal(s.payloads[0].near_lat,-25.4);assert.equal(s.payloads[0].near_lon,-49.2);
});
test('mais proximo sem origem nao escolhe cidade aleatoria',async()=>{
  const s=session();await assert.rejects(s.api.resolve('mercado mais próximo'),/origem manual/);
  assert.equal(s.payloads.length,0);
});
