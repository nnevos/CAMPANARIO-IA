"""Bounded, deterministic, offline table calculations over imported originals.

No dynamic Python code, SQL, spreadsheet formulas or shell commands from users.
Every output states the input file and calculation parameters.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

MAX_ROWS = 100_000
MAX_COLUMNS = 100


def _load(util, document_id: str, sheet: str | None = None):
    from campanario.utilities.document_v8 import DATA_TYPES
    import pandas as pd
    with util.connect() as db:
        row = db.execute('SELECT id,name,sha256 FROM documents WHERE id=?',
                         (document_id,)).fetchone()
    if row is None:
        raise ValueError('Documento não encontrado')
    ext = Path(row['name']).suffix.lower()
    if ext not in DATA_TYPES:
        raise ValueError('A análise exige CSV, XLSX ou JSON importado')
    original = util.docs / (row['id'] + ext)
    if not original.is_file():
        raise FileNotFoundError('Original da planilha não está disponível')
    if original.stat().st_size > 100_000_000:
        raise ValueError('Arquivo grande demais para análise interativa (100 MB)')
    if ext == '.csv':
        # Read-only, no execution of CSV cells beginning with '='.
        try:
            df = pd.read_csv(original, sep=None, engine='python', nrows=MAX_ROWS + 1)
        except (UnicodeDecodeError, ValueError):
            df = pd.read_csv(original, sep=None, engine='python', nrows=MAX_ROWS + 1,
                             encoding='latin-1')
    elif ext == '.xlsx':
        df = pd.read_excel(original, sheet_name=sheet if sheet else 0,
                           nrows=MAX_ROWS + 1, engine='openpyxl')
    else:
        data = json.loads(original.read_text(encoding='utf-8-sig'))
        if not isinstance(data, (list, dict)):
            raise ValueError('JSON precisa conter uma lista ou objeto tabular')
        df = pd.DataFrame(data)
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError('Tabela excede 100.000 linhas ou 100 colunas')
    df.columns = [str(name) for name in df.columns]
    if len(set(df.columns)) != len(df.columns):
        raise ValueError('Colunas duplicadas; corrija a tabela antes da análise')
    return df, {'document_id': row['id'], 'filename': row['name'], 'sha256': row['sha256'],
                'sheet': sheet}


def _json_clean(value: Any) -> Any:
    import pandas as pd
    if isinstance(value, (int, float)):
        return value if not isinstance(value, float) or math.isfinite(value) else None
    if pd.isna(value):
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if hasattr(value, 'item'):
        return _json_clean(value.item())
    return str(value) if not isinstance(value, (str, bool)) else value


def _rows(frame, limit=50):
    return [{str(k): _json_clean(v) for k, v in row.items()}
            for row in frame.head(limit).to_dict(orient='records')]


def inspect(util, args: dict[str, Any]) -> dict[str, Any]:
    uid = str(args.get('document_id') or '')
    df, source = _load(util, uid, args.get('sheet'))
    return {'source': source, 'rows': len(df), 'columns': len(df.columns),
            'schema': [{'name': c, 'type': str(df[c].dtype),
                        'missing': int(df[c].isna().sum()),
                        'unique': int(df[c].nunique(dropna=True))}
                       for c in df.columns],
            'sample': _rows(df, 8), 'sample_is_partial': len(df) > 8}


def analyze(util, args: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd
    uid = str(args.get('document_id') or '')
    df, source = _load(util, uid, args.get('sheet'))
    operation = str(args.get('operation') or 'describe')
    column = args.get('column')
    group = args.get('group_by')
    period = args.get('period_column')
    if column is not None and column not in df:
        raise ValueError('Coluna numérica não existe')
    if group is not None and group not in df:
        raise ValueError('Coluna de agrupamento não existe')
    if period is not None and period not in df:
        raise ValueError('Coluna de período não existe')
    if operation == 'sum':
        # Decimal arithmetic over the imported numeric cells. Never let a model
        # guess which column represents revenue or sum missing values silently.
        from decimal import Decimal, InvalidOperation
        if (not isinstance(column, str) or not column
                or not pd.api.types.is_numeric_dtype(df[column])):
            raise ValueError('Soma exige uma coluna numérica identificada')
        if df.empty or df[column].isna().any():
            return {'source': source, 'operation': operation, 'column': column,
                    'status': 'insufficient_data', 'result': [],
                    'limitation': 'Valores ausentes ou nenhuma linha; não calcular soma parcial'}
        try:
            values = [Decimal(str(v)) for v in df[column]]
            if not all(v.is_finite() for v in values):
                raise ValueError('Valor não finito na coluna numérica')
            total = sum(values, Decimal('0'))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError('Valores inválidos para soma decimal') from exc
        return {'source': source, 'operation': operation, 'column': column,
                'rows_analyzed': len(df), 'result': [{'sum': (format(total, '.2f') if any(
                    keyword in column.casefold() for keyword in
                    ('receita', 'faturamento', 'valor', 'revenue')
                ) else format(total, 'f'))}],
                'status': 'computed'}
    if operation == 'describe':
        nums = df.select_dtypes(include='number')
        if nums.empty:
            return {'source': source, 'operation': operation, 'columns': [],
                    'result': [], 'status': 'insufficient_data'}
        result = nums.describe().T.reset_index().rename(columns={'index': 'column'})
        return {'source': source, 'operation': operation, 'rows_analyzed': len(df),
                'result': _rows(result), 'status': 'computed'}
    if operation == 'missing':
        return {'source': source, 'operation': operation, 'rows_analyzed': len(df),
                'result': [{'column': key, 'missing': int(value)}
                           for key, value in df.isna().sum().items()],
                'status': 'computed'}
    if operation == 'growth':
        # Percentage growth needs a comparable product and two actual months.
        if (not isinstance(column, str) or not pd.api.types.is_numeric_dtype(df[column])
                or not isinstance(group, str) or not isinstance(period, str)):
            raise ValueError('Crescimento exige column numérica, group_by e period_column')
        if df.empty:
            return {'source': source, 'operation': operation,
                    'status': 'insufficient_data', 'result': []}
        parsed = pd.to_datetime(df[period], errors='coerce')
        if parsed.isna().any():
            raise ValueError('Período contém valores ausentes ou datas não reconhecidas')
        count = int(args.get('periods', 6))
        if not 2 <= count <= 36:
            raise ValueError('Número de períodos deve estar entre 2 e 36')
        clean = df[[group, period, column]].copy()
        clean['_period'] = parsed.dt.to_period('M').astype(str)
        values = sorted(clean['_period'].unique().tolist())[-count:]
        if len(values) < 2:
            return {'source': source, 'operation': operation,
                    'status': 'insufficient_data', 'result': [],
                    'limitation': 'São necessários pelo menos dois meses de dados'}
        grouped = clean.groupby(['_period', group], dropna=False)[column].sum()
        first, last = values[0], values[-1]
        products = sorted(clean[group].dropna().astype(str).unique().tolist())
        result = []
        excluded = []
        for product in products:
            # Do not turn an absent month into a zero sale (that invents data).
            if (first, product) not in grouped.index or (last, product) not in grouped.index:
                excluded.append(product)
                continue
            before, after = float(grouped.loc[(first, product)]), float(grouped.loc[(last, product)])
            change = after - before
            pct = (100.0 * change / before) if before != 0 else None
            result.append({'product': product, 'first_value': before,
                           'last_value': after, 'change_absolute': change,
                           'change_percent': pct})
        result.sort(key=lambda r: (r['change_percent'] is None,
                                  -(r['change_percent'] or 0), r['product']))
        return {'source': source, 'operation': operation, 'periods': values,
                'comparison': {'first': first, 'last': last},
                'rows_analyzed': len(df), 'result': result[:100],
                'excluded_missing_endpoint': excluded[:100],
                'result_truncated': len(result) > 100,
                'status': 'computed' if result else 'insufficient_data',
                'limitation': 'Produtos sem registro no início e fim não são comparados. '
                              'Valores iniciais zero não geram percentual.'}
    if operation in ('group', 'trend'):
        if not isinstance(column, str) or not column or not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError('Informe uma coluna numérica para agregação')
        key = period if operation == 'trend' else group
        if not isinstance(key, str) or not key:
            raise ValueError('Informe period_column (trend) ou group_by (group)')
        if df.empty:
            return {'source': source, 'operation': operation, 'result': [],
                    'status': 'insufficient_data'}
        aggregate = str(args.get('aggregation') or 'sum')
        if aggregate not in {'sum', 'mean', 'count', 'min', 'max'}:
            raise ValueError('Agregação não suportada')
        # Group dates as supplied. No arbitrary date parsing or guessed formats.
        result = df.groupby(key, dropna=False)[column].agg(aggregate).reset_index()
        if operation == 'group':
            result = result.sort_values(column, ascending=False)
        else:
            result = result.sort_values(key)
        result = result.head(100)
        if operation == 'trend':
            result['change_absolute'] = result[column].diff()
            result['change_percent'] = result[column].pct_change(fill_method=None) * 100
            result.loc[~result['change_percent'].map(lambda x: math.isfinite(x) if pd.notna(x) else False), 'change_percent'] = float('nan')
        return {'source': source, 'operation': operation, 'aggregation': aggregate,
                'rows_analyzed': len(df), 'result': _rows(result, 100),
                'status': 'computed', 'result_truncated': len(result) >= 100}
    if operation == 'filter':
        # Only fixed comparisons, never pandas eval/query or executable expressions.
        if column not in df:
            raise ValueError('Informe uma coluna de filtro')
        value = args.get('value')
        op = str(args.get('operator', 'eq'))
        if op not in {'eq', 'ne', 'gt', 'gte', 'lt', 'lte'}:
            raise ValueError('Operador desconhecido')
        if op in {'gt', 'gte', 'lt', 'lte'}:
            series = pd.to_numeric(df[column], errors='coerce')
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError('Filtro numérico requer um número') from None
        else:
            series = df[column].astype('string')
            value = str(value)
        mask = {'eq': lambda: series == value, 'ne': lambda: series != value,
                'gt': lambda: series > value, 'gte': lambda: series >= value,
                'lt': lambda: series < value, 'lte': lambda: series <= value}[op]()
        result = df.loc[mask.fillna(False)]
        return {'source': source, 'operation': operation, 'rows_matched': len(result),
                'result': _rows(result), 'result_truncated': len(result) > 50,
                'status': 'computed'}
    raise ValueError('Operação desconhecida (sum, describe, missing, group, trend, growth, filter)')
