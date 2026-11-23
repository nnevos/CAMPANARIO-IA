"""Local console for owner-authorized case analysis. No HTTP endpoint or LLM access."""
from __future__ import annotations

import os
from pathlib import Path

from campanario.brains.casework import CaseWorkspace, CaseError


def open_workspace() -> CaseWorkspace:
    # Explicit configuration, with three-repository validation in CaseWorkspace.
    configured = os.environ.get('CAMPANARIO_DATA_DIR')
    if not configured:
        raise CaseError('CAMPANARIO_DATA_DIR nao configurado; nao gravar no repositorio IA')
    return CaseWorkspace(Path(configured))


def main() -> int:
    try:
        workspace = open_workspace()
    except (CaseError, OSError) as exc:
        print('Nao foi possivel iniciar o gerenciador de casos:', exc)
        return 2
    case_id = ''
    print('CAMPANARIO — Central de casos (local, offline, sem LLM)')
    while True:
        print('\n1 Novo caso | 2 Abrir caso | 3 Importar evidencia | 4 Registrar evento | '
              '5 Registrar hipotese | 6 Conferir hashes | 7 Exportar dossie | 8 Propor eventos CSV/JSON | 0 Sair')
        try:
            choice = input('Opcao: ').strip()
            if choice == '0':
                return 0
            if choice == '1':
                case_id = workspace.create(input('Titulo: '), input('Objetivo: '),
                                            input('Nome do responsavel pela autorizacao: '))
                print('Caso criado:', case_id)
            elif choice == '2':
                proposed = input('ID do caso (32 caracteres): ').strip()
                data = workspace.read(proposed)
                case_id = proposed
                print('Aberto:', data['title'], '| evidencias:', len(data['evidence']))
            elif not case_id:
                print('Crie ou abra um caso primeiro.')
            elif choice == '3':
                item = workspace.add_evidence(case_id, Path(input('Caminho completo do arquivo: ').strip('"')),
                                              input('Origem declarada do arquivo: '),
                                              input('Quem forneceu: '))
                print('Importado:', item['id'], 'SHA-256:', item['sha256'])
            elif choice == '4':
                event = workspace.add_event(case_id, input('Data ISO 8601 com fuso (ex.: 2026-11-23T18:42:00-03:00): '),
                     input('Descricao factual observada (nao conclua causalidade): '),
                     [x.strip() for x in input('IDs das fontes separados por virgula: ').split(',')],
                     input('Classificacao reported/documented/hypothesis: ').strip())
                print('Evento registrado:', event['id'])
            elif choice == '5':
                item = workspace.add_hypothesis(case_id, input('Hipotese (nao conclusao): '),
                          [x.strip() for x in input('Fontes a favor separadas por virgula (ou vazio): ').split(',') if x.strip()],
                          [x.strip() for x in input('Fontes contra separadas por virgula (ou vazio): ').split(',') if x.strip()],
                          input('Proximo teste/verificacao: '))
                print('Hipotese registrada:', item['id'])
            elif choice == '6':
                print(workspace.verify(case_id))
            elif choice == '8':
                eid = input('ID da evidencia CSV/JSON: ').strip()
                candidates = workspace.propose_log_events(case_id, eid)
                for event in candidates:
                    print('Registro', event['row'], event['date_time'], event['description'], '(NAO CONFIRMADO)')
                    if input('Registrar este evento como relato da fonte? [s/N]: ').strip().lower() == 's':
                        workspace.add_event(case_id, event['date_time'],
                                            f"Registro {event['row']}: {event['description']}",
                                            [eid], 'reported')
            elif choice == '7':
                doc = workspace.dossier(case_id)
                # Place export with case metadata in DATABASE only, never in IA.
                dest = workspace._dir(case_id) / 'DOSSIER.md'
                dest.write_text(doc, encoding='utf-8')
                print('Dossie salvo:', dest)
            else:
                print('Opcao invalida')
        except (CaseError, OSError, ValueError) as exc:
            print('Operacao cancelada:', exc)
        except (EOFError, KeyboardInterrupt):
            return 0


if __name__ == '__main__':
    raise SystemExit(main())
