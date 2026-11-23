"""Bounded, read-only, hash-checked textual evidence retrieval for a case.

Extracted text is untrusted data, never an instruction. The exact excerpts are
returned, not inferred assertions. Unsupported document types are explicit.
"""
from __future__ import annotations

import csv
import io
import json
import re
import os
import shutil
import subprocess
import math
import urllib.request
import urllib.error
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree
from pathlib import Path

from campanario.brains.casework import CaseWorkspace, CaseError, _sha256
from campanario.config import get_settings

MAX_TEXT_BYTES = 2_000_000
MAX_SNIPPETS = 8
MAX_EXTRACTED_LINES = 2500
_STOP = frozenset('a o os as de da do das dos em no na nos nas e ou que qual quais como com para por um uma onde quando sobre caso documento documentos evidencias evidência evidências me diga preciso quero descobrir analisar análise investigue investigacao investigação'.split())
_TOKEN = re.compile(r'[^\W_]+', re.UNICODE)


def _terms(value: str) -> set[str]:
    return {s.casefold() for s in _TOKEN.findall(value) if len(s) > 2 and s.casefold() not in _STOP}


def _ocr_image(path: Path) -> tuple[list[str], str]:
    """Read-only OCR of a verified local image; never run OCR on user commands."""
    if os.environ.get('CAMPANARIO_CASE_OCR_ENABLED', str(get_settings().case_ocr_enabled)).lower() not in ('1', 'true', 'yes'):
        return [], 'formato de imagem requer OCR local (CAMPANARIO_CASE_OCR_ENABLED=1)'
    executable = shutil.which('tesseract')
    if not executable:
        return [], 'Tesseract OCR não instalado no host'
    try:
        from PIL import Image
        with Image.open(path) as picture:
            if picture.width * picture.height > 12_000_000 or picture.width < 1 or picture.height < 1:
                return [], 'imagem fora do limite de 12 megapixels'
            picture.verify()
    except Exception:
        return [], 'imagem ilegível ou inválida'
    try:
        # Fixed argv, no shell, no path supplied by network clients, bounded CPU/time/output.
        run = subprocess.run([executable, str(path), 'stdout', '-l', 'por+eng'],
                             capture_output=True, timeout=12, check=False)
        if run.returncode != 0:
            # The host may not have the pt-BR language package; fail explicitly.
            return [], 'idiomas OCR por+eng indisponíveis ou erro de extração'
        content = run.stdout[:250_000].decode('utf-8', errors='replace')
        return [f'OCR: {line}' for line in content.splitlines()[:MAX_EXTRACTED_LINES]], ''
    except subprocess.TimeoutExpired:
        return [], 'OCR excedeu limite de 12 segundos'
    except OSError:
        return [], 'OCR indisponível'


def _ocr_pdf(path: Path) -> tuple[list[str], str]:
    if os.environ.get('CAMPANARIO_CASE_OCR_ENABLED', str(get_settings().case_ocr_enabled)).lower() not in ('1', 'true', 'yes'):
        return [], 'PDF sem camada de texto; OCR local desativado'
    if not shutil.which('tesseract'):
        return [], 'PDF sem camada de texto; Tesseract OCR ausente'
    try:
        import fitz
        from PIL import Image
    except ImportError:
        return [], 'PDF digitalizado requer PyMuPDF e Pillow para OCR'
    import tempfile
    rows = []
    try:
        with fitz.open(str(path)) as doc:
            if doc.needs_pass:
                return [], 'PDF protegido; OCR não executado'
            for i in range(min(doc.page_count, 6)):
                page = doc[i]
                if page.rect.width * page.rect.height > 2_000_000:
                    return [], 'PDF com página fora do limite de rasterização'
                pix = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
                with tempfile.TemporaryDirectory(prefix='camp-ocr-') as folder:
                    image = Path(folder) / 'page.png'
                    pix.save(str(image))
                    page_rows, error = _ocr_image(image)
                if error:
                    return rows, error
                rows.extend(f'página {i+1}: {line}' for line in page_rows)
        return rows[:MAX_EXTRACTED_LINES], ('OCR limitado às primeiras 6 páginas' if len(rows) else 'OCR não encontrou texto')
    except Exception:
        return [], 'PDF digitalizado ilegível para OCR'


