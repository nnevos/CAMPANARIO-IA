"""Offline, source-first investigative case workspace (R3.2).

Case files live exclusively under CAMPANARIO-DATABASE/dados/cases.  No SQLite
schema or dependency is added. Raw evidence is copied byte-for-byte, hashed and
never rewritten; metadata is an atomic JSON ledger. No LLM inference is trusted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

MAX_BYTES = 1024 * 1024 * 1024  # 1 GiB, streamed; bounded by storage, not RAM
MAX_ITEMS = 4096
_ALLOWED = {'.csv', '.json', '.txt', '.log', '.pdf', '.xlsx', '.jpg', '.jpeg', '.png', '.zip', '.md', '.docx', '.html', '.htm'}
_ID = re.compile(r'^[a-f0-9]{32}$')


class CaseError(ValueError):
    """Predictable, non-sensitive workspace failure."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _safe(value, limit=400):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
        raise CaseError('Texto vazio, longo ou com caracteres de controle')
    return value.strip()


def _write_json(path: Path, data: dict):
    # Atomically replace metadata; avoid modifying original evidence.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.ledger-', suffix='.tmp', delete=False) as file:
            tmp = Path(file.name)
            json.dump(data, file, ensure_ascii=False, sort_keys=True, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


class CaseWorkspace:
    def __init__(self, data_dir: Path):
        data_dir = Path(data_dir).resolve(strict=True)
        # Explicit external repository anchor, not the IA tree or shared .venv.
        if not data_dir.is_dir() or data_dir.name != 'dados' or data_dir.parent.name != 'CAMPANARIO-DATABASE':
            raise CaseError('Configurar CAMPANARIO_DATA_DIR em CAMPANARIO-DATABASE/dados existente')
        self.root = data_dir / 'cases'

    def _dir(self, case_id: str) -> Path:
        if not _ID.fullmatch(case_id):
            raise CaseError('Identificador de caso invalido')
        base = self.root / case_id
        if base.is_symlink() or not base.is_dir():
            raise CaseError('Caso inexistente ou link nao permitido')
        return base

    def _load(self, case_id: str):
        base = self._dir(case_id)
        ledger = base / 'case.json'
        if ledger.is_symlink():
            raise CaseError('Ledger com link nao permitido')
        try:
            data = json.loads(ledger.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise CaseError('Ledger indisponivel ou invalido') from exc
        if data.get('case_id') != case_id or data.get('schema') != 1:
            raise CaseError('Ledger incompatível')
        return base, data

    def create(self, title: str, objective: str, authorized_by: str) -> str:
        title, objective, authorized_by = _safe(title, 180), _safe(objective, 1000), _safe(authorized_by, 180)
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise CaseError('Raiz dos casos nao pode ser link')
        case_id = uuid4().hex
        base = self.root / case_id
        base.mkdir(mode=0o700)
        (base / 'originals').mkdir(mode=0o700)
        _write_json(base / 'case.json', {'schema': 1, 'case_id': case_id, 'title': title,
                    'objective': objective, 'authorized_by': authorized_by, 'created_at': _now(),
                    'evidence': [], 'events': [], 'hypotheses': [], 'audit': [{'action':'case_created','at':_now()}]})
        return case_id

    def read(self, case_id: str) -> dict:
        return self._load(case_id)[1]

    def add_evidence(self, case_id: str, source: Path, origin: str, acquired_by: str) -> dict:
        origin, acquired_by = _safe(origin, 300), _safe(acquired_by, 180)
        source = Path(source)
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in _ALLOWED:
            raise CaseError('Fonte invalida, link ou formato nao permitido')
        if not 0 < source.stat().st_size <= MAX_BYTES:
            raise CaseError('Arquivo vazio ou acima da capacidade de 1 GiB')
        base, doc = self._load(case_id)
        if len(doc['evidence']) >= MAX_ITEMS:
            raise CaseError('Limite de evidencias atingido')
        if (base / 'originals').is_symlink():
            raise CaseError('Pasta de originais nao pode ser link')
        eid = 'E' + uuid4().hex[:12]
        target = base / 'originals' / (eid + source.suffix.lower())
        # Open with exclusive creation; preserve source bytes, no ZIP extraction.
        try:
            with source.open('rb') as inp, target.open('xb') as out:
                copied = 0
                for block in iter(lambda: inp.read(1 << 20), b''):
                    copied += len(block)
                    if copied > MAX_BYTES:
                        raise CaseError('Arquivo cresceu durante a copia')
                    out.write(block)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        sha = _sha256(target)
        entry = {'id': eid, 'filename': source.name[:180], 'stored_as': target.name,
                 'sha256': sha, 'size': copied, 'origin': origin,
                 'acquired_by': acquired_by, 'acquired_at': _now(),
                 'status': 'imported_unverified'}
        doc['evidence'].append(entry)
        doc['audit'].append({'action':'evidence_imported', 'evidence_id': eid, 'at':_now()})
        _write_json(base / 'case.json', doc)
        return entry

    def verify(self, case_id: str) -> dict:
        base, doc = self._load(case_id)
        checks = []
        for item in doc['evidence']:
            name = item['stored_as']
            candidate = base / 'originals' / name
            safe_name = Path(name).name == name and not candidate.is_symlink()
            good = bool(safe_name and candidate.is_file() and candidate.stat().st_size == item['size']
                        and _sha256(candidate) == item['sha256'])
            checks.append({'evidence_id': item['id'], 'integrity_ok': good})
        return {'case_id': case_id, 'integrity_ok': all(x['integrity_ok'] for x in checks), 'items': checks}

    def propose_log_events(self, case_id: str, evidence_id: str) -> list[dict]:
        """Preview CSV/JSON records only; never auto-persist or assert an event occurred.

        Both timestamp and action must be explicit source fields. Values are
        untrusted and are limited for safe display. No arbitrary ZIP processing.
        """
        import csv
        base, doc = self._load(case_id)
        entry = next((e for e in doc['evidence'] if e['id'] == evidence_id), None)
        if entry is None:
            raise CaseError('Fonte desconhecida')
        path = base / 'originals' / entry['stored_as']
        if path.is_symlink() or not path.is_file() or _sha256(path) != entry['sha256']:
            raise CaseError('Fonte adulterada ou ausente')
        if path.suffix.lower() not in ('.csv', '.json'):
            raise CaseError('Propostas disponiveis somente para CSV/JSON')
        if path.stat().st_size > 2_000_000:
            raise CaseError('Arquivo grande demais para proposta estruturada')
        try:
            raw = path.read_text(encoding='utf-8-sig')
            if path.suffix.lower() == '.json':
                loaded = json.loads(raw)
                rows = loaded if isinstance(loaded, list) else [loaded]
            else:
                rows = list(csv.DictReader(raw.splitlines()))
        except (UnicodeError, ValueError, csv.Error) as exc:
            raise CaseError('Dados estruturados invalidos') from exc
        proposed = []
        for i, row in enumerate(rows[:100]):
            if not isinstance(row, dict):
                continue
            stamp = row.get('timestamp')
            action = row.get('action')
            if not isinstance(stamp, str) or not isinstance(action, str):
                continue
            try:
                dt = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    continue
                action = _safe(action, 200)
            except (ValueError, CaseError):
                continue
            proposed.append({'source_id': evidence_id, 'row': i + 1,
                             'date_time': dt.isoformat(), 'description': action,
                             'classification': 'reported', 'confirmed': False})
        return proposed

    def add_event(self, case_id: str, date_time: str, description: str, evidence_ids: list[str],
                  classification: str = 'reported') -> dict:
        # User-supplied chronology, no inferred causal chain.
        date_time = _safe(date_time, 45)
        try:
            parsed = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
        except ValueError as exc:
            raise CaseError('Data/hora precisa ser ISO 8601') from exc
        if parsed.tzinfo is None:
            raise CaseError('Informar fuso horario explicitamente')
        description = _safe(description, 1000)
        if classification not in ('reported', 'documented', 'hypothesis'):
            raise CaseError('Classificacao de evento invalida')
        base, doc = self._load(case_id)
        known = {e['id'] for e in doc['evidence']}
        if not evidence_ids or any(e not in known for e in evidence_ids):
            raise CaseError('Evento precisa de IDs de evidencias existentes')
        event = {'id': 'T' + uuid4().hex[:12], 'date_time': parsed.isoformat(),
                 'description': description, 'evidence_ids': sorted(set(evidence_ids)),
                 'classification': classification, 'recorded_at': _now()}
        doc['events'].append(event)
        doc['audit'].append({'action': 'event_recorded', 'event_id': event['id'], 'at':_now()})
        _write_json(base / 'case.json', doc)
        return event

    def add_hypothesis(self, case_id: str, statement: str, supporting: list[str],
                       opposing: list[str], next_check: str) -> dict:
        base, doc = self._load(case_id)
        known = {e['id'] for e in doc['evidence']}
        if any(e not in known for e in supporting + opposing):
            raise CaseError('Hipotese referencia evidencia inexistente')
        if set(supporting) & set(opposing):
            raise CaseError('Uma evidencia nao pode ser simultaneamente pro e contra na mesma hipotese')
        item = {'id': 'H' + uuid4().hex[:12], 'statement': _safe(statement, 500),
                'supporting': sorted(set(supporting)), 'opposing': sorted(set(opposing)),
                'next_check': _safe(next_check, 500), 'status': 'unresolved', 'recorded_at': _now()}
        doc['hypotheses'].append(item)
        doc['audit'].append({'action':'hypothesis_recorded', 'hypothesis_id':item['id'], 'at':_now()})
        _write_json(base / 'case.json', doc)
        return item

    def review(self, case_id: str) -> dict:
        """Evidence-linked deterministic analysis, not semantic investigation.

        Time separations are clock arithmetic only. Hypotheses are never scored
        as true or false by number of sources; each retains unresolved status.
        """
        doc = self.read(case_id)
        integrity = self.verify(case_id)
        ordered = sorted(doc['events'], key=lambda x: x['date_time'])
        intervals = []
        for previous, current in zip(ordered, ordered[1:]):
            start = datetime.fromisoformat(previous['date_time'])
            end = datetime.fromisoformat(current['date_time'])
            minutes = round((end - start).total_seconds() / 60, 2)
            intervals.append({'before': previous['id'], 'after': current['id'],
                              'elapsed_minutes': minutes,
                              'meaning': 'diferença entre horários declarados; não causalidade'})
        hypothesis_matrix = [{'hypothesis_id': h['id'], 'statement': h['statement'],
                              'supporting_evidence': h['supporting'],
                              'opposing_evidence': h['opposing'],
                              'next_check': h['next_check'], 'verdict': 'unresolved'}
                             for h in doc['hypotheses']]
        return {'case_id': case_id, 'integrity_ok': integrity['integrity_ok'],
                'events_count': len(ordered), 'intervals': intervals,
                'hypothesis_matrix': hypothesis_matrix,
                'limitations': ['registros humanos, não fatos externos confirmados',
                                'intervalos não indicam autoria, causa nem trajetos',
                                'hipóteses permanecem inconclusivas',
                                'nenhum documento foi autenticado pelo motor']}

    def dossier(self, case_id: str) -> str:
        doc = self.read(case_id)
        check = self.verify(case_id)
        lines = ['# Dossiê de caso — ' + doc['title'], '',
                 '**Status:** análise documental provisória; não prova fatos externos, culpa ou causalidade.',
                 '**Objetivo declarado:** ' + doc['objective'],
                 '**Responsável pela autorização informada:** ' + doc['authorized_by'],
                 '**Caso:** `' + case_id + '`',
                 '**Integridade dos originais:** ' + ('OK' if check['integrity_ok'] else 'FALHA — NÃO UTILIZAR'),
                 '', '## Evidências importadas (originais não interpretados)']
        for item in doc['evidence']:
            ok = next(x['integrity_ok'] for x in check['items'] if x['evidence_id'] == item['id'])
            lines.append(f"- [{item['id']}] {item['filename']} | SHA-256 `{item['sha256']}` | origem declarada: {item['origin']} | integridade: {'OK' if ok else 'FALHA'}")
        lines += ['', '## Cronologia declarada (não confirma ocorrência)']
        for event in sorted(doc['events'], key=lambda x:x['date_time']):
            lines.append(f"- {event['date_time']} — {event['description']} ({event['classification']}) [fontes: {', '.join(event['evidence_ids'])}]")
        lines += ['', '## Hipóteses concorrentes — não verificadas']
        for item in doc['hypotheses']:
            lines.append(f"- {item['statement']} | a favor: {', '.join(item['supporting']) or 'nenhuma'} | contra: {', '.join(item['opposing']) or 'nenhuma'} | verificar: {item['next_check']}")
        review = self.review(case_id)
        lines += ['', '## Intervalos entre horários declarados']
        for delta in review['intervals']:
            lines.append(f"- {delta['before']} → {delta['after']}: {delta['elapsed_minutes']} minutos (sem inferência causal).")
        lines += ['', '## Limitações e próximos passos',
                  '- Importação não autentica a origem nem verifica o conteúdo das fontes.',
                  '- Eventos e hipóteses são declarações humanas; sem extração automática ou inferência de culpa.',
                  '- Checar autoria, horários, fuso, completude e registros independentes antes de concluir.',
                  '- Nenhuma busca, alteração em sistemas externos ou decisão foi executada.']
        return '\n'.join(lines) + '\n'
