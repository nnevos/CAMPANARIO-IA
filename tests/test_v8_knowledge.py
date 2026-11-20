"""V8 integration tests: real fixture files are ingested; no canned model answers."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from campanario.chat.document_intent import document_request, search_document
from campanario.chat.local_library import ReadOnlyLocalLibrary
from campanario.chat.service import ChatService
from campanario.chat.context import RecentMessagesContextManager
from campanario.model.protocol import ModelChunk
from campanario.utilities.service import UtilityService
from test_chat_service import InMemoryMessages, InMemorySessions


@pytest.fixture
def util(tmp_path):
    return UtilityService(tmp_path / 'utility')


def import_text(util, name, content):
    path = util.roots[0] / name
    path.write_text(content, encoding='utf8')
    result = util.run('library.import', {'path': str(path), 'confirm': True})
    assert result['status'] == 'success', result
    return result['result']


def test_markdown_copy_metadata_sections_retrieval_and_restart(util):
    content = '# Regras de Exemplo\n\n## Ocultista em 20% de NEX\n\nO Ocultista recebe a Marca Simulada Alfa.\n'
    doc = import_text(util, 'Ordem Paranormal - Exemplo.md', content)
    assert doc['state'] == 'available'
    uid = doc['id']
    info = util.run('library.document', {'document_id': uid, 'include_markdown': True})['result']
    assert info['markdown'] == content
    assert info['sha256'] == hashlib.sha256(content.encode()).hexdigest()
    assert info['version'].startswith('8.')
    assert (util.docs / (uid + '.md')).read_text() == content
    result = util.run('library.retrieve', {'query': 'O que Ocultista ganha em 20% de NEX?',
                                           'document_hint': 'Ordem Paranormal'})['result']
    assert result['status'] == 'found' and result['evidence']
    assert 'Marca Simulada Alfa' in result['evidence'][0]['excerpt']
    assert result['evidence'][0]['section'] == 'Ocultista em 20% de NEX'
    assert result['evidence'][0]['evidence_id'].startswith('library:')
    again = UtilityService(util.base)
    assert again.run('library.document', {'document_id': uid})['result']['state'] == 'available'
    assert again.run('library.retrieve', {'query': 'Ocultista 20% NEX'})['result']['evidence']
    assert again.run('library.import', {'path': str(util.roots[0]/'Ordem Paranormal - Exemplo.md'),
                                        'confirm': True})['result']['duplicate_id'] == uid


def test_existing_documents_schema_remains_compatible(util):
    with util.connect() as db:
        db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)',
                   ('old', 'Manual Legado.txt', 'geral', 'digest-legado',
                    'A sala do Manual Legado é a sala 36.',
                    json.dumps([{'page': 7, 'text': 'A sala do Manual Legado é a sala 36.'}]),
                    'legado.txt', '2025-01-01'))
    info = util.run('library.document', {'document_id': 'old', 'include_markdown': True})['result']
    assert info['version'] == 'legacy' and info['markdown']
    old = ReadOnlyLocalLibrary(util.db).search('Onde fica sala do Manual Legado?')
    assert old is not None and old.quote.page == 7
    assert util.run('library.retrieve', {'query': 'Qual sala do Manual Legado?'})['result']['evidence']


def test_source_miss_and_missing_document_never_claims_lookup(util):
    import_text(util, 'outro.txt', 'Um manual sem qualquer progressão do personagem.')
    result = util.run('library.retrieve', {
        'query': 'O que Ocultista ganha em 20% de NEX?', 'document_hint': 'Ordem Paranormal',
    })['result']
    assert result['status'] == 'not_found' and not result['evidence']
    miss = util.run('library.document', {'document_id': 'missing'})
    assert miss['status'] == 'failed'


def test_document_compare_no_auto_resolution(util):
    a = import_text(util, 'um.md', '# Procedimento\n\nO selo é azul.\n')
    b = import_text(util, 'dois.md', '# Procedimento\n\nO selo é vermelho.\n')
    diff = util.run('library.compare', {'document_a': a['id'], 'document_b': b['id']})['result']
    assert not diff['identical_content'] and '-O selo é azul.' in diff['diff']
    assert '+O selo é vermelho.' in diff['diff']


def test_csv_xlsx_and_json_deterministic_analysis(util):
    pandas = pytest.importorskip('pandas')
    openpyxl = pytest.importorskip('openpyxl')
    csv_doc = import_text(util, 'vendas.csv',
                          'mes,produto,valor\n2026-01,Livro,10\n2026-02,Livro,20\n2026-02,Jogo,35\n')
    res = util.run('data.inspect', {'document_id': csv_doc['id']})
    assert res['status'] == 'success' and res['result']['rows'] == 3
    group = util.run('data.analyze', {'document_id': csv_doc['id'], 'operation': 'group',
                                     'group_by': 'produto', 'column': 'valor'})['result']
    assert group['result'][0]['valor'] == 35
    trend = util.run('data.analyze', {'document_id': csv_doc['id'], 'operation': 'trend',
                                     'period_column': 'mes', 'column': 'valor'})['result']
    assert trend['result'][1]['valor'] == 55
    assert trend['result'][1]['change_absolute'] == 45
    xls = util.roots[0] / 'vendas.xlsx'
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Vendas'
    ws.append(['produto', 'valor']); ws.append(['Livro', 5]); ws.append(['Jogo', 7]); wb.save(xls)
    imported = util.run('library.import', {'path': str(xls), 'confirm': True})
    assert imported['status'] == 'success'
    assert util.run('data.inspect', {'document_id': imported['result']['id']})['result']['rows'] == 2
    jd = import_text(util, 'estoque.json', '[{"produto":"Caderno","valor":6}]')
    assert util.run('data.inspect', {'document_id': jd['id']})['result']['rows'] == 1
    failed = util.run('data.analyze', {'document_id': csv_doc['id'], 'operation': 'unsafe_python',
                                      'code': 'import os; os.remove("something")'})
    assert failed['status'] == 'failed'
    assert not util.run('data.inspect', {'document_id': 'not-a-document'})['status'] == 'success'


def test_docx_and_pdf_provenance(util):
    docx = pytest.importorskip('docx')
    d = docx.Document()
    d.add_heading('Regras de Personagem', 1)
    d.add_paragraph('O item da planilha de exemplo é bronze.')
    d.add_table(rows=2, cols=2)
    p = util.roots[0] / 'regras.docx'; d.save(p)
    r = util.run('library.import', {'path': str(p), 'confirm': True})
    assert r['status'] == 'success'
    info = util.run('library.document', {'document_id': r['result']['id'],
                                         'include_markdown': True})['result']
    assert '# Regras de Personagem' in info['markdown'] and 'bronze' in info['markdown']
    reportlab = pytest.importorskip('reportlab.pdfgen.canvas')
    pdf = util.roots[0] / 'impresso.pdf'
    canvas = reportlab.Canvas(str(pdf))
    canvas.drawString(40, 700, 'O Ocultista em 20% de NEX recebe Selo Ficticio Bronze.')
    canvas.showPage(); canvas.save()
    result = util.run('library.import', {'path': str(pdf), 'confirm': True})
    assert result['status'] == 'success'
    reply = util.run('library.retrieve', {'query': 'Ocultista em 20% de NEX?'})['result']
    assert any(hit['page'] == 1 and 'Selo Ficticio Bronze' in hit['excerpt']
               for hit in reply['evidence'])


def test_scanned_pdf_is_identified_without_invented_text(util):
    pypdf = pytest.importorskip('pypdf')
    pdf = util.roots[0] / 'digitalizado.pdf'
    writer = pypdf.PdfWriter(); writer.add_blank_page(width=400, height=300)
    with pdf.open('wb') as f: writer.write(f)
    result = util.run('library.import', {'path': str(pdf), 'confirm': True, 'ocr': False})
    assert result['status'] == 'success'
    assert result['result']['state'] == 'partial'
    assert not result['result']['indexed_sections']
    assert (util.docs / (result['result']['id'] + '.pdf')).is_file()


class NeverTrustModel:
    def __init__(self): self.calls = 0
    async def health(self): return True
    async def stream(self, request):
        self.calls += 1
        yield ModelChunk(text='RESPOSTA_INVENTADA')
        yield ModelChunk(text='', done=True)


@pytest.mark.asyncio
async def test_ordem_paranormal_multi_turn_only_real_fixture_source(util):
    doc = import_text(util, 'Ordem Paranormal Exemplo.md',
                      '# Progressão\n\n## Ocultista 20% NEX\n\nNo exemplo fictício, Ocultista recebe Talento Simulado T12.')
    provider = NeverTrustModel()
    chat = ChatService(InMemorySessions(), InMemoryMessages(), provider,
                       RecentMessagesContextManager(12), 'fake',
                       local_library=ReadOnlyLocalLibrary(util.db),
                       grounded_synthesis=False, low_latency_mode=True)
    session = chat.create_session()
    questions = [
        'O que Ocultista ganha em 20% de NEX em Ordem Paranormal?',
        'No Database tem um documento de Ordem Paranormal com essas informações.',
        'Então o que o Ocultista ganha em 20% de NEX?',
    ]
    answers = []
    for question in questions:
        events = [e async for e in chat.stream_turn(session.id, question)]
        answers.append(''.join(e.text for e in events if e.type == 'token'))
    assert 'Talento Simulado T12' in answers[2]
    assert 'Fonte: Ordem Paranormal Exemplo.md' in answers[2]
    assert 'RESPOSTA_INVENTADA' not in answers[2]
    assert provider.calls == 0 or 'RESPOSTA_INVENTADA' in answers[0]
    # Missing database has no document-grounded answer, even if a model exists.
    empty = UtilityService(util.base.parent / 'empty')
    chat2 = ChatService(InMemorySessions(), InMemoryMessages(), NeverTrustModel(),
                        RecentMessagesContextManager(12), 'fake',
                        local_library=ReadOnlyLocalLibrary(empty.db),
                        grounded_synthesis=False, low_latency_mode=True)
    session2 = chat2.create_session()
    for text in questions:
        events = [e async for e in chat2.stream_turn(session2.id, text)]
    answer = ''.join(e.text for e in events if e.type == 'token')
    assert 'Não encontrei' in answer and 'Fonte:' not in answer


@pytest.mark.asyncio
async def test_natural_language_growth_uses_real_csv_without_generation(util):
    # Complete endpoints in actual imported data, not a response baked into prompt.
    rows = ['mes,produto,valor']
    for month, left, right in [('2026-01', 10, 50), ('2026-02', 12, 45),
                               ('2026-03', 20, 40), ('2026-04', 25, 35),
                               ('2026-05', 31, 30), ('2026-06', 50, 20)]:
        rows.extend((f'{month},Livro,{left}', f'{month},Jogo,{right}'))
    imported = import_text(util, 'vendas.csv', '\n'.join(rows) + '\n')
    growth = util.run('data.analyze', {
        'document_id': imported['id'], 'operation': 'growth', 'column': 'valor',
        'group_by': 'produto', 'period_column': 'mes',
    })
    assert growth['status'] == 'success'
    assert growth['result']['result'][0]['product'] == 'Livro'
    assert growth['result']['result'][0]['change_percent'] == 400.0
    provider = NeverTrustModel()
    chat = ChatService(InMemorySessions(), InMemoryMessages(), provider,
                       RecentMessagesContextManager(12), 'fake',
                       local_library=ReadOnlyLocalLibrary(util.db),
                       grounded_synthesis=True, low_latency_mode=True)
    session = chat.create_session()
    events = [e async for e in chat.stream_turn(
        session.id, 'Campanário, analise as vendas dos últimos seis meses '
                    'e identifique quais produtos tiveram maior crescimento.')]
    answer = ''.join(e.text for e in events if e.type == 'token')
    assert 'Livro' in answer and '400.00%' in answer
    assert 'Fonte: vendas.csv' in answer
    # V9.1 may attempt expression via Ollama, but bogus generations are discarded;
    # computed values must still be exactly the deterministic spreadsheet result.
    assert provider.calls <= 2
    assert 'RESPOSTA_INVENTADA' not in answer


def test_growth_does_not_invent_zero_for_missing_month(util):
    imported = import_text(util, 'pontos.csv',
        'mes,produto,valor\n2026-01,Livro,3\n2026-02,Jogo,7\n2026-02,Livro,10\n')
    outcome = util.run('data.analyze', {
        'document_id': imported['id'], 'operation': 'growth',
        'group_by': 'produto', 'period_column': 'mes', 'column': 'valor',
    })['result']
    assert outcome['excluded_missing_endpoint'] == ['Jogo']
    assert all(r['product'] != 'Jogo' for r in outcome['result'])


def test_local_document_fts_index_is_persistent_if_supported(util):
    imported = import_text(util, 'exemplo.txt',
                           'O índice catalogado contém a evidência kappa no volume 9.')
    with util.connect() as db:
        try:
            size = db.execute('SELECT count(*) FROM document_fts').fetchone()[0]
        except sqlite3.OperationalError:
            pytest.skip('SQLite compiled without FTS5')
        assert size >= 1
    reopened = UtilityService(util.base)
    hits = reopened.run('library.retrieve', {'query': 'índice evidência kappa'})['result']['evidence']
    assert hits and hits[0]['document_id'] == imported['id']
    assert hits[0]['method'] == 'fts5+lexical_sections'
