"""Offline read-and-calculate natural-language requests, independent of LLMs.

Only a narrow, explicit set of intents can be automated. Unsupported analytical
questions ask for structured column selection rather than making up numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from campanario.chat.local_library import _fold


@dataclass(frozen=True, slots=True)
class DataAnalysisResult:
    subject: str
    status: str
    verified_answer: str
    source_name: str = ''
    source_id: str = ''
    digest: str = ''
    operation: str = ''
    evidence_excerpt: str = ''
    searches: int = 1
    read_count: int = 0
    requires_abstention: bool = False


def is_data_request(question: str) -> bool:
    text = _fold(question)
    command = bool(re.search(r'\b(?:analise|analisar|calcule|calcular|compare|comparar|'
                             r'crescimento|estatisticas|agrupamento|tendencias|tendencia|faturamento|soma|total)\b', text))
    context = bool(re.search(r'\b(?:planilha|planilhas|csv|xlsx|excel|vendas|dados|'
                             r'receitas|tabela|tabelas|produtos|faturamento)\b', text))
    return command and context


def _pick(labels: list[str], candidates: tuple[str, ...]) -> str:
    choices = [name for name in labels if _fold(name).replace(' ', '_') in candidates]
    return choices[0] if len(choices) == 1 else ''


def run_data_question(database: Path, question: str) -> DataAnalysisResult:
    """Only actual imported originals. Never upload a file or evaluate code."""
    from campanario.utilities.data_v8 import inspect, analyze
    from campanario.utilities.document_v8 import DATA_TYPES
    if not Path(database).is_file():
        return DataAnalysisResult(question, 'insufficient', 'A biblioteca local não está disponível.')

    class Reader:
        docs = Path(database).parent / 'documentos'
        def connect(self):
            db = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro',
                                 uri=True, timeout=2.0)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            return db

    reader = Reader()
    try:
        with reader.connect() as db:
            files = [dict(row) for row in db.execute(
                'SELECT id,name,sha256 FROM documents ORDER BY created DESC LIMIT 300')
                if Path(row['name']).suffix.lower() in DATA_TYPES]
    except (sqlite3.Error, OSError):
        return DataAnalysisResult(question, 'insufficient',
                                  'Não consegui consultar o catálogo de planilhas.')
    if not files:
        return DataAnalysisResult(question, 'insufficient',
                                  'Não há planilhas CSV, XLSX ou JSON importadas para analisar.')
    terms = _fold(question)
    exact_named = [f for f in files if _fold(f['name']) in terms]
    named = exact_named or [f for f in files if _fold(Path(f['name']).stem) in terms]
    if len(named) == 1:
        source = named[0]
    elif len(files) == 1:
        source = files[0]
    else:
        names = ', '.join(f['name'] for f in files[:8])
        return DataAnalysisResult(question, 'insufficient',
                                  'Encontrei múltiplas planilhas: ' + names +
                                  '. Indique o nome do arquivo para evitar escolher a fonte errada.')
    uid = source['id']
    try:
        schema = inspect(reader, {'document_id': uid})
        cols = [item['name'] for item in schema['schema']]
        numeric = [item['name'] for item in schema['schema']
                   if item['type'].startswith(('int', 'float'))]
        product = _pick(cols, ('produto', 'produtos', 'product', 'item', 'categoria'))
        month = _pick(cols, ('mes', 'data', 'periodo', 'competencia', 'month', 'date'))
        value = _pick(numeric, ('vendas', 'valor', 'receita', 'faturamento',
                                'total', 'quantidade', 'sales', 'revenue'))
        if re.search(r'\b(?:crescimento|cresceram|cresceu)\b', terms):
            operation = 'growth'
            if not product or not month or not value:
                return DataAnalysisResult(question, 'insufficient',
                    f'A planilha {source["name"]} foi inspecionada, mas não foi possível identificar '
                    'sem ambiguidade produto, mês e valor. Colunas disponíveis: ' + ', '.join(cols) +
                    '. Configure as colunas em Ferramentas > Análises.')
            params = {'document_id': uid, 'operation': 'growth', 'group_by': product,
                      'period_column': month, 'column': value, 'periods': 6}
        elif re.search(r'\b(?:faturamento\s+total|receita\s+total|total\s+(?:de\s+)?(?:faturamento|vendas|receita)|soma\s+(?:de\s+)?(?:vendas|receita|faturamento))\b', terms):
            operation = 'sum'
            if not value:
                return DataAnalysisResult(question, 'insufficient',
                    f'A planilha {source["name"]} foi inspecionada, mas não foi possível '
                    'identificar uma coluna numérica de faturamento com segurança. '
                    'Colunas disponíveis: ' + ', '.join(cols))
            params = {'document_id': uid, 'operation': operation, 'column': value}
        elif re.search(r'\b(?:ausentes|faltantes|incompletos)\b', terms):
            operation = 'missing'
            params = {'document_id': uid, 'operation': operation}
        else:
            operation = 'describe'
            params = {'document_id': uid, 'operation': operation}
        outcome = analyze(reader, params)
    except (ImportError, ValueError, OSError, sqlite3.Error) as exc:
        return DataAnalysisResult(question, 'insufficient',
                                  f'Não consegui calcular a análise de {source["name"]}: '
                                  f'{type(exc).__name__}: {str(exc)[:170]}')
    if outcome['status'] != 'computed':
        return DataAnalysisResult(question, 'insufficient',
                                  f'A planilha {source["name"]} não contém dados suficientes '
                                  'para a operação solicitada.')
    if operation == 'growth':
        start, end = outcome['comparison']['first'], outcome['comparison']['last']
        rows = outcome['result']
        lines = [f'Análise calculada no arquivo {source["name"]} entre {start} e {end} '
                 f'(meses distintos presentes: {len(outcome["periods"])}).']
        for row in rows[:8]:
            pct = ('percentual indefinido (início igual a zero)' if row['change_percent'] is None
                   else f'{row["change_percent"]:.2f}%')
            lines.append(f'{row["product"]}: {row["first_value"]:g} → '
                         f'{row["last_value"]:g}; crescimento {pct}; '
                         f'variação absoluta {row["change_absolute"]:g}.')
        if outcome['excluded_missing_endpoint']:
            lines.append('Não comparáveis por ausência em uma das pontas: ' +
                         ', '.join(outcome['excluded_missing_endpoint'][:10]) + '.')
        lines.append('Método: soma por produto/mês; percentual = '
                     '(último - primeiro) / primeiro × 100, quando primeiro ≠ 0.')
    elif operation == 'sum':
        lines = [f'Soma calculada no arquivo {source["name"]}, coluna {value}: '
                 f'{outcome["result"][0]["sum"]} '
                 f'(linhas analisadas: {outcome["rows_analyzed"]}).']
        lines.append('Unidade monetária não confirmada pela planilha; valor numérico bruto.')
    elif operation == 'missing':
        lines = ['Valores ausentes calculados no arquivo ' + source['name'] + ':']
        lines.extend(f'{r["column"]}: {r["missing"]}' for r in outcome['result'][:15])
    else:
        lines = ['Estatísticas calculadas no arquivo ' + source['name'] + ':']
        for row in outcome['result'][:8]:
            lines.append(f'{row["column"]}: média={row.get("mean")}, '
                         f'mín={row.get("min")}, máx={row.get("max")}, '
                         f'contagem={row.get("count")}')
    lines.append('Fonte: ' + source['name'] + ' (original importado; SHA-256: ' +
                 source['sha256'][:16] + '…).')
    answer = '\n'.join(lines)
    return DataAnalysisResult(question, 'grounded', answer, source['name'], uid,
                              source['sha256'], operation, answer, read_count=1)
