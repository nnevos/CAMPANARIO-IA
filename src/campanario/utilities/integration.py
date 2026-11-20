from pathlib import Path
from campanario.runtime.capabilities import (CapabilityDefinition,CapabilityProvenance,CapabilityProviderKind,CallbackCapabilityProvider)
from campanario.utilities.service import UtilityService, OPERATIONS, WRITE

_SERVICE = None

def service(base:Path|None=None):
 global _SERVICE
 if base is not None:return UtilityService(base)
 if _SERVICE is None:
  from campanario.config import get_settings
  s=get_settings();_SERVICE=UtilityService(s.data_dir/s.memory_environment/'utilidades')
 return _SERVICE

def register_utilities(registry, util=None):
 util=util or service()
 async def invoke(name,args):
  outcome=util.run(name,args)
  if outcome['status']!='success':
   from campanario.runtime.capabilities import CapabilityExecutionError
   raise CapabilityExecutionError(outcome['result']['error'])
  return outcome
 registry.register_provider(CallbackCapabilityProvider('campanario.local.utilities',invoke))
 for name,description in OPERATIONS.items():
  registry.register(CapabilityDefinition(name=name,description=description,provider_id='campanario.local.utilities',provenance=CapabilityProvenance(provider_kind=CapabilityProviderKind.SYSTEM,provider_id='campanario.local.utilities'),input_schema={'type':'object'},output_schema={'type':'object'},permissions=('utilities.write',) if name in WRITE else ('utilities.read',)))
