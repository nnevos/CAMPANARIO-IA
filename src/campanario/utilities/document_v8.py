"""V8 incremental knowledge pipeline for the existing utility SQLite database.

All documents are data. There is no arbitrary Python/SQL execution, no network
access and no replacement of the legacy `documents` table. Large/corrupt
sources fail explicitly; original files and extraction limitations are retained.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import mimetypes
import re
import shutil
import sqlite3
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from campanario.chat.local_library import _fold, _tokens

VERSION = '8.0.1'
SUPPORTED = frozenset({'.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.json', '.log'})
DATA_TYPES = frozenset({'.csv', '.xlsx', '.json'})
MAX_CHARS = 8_000_000
MAX_PAGES = 3_000
MAX_BYTES = 500_000_000

DETAILS_SCHEMA = '''
CREATE TABLE IF NOT EXISTS document_details (
 document_id TEXT PRIMARY KEY, byte_size INTEGER NOT NULL, mime TEXT NOT NULL,
 method TEXT NOT NULL, state TEXT NOT NULL, stage TEXT NOT NULL,
 errors TEXT NOT NULL, markdown TEXT NOT NULL, processor_version TEXT NOT NULL,
 updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_sections (
 document_id TEXT NOT NULL, ordinal INTEGER NOT NULL, page INTEGER,
 heading TEXT NOT NULL, body TEXT NOT NULL, method TEXT NOT NULL,
 evidence_id TEXT NOT NULL, PRIMARY KEY(document_id,ordinal)
);
CREATE INDEX IF NOT EXISTS ix_document_sections_document ON document_sections(document_id);
'''


def ensure_schema(db: sqlite3.Connection) -> None:
    """Additive SQLite migration. Existing documents, chats, and memories untouched."""
    db.executescript(DETAILS_SCHEMA)
    try:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5("
                   "heading, body, document_id UNINDEXED, evidence_id UNINDEXED, "
                   "tokenize='unicode61 remove_diacritics 2')")
        missing = db.execute(
            'SELECT rowid,document_id,heading,body,evidence_id FROM document_sections '
            'WHERE rowid NOT IN (SELECT rowid FROM document_fts) LIMIT 100000'
        ).fetchall()
        if missing:
            db.executemany('INSERT INTO document_fts '
                           '(rowid,document_id,heading,body,evidence_id) VALUES (?,?,?,?,?)',
                           [tuple(row) for row in missing])
            db.commit()
    except sqlite3.OperationalError:
        # Some older Windows SQLite distributions have no FTS5. Safe lexical fallback.
        pass


def _md_cell(value: Any) -> str:
    return str(value if value is not None else '').replace('\\', '\\\\').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def _markdown_table(rows: list[list[Any]]) -> str:
    if not rows:
        return ''
    width = max(len(row) for row in rows)
    header = rows[0]
    line = lambda row: '| ' + ' | '.join(_md_cell(row[j]) if j < len(row) else '' for j in range(width)) + ' |'
    return '\n'.join([line(header), '| ' + ' | '.join(['---'] * width) + ' |',
                      *(line(row) for row in rows[1:])])


def _ocr_pdf_page(path: Path, page_number: int) -> str:
    """Optional LOCAL OCR; fixed executables/argv, bounded raster and subprocesses."""
    if not shutil.which('pdftoppm') or not shutil.which('tesseract'):
        raise RuntimeError('OCR local indisponível: instale pdftoppm e Tesseract')
    with tempfile.TemporaryDirectory(prefix='campanario-ocr-') as folder:
        target = str(Path(folder) / 'page')
        subprocess.run(['pdftoppm', '-f', str(page_number), '-l', str(page_number),
                        '-singlefile', '-scale-to', '1700', '-png', str(path), target],
                       check=True, capture_output=True, timeout=35)
        image = target + '.png'
        if not Path(image).is_file() or Path(image).stat().st_size > 25_000_000:
            raise ValueError('Imagem OCR ausente ou excede o limite local')
        result = subprocess.run(['tesseract', image, 'stdout', '-l', 'por+eng'],
                                check=True, capture_output=True, timeout=40)
        return result.stdout.decode('utf-8', errors='replace').strip()


@dataclass
class Extraction:
    pages: list[dict[str, Any]]
    markdown: str
    method: str
    warnings: list[str]
    state: str


def extract_document(path: Path, *, ocr: bool = True) -> Extraction:
    """Extract only text genuinely contained in a file, with explicit loss reports."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError('Formato não suportado')
    pages: list[dict[str, Any]] = []
    warnings: list[str] = []
    method = ext.lstrip('.')
    if ext == '.pdf':
        from pypdf import PdfReader
        pdf = PdfReader(str(path), strict=False)
        if pdf.is_encrypted:
            raise ValueError('PDF protegido por senha; não foi possível extrair')
        if len(pdf.pages) > MAX_PAGES:
            raise ValueError('PDF excede o limite de 3000 páginas')
        for number, page in enumerate(pdf.pages, 1):
            try:
                body = (page.extract_text(extraction_mode='layout') or '').strip()
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                # Missing /Contents on a blank/scanned page is not a broken book.
                try:
                    body = (page.extract_text() or '').strip()
                except (KeyError, IndexError, ValueError, TypeError):
                    body = ''
                warnings.append(f'Página {number}: extração textual limitada ({type(exc).__name__})')
            source = 'pdf_text'
            if len(body) < 16:
                if ocr:
                    try:
                        body = _ocr_pdf_page(path, number)
                        source = 'ocr_local'
                        warnings.append(f'Página {number}: OCR local; conferir imagem original e acurácia')
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                        warnings.append(f'Página {number}: OCR indisponível/falhou ({type(exc).__name__})')
                else:
                    warnings.append(f'Página {number}: texto insuficiente; OCR não solicitado')
            if not body:
                warnings.append(f'Página {number}: sem texto recuperável')
            pages.append({'page': number, 'text': body, 'method': source})
        method = 'pdf_text+ocr' if any(p['method'] == 'ocr_local' for p in pages) else 'pdf_text'
    elif ext == '.docx':
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        from docx.oxml.ns import qn
        doc = Document(str(path))
        blocks = []
        for child in doc.element.body.iterchildren():
            if child.tag == qn('w:p'):
                para = Paragraph(child, doc)
                value = para.text.strip()
                if not value:
                    continue
                style = (para.style.name or '') if para.style else ''
                depth = re.search(r'(?:heading|título|titulo)\s*(\d+)', style, re.I)
                if depth:
                    blocks.append('#' * min(6, int(depth.group(1))) + ' ' + value)
                elif 'list' in style.lower() or 'lista' in style.lower():
                    blocks.append('- ' + value)
                else:
                    blocks.append(value)
            elif child.tag == qn('w:tbl'):
                table = Table(child, doc)
                blocks.append(_markdown_table([[c.text for c in row.cells] for row in table.rows]))
        warnings.append('DOCX: paginação e notas de rodapé não são extraídas com fidelidade garantida')
        pages.append({'page': None, 'text': '\n\n'.join(blocks), 'method': 'docx_xml'})
        method = 'docx_xml'
    elif ext == '.xlsx':
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True, keep_links=False)
        try:
            for ws in wb.worksheets:
                rows = []
                for row_number, row in enumerate(ws.iter_rows(values_only=True), 1):
                    if row_number > 20_000:
                        warnings.append(f'Planilha {ws.title}: limite de 20000 linhas extraídas')
                        break
                    rows.append(list(row)[:100])
                page_text = '## Aba: ' + ws.title + '\n\n' + _markdown_table(rows)
                pages.append({'page': None, 'section': ws.title, 'text': page_text,
                              'method': 'xlsx_cached_values'})
        finally:
            wb.close()
        warnings.append('XLSX: fórmulas não executadas; apenas valores armazenados no arquivo')
        method = 'xlsx_cached_values'
    else:
        if path.stat().st_size > MAX_CHARS * 4:
            raise ValueError('Arquivo de texto muito grande para processamento em memória')
        content = path.read_text(encoding='utf-8-sig')
        if ext == '.csv':
            sample = content[:8192]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            except csv.Error:
                dialect = csv.excel
            rows = []
            for i, row in enumerate(csv.reader(io.StringIO(content), dialect), 1):
                if i > 20_000:
                    warnings.append('CSV: limite de 20000 linhas para Markdown')
                    break
                rows.append(row[:100])
            content = _markdown_table(rows)
            method = 'csv_table'
        elif ext == '.json':
            value = json.loads(content)
            content = '```json\n' + json.dumps(value, ensure_ascii=False, indent=2) + '\n```'
            method = 'json_text'
        pages.append({'page': None, 'text': content, 'method': method})
    total = sum(len(p['text']) for p in pages)
    if total > MAX_CHARS:
        raise ValueError('Extração excedeu 8 milhões de caracteres; divida o documento')
    markdown = '\n\n'.join(
        (f'<!-- Página {page["page"]} -->\n\n' if page.get('page') else '') + page['text']
        for page in pages
    )
    state = 'available' if total and not warnings else 'partial'
    return Extraction(pages, markdown, method, warnings, state)


