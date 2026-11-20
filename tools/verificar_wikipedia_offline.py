"""Offline Kiwix diagnostics (no writes, downloads, internet or DB access)."""
from __future__ import annotations

from campanario.chat.zim_wikipedia import OfflineWikipediaZim
from campanario.config import Settings


def main() -> int:
    settings = Settings()
    directory = settings.zim_dir or (settings.data_dir.parent / 'zim')
    print('CAMPANARIO - WIKIPEDIA OFFLINE')
    print('Ativado em .env:', settings.zim_enabled)
    print('Diretorio ZIM:', directory)
    print('Servidor:', settings.zim_base_url)
    try:
        reader = OfflineWikipediaZim(
            directory, base_url=settings.zim_base_url,
            book_name=settings.zim_book_name,
            timeout_seconds=settings.zim_timeout_seconds,
        )
        result = reader.search('Quem foi Ada Lovelace?', subject='Ada Lovelace')
    except ValueError as exc:
        print('Configuracao invalida:', exc)
        return 2
    print('Status:', reader.last_status)
    if result is None:
        print('Ainda nao foi possivel obter evidencias do artigo Ada Lovelace.')
        print('Confira arquivo wikipedia_pt*.zim, kiwix-serve e o arquivo .env.')
        return 1
    print('Artigo confirmado:', result.title)
    print('Fonte:', result.locator)
    print('Trecho literal:', result.excerpt[:350])
    if not settings.zim_enabled:
        print('ATENCAO: a integracao do CHAT ainda esta desligada no .env!')
        return 1
    print('OK: leitura local demonstrada. Teste na interface do Campanario.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
