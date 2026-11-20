/* CAMPANÁRIO Intelligence V5: HUD orientado a estados REAIS já expostos pela interface. */
(()=>{'use strict';
const core=document.getElementById('coreTelemetryState');
const top=document.getElementById('topState');
const main=document.getElementById('mainLayout');
const status=document.getElementById('statusValue');
if(!core||!top||!main)return;
const update=()=>{
 const state=(top.textContent||'').trim();
 const connected=(status?.textContent||'').trim();
 const current=main.dataset.activeView||'inicio';
 core.textContent=`${current.toUpperCase()} // ${state.toUpperCase()||'AGUARDANDO'}`;
 core.title=`Estado informado pelo aplicativo: ${state}. Conexão: ${connected}`;
 document.body.dataset.hudView=current;
};
new MutationObserver(update).observe(top,{subtree:true,childList:true,characterData:true});
new MutationObserver(update).observe(main,{attributes:true,attributeFilter:['data-active-view']});
update();
})();
