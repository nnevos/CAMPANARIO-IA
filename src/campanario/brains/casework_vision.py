"""Optional local visual *leads* for case images; never factual proof.

A visual model's output is not entered into the evidence vault as an observation,
and must never be used to identify people, accuse anyone, or infer hidden events.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
from pathlib import Path

from campanario.brains.casework import CaseWorkspace, _sha256
from campanario.config import get_settings


def local_visual_leads(workspace: CaseWorkspace, case_id: str, limit: int = 2) -> dict:
    if os.environ.get('CAMPANARIO_CASE_VISION_ENABLED', str(get_settings().case_vision_enabled)).lower() not in ('1', 'true', 'yes'):
        return {'status': 'disabled', 'leads': [], 'reason': 'modelo visual local desativado'}
    model = os.environ.get('CAMPANARIO_CASE_VISION_MODEL', get_settings().case_vision_model)
    if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,90}', model):
        return {'status': 'unavailable', 'leads': [], 'reason': 'modelo visual inválido'}
    if not workspace.verify(case_id)['integrity_ok']:
        return {'status': 'integrity_failed', 'leads': [], 'reason': 'hash de original não confere'}
    doc = workspace.read(case_id)
    originals = workspace._dir(case_id) / 'originals'
    leads = []
    for item in doc['evidence']:
        if len(leads) >= min(max(limit, 0), 2):
            break
        source = originals / item['stored_as']
        if source.suffix.casefold() not in ('.png', '.jpg', '.jpeg'):
            continue
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 5_000_000 or _sha256(source) != item['sha256']:
            return {'status': 'integrity_failed', 'leads': [], 'reason': 'original alterado ou acima do limite'}
        try:
            from PIL import Image
            with Image.open(source) as image:
                if image.width * image.height > 12_000_000:
                    continue
                image.verify()
            payload = json.dumps({
                'model': model, 'stream': False,
                'prompt': ('Descreva apenas texto ou objetos visualmente aparentes, sem identificar '
                           'pessoas, imaginar eventos, intenções, culpados ou causas. '
                           'Declare incerteza. A saída é uma pista NÃO VERIFICADA.'),
                'images': [base64.b64encode(source.read_bytes()).decode('ascii')],
                'options': {'temperature': 0, 'num_predict': 180}
            }).encode('utf-8')
            req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=payload,
                                         headers={'Content-Type': 'application/json'}, method='POST')
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=25) as reply:
                response = json.load(reply)
            value = response.get('response')
            if not isinstance(value, str) or not value.strip():
                raise ValueError('resposta vazia')
            leads.append({'evidence_id': item['id'], 'sha256': item['sha256'],
                          'description': value.strip()[:900], 'status': 'unverified_visual_suggestion'})
        except (Exception) as exc:
            # Do not leak private file paths or model outputs on error.
            return {'status': 'unavailable', 'leads': leads,
                    'reason': 'modelo visual local indisponível: ' + type(exc).__name__}
    return {'status': 'provisional' if leads else 'no_supported_images', 'leads': leads,
            'reason': 'pistas de modelo visual precisam revisão humana; não são evidências'}
