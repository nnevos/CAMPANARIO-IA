"""Double-click diagnostic: Cellbit from an offline Kiwix article, read-only."""
from __future__ import annotations

from campanario.chat.zim_wikipedia import OfflineWikipediaZim
from campanario.config import Settings


def main() -> int:
    settings = Settings()
    directory = settings.zim_dir or (settings.data_dir.parent / 'zim')
    print('CAMPANARIO - TESTE OFFLINE: CELLBIT (sem internet)')
    print('Wikipedia habilitada:', settings.zim_enabled)
    print('Pasta dos ZIMs:', directory)
    print('Servidor local:', settings.zim_base_url)
    if not settings.zim_enabled:
        print('Ative CAMPANARIO_ZIM_ENABLED=true no .env; nao apague outras configuracoes.')
        return 2
    try:
        source = OfflineWikipediaZim(
            directory,
            base_url=settings.zim_base_url,
            book_name=settings.zim_book_name,
            timeout_seconds=settings.zim_timeout_seconds,
        )
        result = source.search('todd quem é cellbit?', subject='Cellbit')
    except ValueError as exc:
        print('Configuracao de Kiwix invalida:', exc)
        return 2
    print('Status:', source.last_status)
    if result is None:
        print('Nao foi encontrado um artigo exato com evidencia suficiente para Cellbit.')
        print('Se o status for no_unique_exact_title, confira Cellbit na busca do Kiwix em http://127.0.0.1:8181')
        print('Nenhum dado foi escrito, e a pesquisa na internet nao foi usada.')
        return 1
    print('Artigo:', result.title)
    print('Fonte:', result.locator)
    print('Trecho:', result.excerpt[:450])
    print('OK: fonte local encontrada. Reinicie o Campanario e pergunte: todd quem e cellbit?')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