class _SafeHTMLText(HTMLParser):
    """Text only; scripts, styles and HTML instructions never execute."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.lines: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'svg', 'iframe', 'template'):
            self.skip += 1
        elif not self.skip and tag in ('p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3'):
            self.lines.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg', 'iframe', 'template') and self.skip:
            self.skip -= 1
        elif not self.skip and tag in ('p', 'div', 'li', 'tr'):
            self.lines.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.lines.append(data)


def _extract_docx(path: Path) -> tuple[list[str], str]:
    """Extract bounded Word paragraphs; never follow ZIP entries or external relationships."""
    try:
        with zipfile.ZipFile(path) as z:
            entries = z.infolist()
            if len(entries) > 300 or sum(i.file_size for i in entries) > 12_000_000:
                return [], 'DOCX excede limites de descompactação'
            try:
                member = z.getinfo('word/document.xml')
            except KeyError:
                return [], 'DOCX sem documento principal'
            if member.file_size > 4_000_000 or member.compress_size > 4_000_000:
                return [], 'DOCX XML excede limite seguro'
            content = z.read(member)
        root = ElementTree.fromstring(content)
        ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        paragraphs = []
        for paragraph in root.iter(ns + 'p'):
            text = ''.join((node.text or '') for node in paragraph.iter(ns + 't'))
            if text.strip():
                paragraphs.append(text[:1000])
            if len(paragraphs) >= MAX_EXTRACTED_LINES:
                return paragraphs, 'DOCX truncado no limite de extração'
        return paragraphs, ''
    except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError, RuntimeError):
        return [], 'DOCX inválido ou ilegível'


def _extract(path: Path) -> tuple[list[str], str]:
    suffix = path.suffix.casefold()
    if path.stat().st_size > (10_000_000 if suffix in ('.pdf', '.png', '.jpg', '.jpeg') else MAX_TEXT_BYTES):
        return [], 'arquivo excede limite de leitura textual de 2 MB'
    if suffix in ('.html', '.htm'):
        try:
            raw = path.read_text(encoding='utf-8-sig')
            parser = _SafeHTMLText()
            parser.feed(raw)
            return [v.strip()[:1000] for v in ''.join(parser.lines).splitlines() if v.strip()][:MAX_EXTRACTED_LINES], ''
        except (UnicodeError, ValueError):
            return [], 'HTML inválido ou não UTF-8'
    if suffix == '.docx':
        return _extract_docx(path)
    if suffix in ('.txt', '.log', '.md'):
        try:
            return path.read_text(encoding='utf-8-sig').splitlines()[:MAX_EXTRACTED_LINES], ''
        except UnicodeError:
            return [], 'texto não é UTF-8'
    if suffix == '.csv':
        try:
            with path.open(encoding='utf-8-sig', newline='') as stream:
                reader = csv.reader(stream)
                return [' | '.join(cell[:300] for cell in row[:24]) for _, row in zip(range(MAX_EXTRACTED_LINES), reader)], ''
        except (UnicodeError, csv.Error):
            return [], 'CSV inválido'
    if suffix == '.json':
        try:
            obj = json.loads(path.read_text(encoding='utf-8-sig'))
            serialized = json.dumps(obj, ensure_ascii=False, indent=2)
            return serialized.splitlines()[:MAX_EXTRACTED_LINES], ''
        except (ValueError, UnicodeError):
            return [], 'JSON inválido'
    if suffix in ('.png', '.jpg', '.jpeg'):
        return _ocr_image(path)
    if suffix == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            return [], 'leitor pypdf não instalado; PDF não analisado'
        try:
            reader = PdfReader(str(path), strict=True)
            if reader.is_encrypted:
                return [], 'PDF protegido; não analisado'
            rows = []
            for page_no, page in enumerate(reader.pages[:35], 1):
                for line in (page.extract_text() or '').splitlines():
                    rows.append(f'página {page_no}: {line}')
                    if len(rows) >= MAX_EXTRACTED_LINES:
                        return rows, 'texto truncado no limite de extração'
            if not rows and any(bool(getattr(page, 'images', [])) for page in reader.pages[:6]):
                return _ocr_pdf(path)
            return rows, ''
        except Exception:
            return [], 'PDF ilegível ou incompatível'
    if suffix == '.xlsx':
        try:
            from openpyxl import load_workbook
        except ImportError:
            return [], 'leitor openpyxl não instalado; planilha não analisada'
        try:
            book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
            rows = []
            try:
                for sheet in book.worksheets[:10]:
                    for row_number, values in enumerate(sheet.iter_rows(max_row=500, max_col=24, values_only=True), 1):
                        rendered = ' | '.join(str(v)[:250] for v in values if v is not None)
                        if rendered:
                            rows.append(f'aba {sheet.title[:50]} linha {row_number}: {rendered}')
                        if len(rows) >= MAX_EXTRACTED_LINES:
                            return rows, 'planilha truncada no limite de extração'
            finally:
                book.close()
            return rows, ''
        except Exception:
            return [], 'planilha ilegível ou incompatível'
    return [], 'formato sem extração textual segura neste marco'


def _local_embeddings(texts: list[str]) -> list[list[float]]:
    """Opt-in local Ollama embedding transport. Never connects to remote hosts."""
    model = os.environ.get('CAMPANARIO_CASE_EMBED_MODEL', get_settings().case_embed_model)
    if not re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,90}', model):
        raise ValueError('nome do modelo de embedding inválido')
    body = json.dumps({'model': model, 'input': texts}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:11434/api/embed', data=body,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    # Explicitly ignore system HTTP proxy for private case material.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=12) as res:
        result = json.load(res)
    vectors = result.get('embeddings')
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise ValueError('resposta de embedding incompleta')
    for v in vectors:
        if not isinstance(v, list) or len(v) < 8 or len(v) > 4096 or any(
                not isinstance(n, (int, float)) or not math.isfinite(n) for n in v):
            raise ValueError('embedding inválido')
    if any(len(v) != len(vectors[0]) for v in vectors):
        raise ValueError('dimensões incompatíveis')
    return vectors


def _semantic_candidates(question: str, rows: list[tuple]) -> tuple[list[tuple], str]:
    """Rank at most 60 verified text lines; scores are relevance, not truth."""
    if os.environ.get('CAMPANARIO_CASE_SEMANTIC_ENABLED', str(get_settings().case_semantic_enabled)).lower() not in ('1', 'true', 'yes'):
        return [], 'recuperação semântica opcional desativada'
    if not rows:
        return [], 'nenhuma linha legível para recuperação semântica'
    limited = rows[:60]
    try:
        vectors = _local_embeddings([question[:600]] + [r[4][:450] for r in limited])
    except (ValueError, TimeoutError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return [], 'embeddings Ollama local indisponíveis (' + type(exc).__name__ + ')'
    a = vectors[0]
    norm = math.sqrt(sum(x*x for x in a))
    scored = []
    for row, vector in zip(limited, vectors[1:]):
        denom = norm * math.sqrt(sum(x*x for x in vector))
        similarity = sum(x*y for x, y in zip(a, vector)) / denom if denom else -1
        if similarity >= 0.40:
            scored.append((similarity, *row[1:]))
    return sorted(scored, key=lambda x: -x[0])[:MAX_SNIPPETS], ''


def search_case_evidence(workspace: CaseWorkspace, case_id: str, question: str) -> dict:
    """Return only verified, exact excerpts with filename + numbered source lines.

    Hash check occurs immediately before opening each original; no filesystem
    path is accepted from the client. No writes or model calls are performed.
    """
    if not isinstance(question, str) or not question.strip() or len(question) > 600:
        raise ValueError('Pergunta inválida')
    doc = workspace.read(case_id)
    checks = workspace.verify(case_id)
    if not checks['integrity_ok']:
        return {'integrity_ok': False, 'snippets': [], 'unsupported': [], 'searched': 0, 'limitations': ['integridade_falhou']}
    terms = _terms(question)
    candidates = []
    unsupported = []
    scanned = 0
    semantic_rows = []
    base = workspace._dir(case_id) / 'originals'
    for entry in doc['evidence'][:128]:
        path = base / entry['stored_as']
        if path.is_symlink() or not path.is_file() or _sha256(path) != entry['sha256']:
            return {'integrity_ok': False, 'snippets': [], 'unsupported': [], 'searched': scanned, 'limitations': ['integridade_falhou_durante_leitura']}
        lines, reason = _extract(path)
        if reason:
            unsupported.append({'evidence_id': entry['id'], 'reason': reason})
        if not lines:
            continue
        scanned += 1
        for index, line in enumerate(lines, 1):
            cleaned = ' '.join(line.split())[:500]
            if not cleaned:
                continue
            overlap = len(terms & _terms(cleaned))
            if len(semantic_rows) < 60:
                semantic_rows.append((overlap, entry['id'], entry['filename'], index, cleaned, entry['sha256']))
            if overlap:
                candidates.append((overlap, entry['id'], entry['filename'], index, cleaned, entry['sha256']))
    candidates.sort(key=lambda x: (-x[0], x[1], x[3]))
    semantic, semantic_note = _semantic_candidates(question, semantic_rows)
    existing = {(item[1], item[3]) for item in candidates}
    for record in semantic:
        if (record[1], record[3]) not in existing:
            candidates.append((round(record[0], 3), *record[1:]))
    snippets = [{'evidence_id': eid, 'filename': filename, 'line': line, 'quote': quote,
                 'sha256': checksum, 'matched_terms': relevance}
                for relevance, eid, filename, line, quote, checksum in candidates[:MAX_SNIPPETS]]
    return {'integrity_ok': True, 'snippets': snippets, 'unsupported': unsupported,
            'searched': scanned, 'limitations': ['trechos não comprovam veracidade externa',
            'similaridade semântica não comprova verdade ou nexo causal', 'consulta limitada a 60 linhas semânticas'],
            'semantic_note': semantic_note, 'semantic_used': bool(semantic)}

_NUMERIC = re.compile(r'(?<!\w)\d+(?:[.,]\d+)?(?!\w)')


def numeric_disagreements(workspace: CaseWorkspace, case_id: str) -> list[dict]:
    """Find narrow cross-file disagreements, never infer truth or causality.

    Only equivalent surrounding text with a different *single* numeric value
    qualifies. Dates, multiple quantities and distinct wording are ignored.
    """
    doc = workspace.read(case_id)
    if not workspace.verify(case_id)['integrity_ok']:
        return []
    base = workspace._dir(case_id) / 'originals'
    groups: dict[str, list[tuple[str, int, str, str]]] = {}
    for entry in doc['evidence'][:128]:
        path = base / entry['stored_as']
        if path.is_symlink() or not path.is_file() or _sha256(path) != entry['sha256']:
            return []
        rows, _ = _extract(path)
        for idx, row in enumerate(rows[:1000], 1):
            value = ' '.join(row.strip().split())[:350]
            found = _NUMERIC.findall(value)
            if len(found) != 1 or not any(c.isalpha() for c in value):
                continue
            shape = _NUMERIC.sub('<valor>', value).casefold()
            if len(shape) < 16:
                continue
            groups.setdefault(shape, []).append((entry['id'], idx, found[0], value))
    results = []
    for records in groups.values():
        if len({x[0] for x in records}) < 2 or len({x[2] for x in records}) < 2:
            continue
        left = records[0]
        right = next((x for x in records if x[0] != left[0] and x[2] != left[2]), None)
        if right:
            results.append({'first': {'evidence_id': left[0], 'line': left[1], 'quote': left[3]},
                            'second': {'evidence_id': right[0], 'line': right[1], 'quote': right[3]},
                            'status': 'potential_numeric_disagreement',
                            'warning': 'Valores divergentes em frases comparáveis; fonte e contexto ainda requerem revisão'})
        if len(results) >= 8:
            break
    return results