def _sections(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve headings and tables; bound large paragraphs without fabricating text."""
    result = []
    for page in pages:
        heading = str(page.get('section') or '')
        current: list[str] = []
        def flush():
            if not current:
                return
            body = '\n'.join(current).strip()
            current.clear()
            if body:
                result.append({'page': page.get('page'), 'heading': heading,
                               'text': (heading + '\n' + body if heading else body),
                               'method': page.get('method', 'unknown')})
        for line in str(page.get('text', '')).splitlines():
            clean = line.strip()
            if clean.startswith('#') and re.match(r'^#{1,6}\s+', clean):
                flush()
                heading = clean.lstrip('# ').strip()
                continue
            if not clean:
                if len('\n'.join(current)) > 200:
                    flush()
                continue
            # Keep table rows grouped with their Markdown heading.
            if current and sum(len(s) for s in current) > 1300 and not clean.startswith('|'):
                flush()
            current.append(clean)
        flush()
        # Existing PDF often lacks paragraph markers. Build short adjacent line
        # windows so an isolated '20% NEX' header can be read with its next lines.
        if not any(p.get('page') == page.get('page') for p in result):
            text = str(page.get('text', '')).strip()
            if text:
                result.append({'page': page.get('page'), 'heading': heading,
                               'text': text[:1600], 'method': page.get('method', 'unknown')})
    return result


def import_file(util: Any, args: dict[str, Any]) -> dict[str, Any]:
    from campanario.utilities.service import now, required
    path = util.path(required(args, 'path'), existing=True)
    if not path.is_file() or path.suffix.lower() not in SUPPORTED or path.stat().st_size > MAX_BYTES:
        raise ValueError('Arquivo ausente, acima de 500 MB ou não suportado')
    digest = hashlib.sha256()
    with path.open('rb') as src:
        for part in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(part)
    sha = digest.hexdigest()
    with util.connect() as db:
        duplicate = db.execute('SELECT id FROM documents WHERE sha256=?', (sha,)).fetchone()
    if duplicate:
        return {'imported': False, 'duplicate_id': duplicate['id']}
    uid = str(uuid4())
    original = util.docs / (uid + path.suffix.lower())
    shutil.copyfile(path, original)
    # Source deletion after upload never destroys the original.
    category = str(args.get('category') or 'geral')[:100]
    try:
        extraction = extract_document(original, ocr=args.get('ocr', True) is not False)
        error = extraction.warnings
        pages = extraction.pages
        markdown = extraction.markdown
        status = extraction.state
        method = extraction.method
    except Exception as exc:
        error = [f'{type(exc).__name__}: {str(exc)[:250]}']
        pages = []
        markdown = ''
        status = 'error'
        method = path.suffix.lstrip('.')
    entries = _sections(pages)
    with util.connect() as db:
        with db:
            db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)',
                       (uid, path.name, category, sha,
                        '\n'.join(page['text'] for page in pages),
                        json.dumps(pages, ensure_ascii=False), str(path), now()))
            db.execute('INSERT INTO document_details VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (uid, original.stat().st_size,
                        mimetypes.guess_type(path.name)[0] or 'application/octet-stream',
                        method, status, 'concluída' if status != 'error' else 'erro',
                        json.dumps(error, ensure_ascii=False), markdown, VERSION, now()))
            for ordinal, section in enumerate(entries):
                evidence_id = f'library:{uid}:{ordinal}'
                rowid = db.execute('INSERT INTO document_sections VALUES (?,?,?,?,?,?,?)',
                                   (uid, ordinal, section['page'], section['heading'],
                                    section['text'], section['method'], evidence_id)).lastrowid
                try:
                    db.execute('INSERT INTO document_fts '
                               '(rowid,document_id,heading,body,evidence_id) VALUES (?,?,?,?,?)',
                               (rowid, uid, section['heading'], section['text'], evidence_id))
                except sqlite3.OperationalError:
                    pass

    return {'imported': True, 'id': uid, 'pages': len(pages), 'sha256': sha,
            'state': status, 'method': method, 'warnings': error,
            'indexed_sections': len(entries), 'requires_ocr': status == 'partial' and
            any('OCR' in value for value in error) and not any(p.get('text') for p in pages)}


def reindex_document(util: Any, uid: str) -> dict[str, Any]:
    """Retry failed or legacy extraction from the verified preserved original.

    On a failed extraction the previous search index is kept intact. Reindexing
    never runs code from the document and never modifies the original bytes.
    """
    from campanario.utilities.service import now
    with util.connect() as db:
        doc = db.execute('SELECT * FROM documents WHERE id=?', (uid,)).fetchone()
    if doc is None:
        raise ValueError('Documento não encontrado')
    path = util.docs / (uid + Path(doc['name']).suffix.lower())
    if not path.is_file() or not path.resolve().is_relative_to(util.docs.resolve()):
        raise ValueError('Original preservado não encontrado; não foi possível reindexar')
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != doc['sha256']:
        raise ValueError('Hash do original divergente; reindexação bloqueada')
    extraction = extract_document(path, ocr=True)
    entries = _sections(extraction.pages)
    if not entries:
        raise ValueError('Nenhum texto extraído; confira OCR/dependências e o arquivo original')
    pages_text = '\n'.join(page['text'] for page in extraction.pages)
    with util.connect() as db:
        with db:
            try:
                db.execute('DELETE FROM document_fts WHERE document_id=?', (uid,))
            except sqlite3.OperationalError:
                pass
            db.execute('DELETE FROM document_sections WHERE document_id=?', (uid,))
            db.execute('UPDATE documents SET content=?, pages=? WHERE id=?',
                       (pages_text, json.dumps(extraction.pages, ensure_ascii=False), uid))
            db.execute('INSERT OR REPLACE INTO document_details VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (uid, path.stat().st_size,
                        mimetypes.guess_type(doc['name'])[0] or 'application/octet-stream',
                        extraction.method, extraction.state, 'concluída',
                        json.dumps(extraction.warnings, ensure_ascii=False),
                        extraction.markdown, VERSION, now()))
            for ordinal, section in enumerate(entries):
                evidence_id = f'library:{uid}:{ordinal}'
                rowid = db.execute('INSERT INTO document_sections VALUES (?,?,?,?,?,?,?)',
                                   (uid, ordinal, section['page'], section['heading'],
                                    section['text'], section['method'], evidence_id)).lastrowid
                try:
                    db.execute('INSERT INTO document_fts '
                               '(rowid,document_id,heading,body,evidence_id) VALUES (?,?,?,?,?)',
                               (rowid, uid, section['heading'], section['text'], evidence_id))
                except sqlite3.OperationalError:
                    pass
    return {'reindexed': True, 'id': uid, 'indexed_sections': len(entries),
            'state': extraction.state, 'warnings': extraction.warnings}


def _doc_row(db: sqlite3.Connection, uid: str):
    return db.execute('SELECT d.*, x.byte_size, x.mime, x.method, x.state, x.stage, '
                      'x.errors, x.markdown, x.processor_version, x.updated '
                      'FROM documents d LEFT JOIN document_details x ON d.id=x.document_id '
                      'WHERE d.id=?', (uid,)).fetchone()


def document_info(util: Any, uid: str, *, markdown: bool = False) -> dict[str, Any]:
    with util.connect() as db:
        row = _doc_row(db, uid)
    if not row:
        raise ValueError('Documento não encontrado')
    data = {key: row[key] for key in ('id', 'name', 'category', 'sha256', 'created')}
    data.update({'bytes': row['byte_size'], 'type': row['mime'],
                 'method': row['method'] or 'legacy', 'state': row['state'] or 'available',
                 'stage': row['stage'] or 'legado',
                 'errors': json.loads(row['errors']) if row['errors'] else [],
                 'version': row['processor_version'] or 'legacy',
                 'source': 'imported_document'})
    if markdown:
        data['markdown'] = row['markdown'] if row['markdown'] is not None else row['content']
    return data


def retrieve(util: Any, query: str, *, document_id: str = '',
             document_hint: str = '', limit: int = 6) -> dict[str, Any]:
    """Actual local reading; return candidates as excerpts, not generated answers."""
    query = query.strip()[:500]
    if not query:
        raise ValueError('Consulta vazia')
    limit = max(1, min(20, int(limit)))
    words = _tokens(query) - {'database', 'documento', 'documentos', 'arquivo', 'arquivos',
                               'biblioteca', 'pdf', 'livro', 'segundo', 'consulte', 'procure',
                               'busque', 'enviou', 'enviei', 'enviado', 'encontrei', 'informacoes',
                               'ganha', 'ganham', 'qual', 'quais', 'sobre'}
    # Numeric levels and percentages are decisive, never silently relaxed.
    numbers = set(re.findall(r'\b\d+(?:[.,]\d+)?\b', query))
    with util.connect() as db:
        fts_ids = None
        try:
            fts_words = list(sorted(words))[:18]
            if fts_words:
                literal = ' OR '.join('"' + word.replace('"', '') + '"' for word in fts_words)
                fts_ids = {row[0] for row in db.execute(
                    'SELECT rowid FROM document_fts WHERE document_fts MATCH ? '
                    'ORDER BY bm25(document_fts), rowid LIMIT 10000', (literal,))}
        except sqlite3.OperationalError:
            fts_ids = None
        docs = db.execute('SELECT id,name,sha256,pages FROM documents ORDER BY created DESC LIMIT 300').fetchall()
        candidates: list[dict[str, Any]] = []
        seen_docs = []
        for doc in docs:
            if document_id and doc['id'] != document_id:
                continue
            name = _fold(doc['name'])
            hint_terms = _tokens(document_hint)
            if hint_terms and not hint_terms.issubset(_tokens(name)):
                continue
            seen_docs.append(doc['name'])
            try:
                sections = db.execute('SELECT rowid,* FROM document_sections WHERE document_id=? ORDER BY ordinal LIMIT 20000',
                                      (doc['id'],)).fetchall()
            except sqlite3.OperationalError:  # legacy read-only databases lack this additive table
                sections = []
            if sections:
                blocks = [dict(s) for s in sections
                          if fts_ids is None or not fts_ids or s['rowid'] in fts_ids]
            else:
                # Old documents remain searchable with no migration/reimport.
                try:
                    blocks = [dict(p, heading='', body=p.get('text', ''),
                                   evidence_id=f'library:{doc["id"]}:page:{i}',
                                   method='legacy')
                              for i, p in enumerate(json.loads(doc['pages']))]
                except (ValueError, TypeError):
                    blocks = []
            for s in blocks:
                text = s['body'][:2400]
                found = _tokens(text)
                matches = words & found
                if numbers and not numbers.issubset(set(re.findall(r'\b\d+(?:[.,]\d+)?\b', text))):
                    continue
                if len(matches) < min(2, len(words)) or not matches:
                    continue
                # Avoid presenting topical matches as an answer, even if ranked.
                coverage = len(matches) / max(1, len(words))
                if coverage < 0.42:
                    continue
                score = round(coverage * 10 + len(matches) +
                              (3 if document_hint and hint_terms.issubset(_tokens(name)) else 0), 4)
                candidates.append({'evidence_id': s['evidence_id'], 'document_id': doc['id'],
                                   'document': doc['name'], 'sha256': doc['sha256'],
                                   'page': s.get('page'), 'section': s.get('heading') or None,
                                   'excerpt': text[:1600], 'method': 'fts5+lexical_sections' if fts_ids else 'lexical_sections',
                                   'extraction_method': s.get('method'), 'score': score})
    candidates.sort(key=lambda x: (-x['score'], x['document'], str(x['page']), x['evidence_id']))
    return {'query': query, 'searched_documents': len(seen_docs),
            'documents': seen_docs[:30], 'evidence': candidates[:limit],
            'status': 'found' if candidates else 'not_found',
            'note': 'Trechos literais; pertinência e veracidade externa não são garantidas.'}


def compare(util: Any, first: str, second: str) -> dict[str, Any]:
    """Deterministic comparison; no unsupported model-invented conclusions."""
    import difflib
    with util.connect() as db:
        a, b = _doc_row(db, first), _doc_row(db, second)
    if a is None or b is None:
        raise ValueError('Um ou mais documentos não foram encontrados')
    left = (a['markdown'] or a['content']).splitlines()
    right = (b['markdown'] or b['content']).splitlines()
    differences = list(difflib.unified_diff(left[:5000], right[:5000],
                                            fromfile=a['name'], tofile=b['name'], lineterm=''))
    return {'document_a': a['name'], 'document_b': b['name'],
            'identical_content': left == right, 'diff': '\n'.join(differences[:400]),
            'truncated': len(differences) > 400 or len(left) > 5000 or len(right) > 5000,
            'method': 'difflib_line_comparison'}
