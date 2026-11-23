"""Read-only Maps V2 setup diagnostics. No GPS, network outside loopback or writes."""
from __future__ import annotations
import socket
from urllib.parse import urlsplit
from campanario.app.navigation_v2 import _loopback_url

SERVICES=(('Motor OSRM carro','CAMPANARIO_MAPS_ROUTER_URL','http://127.0.0.1:5000'),
          ('Motor OSRM caminhada','CAMPANARIO_MAPS_WALK_ROUTER_URL','http://127.0.0.1:5001'),
          ('Busca Nominatim','CAMPANARIO_MAPS_GEOCODER_URL','http://127.0.0.1:8088'),
          ('Categorias Overpass','CAMPANARIO_MAPS_OVERPASS_URL','http://127.0.0.1:12345'))


def diagnose():
    results=[]
    for name,var,default in SERVICES:
        try:
            endpoint=_loopback_url(var,default)
            url=urlsplit(endpoint)
            port=url.port or 80
            with socket.create_connection((url.hostname,port),timeout=1):
                status='PORTA ABERTA (nao comprova grafo OSM importado)'
        except (ValueError,OSError,TimeoutError):
            endpoint='indisponivel'
            status='INDISPONIVEL'
        results.append((name,endpoint,status))
    return results

if __name__=='__main__':
    print('CAMPANARIO MAPS V2 - Diagnostico local')
    print('Nao consulta GPS, nao altera bancos, nao baixa mapas.\n')
    for name,endpoint,status in diagnose():
        print(f'{name}: {status}\n  {endpoint}')
    print('\nVeja docs/operations/INSTALACAO_MAPS_V2.md para preparar OSRM/Nominatim/Overpass.')
