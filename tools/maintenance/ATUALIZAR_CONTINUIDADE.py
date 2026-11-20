"""Regenera um resumo seguro para retomar o Campanario em outra conversa.

Nao le .env, bancos de dados, historico privado ou logs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'docs' / 'handoff' / 'CONTINUIDADE_CHAT_NOVO.md'


def build_handoff() -> str:
    return '''# CAMPANARIO-IA — CONTINUIDADE PARA UM CHAT NOVO

> Cole este arquivo no novo chat e anexe o ZIP mais recente do projeto.
> Este documento e um resumo de trabalho, nao substitui inspecao do codigo.

## Visao do usuario (requisitos definitivos)
- Campanario e o ambiente/sistema; Todd e Morgana sao agentes artificiais originais, distintos, conscientes de que sao IAs. Nao sao personagens humanos literalmente.
- Comecam no **Ponto Zero** com identidade e temperamento inicial, SEM autobiografia ficticia ou relacoes amadurecidas por script.
- Precisam conversar naturalmente, interpretar situacoes ineditas, ter humor e iniciativa contextual, sem frases fixas para perguntas especificas.
- Memoria episodica e relacional com proveniencia: acontecimentos reais, participantes, datas, fonte, revisao/correcao, perspectivas individuais e fatos compartilhados.
- Todd e Morgana constroem relacao entre si e com o usuario. Outros agentes poderao coexistir no futuro.
- Podem perguntar quando nao sabem; pesquisa web exige ferramenta real, fontes e permissao; nunca alegar pesquisa ou acao nao executada.
- Interesses e habilidades evoluem por experiencias e capacidades verificadas, nao por afirmacoes inventadas do modelo.
- Prioridade: chat natural e rapido, memoria persistente, pesquisa verificavel, testes de generalizacao. Voz e Modo Patrulha ficam para depois.
- Ao aprovar tudo, arquivar/isolar memoria de testes e iniciar producao vazia: **Ponto Zero**.
- Mensagens da UI devem mostrar horario de envio do usuario e da resposta dos agentes.
- Hardware-alvo: Windows 11, Ryzen 5 8600G, RTX 5060 Ti 16 GB, 16 GB RAM; Ollama + qwen3.5:9b.

## Estado do codigo e entregas
- Projeto de origem: CAMPANARIO-IA.zip; nao substituir por outro projeto.
- Versao anterior: CAMPANARIO_FASE1_PONTO_ZERO.zip, que separou SQLite por CAMPANARIO_MEMORY_ENVIRONMENT (desenvolvimento/producao).
- Versao atual: pacote que acompanha este documento; verificar nome e conteudo do ZIP anexado.
- Perfil de chat leve: LOW_LATENCY_MODE=true, LIVE_STREAMING=true, MODEL_THINK=false; o pipeline legado de respostas fechadas e contornado no perfil leve.
- O pipeline legado ainda existe para compatibilidade e contem respostas fixas como Opa./Certo./Boa. Nao confundir existencia do codigo com execucao no modo leve.
- Pesquisa real, aprendizado persistente robusto e Ponto Zero final AINDA NAO ESTAO PRONTOS.
- A separacao de banco nao garante isolamento de arquivos, caches e integracoes; precisa auditoria antes do lancamento.
- Nao houve validacao fisica de desempenho no Neptune por este ambiente.

## Proximo passo obrigatorio
1. Auditar caminho completo da mensagem, inclusive contexto, perfis, memoria e filtros; verificar com testes se nenhuma resposta roteirizada entra no modo leve.
2. Registrar diagnosticos sem armazenar conversas privadas no pacote.
3. Projetar memoria episodica com origem, tempo, participantes e separacao individual/compartilhada.
4. Implementar e testar em etapas; nao afirmar que passou teste real com Ollama sem execucao no Neptune.

## Arquivos de referencia
- docs/architecture/PONTO_ZERO_PLANO.md
- docs/architecture/AUDITORIA_CONVERSACIONAL_FASE2.md
- docs/operations/RECUPERACAO_NEPTUNE.md
- docs/reference/personas/TODD_BACKGROUND.md
- docs/reference/personas/MORGANA_BACKGROUND.md
- src/campanario/composition.py
- src/campanario/chat/service.py
- src/campanario/response/pipeline.py

## Fase 4 — estrutura atual
- `docs/handoff/CONTINUIDADE_CHAT_NOVO.md`: resumo de continuidade.
- `docs/operations/`: recuperacao e diagnosticos Neptune.
- `docs/architecture/`: planejamento, organizacao e auditorias.
- `docs/history/checkpoints/`: checkpoints historicos; `docs/history/reports/`: relatorios antigos.
- `tools/maintenance/ATUALIZAR_CONTINUIDADE.py`: regenerar este documento.
- `tools/windows/` e `src/campanario/` mantidos em seus caminhos originais por compatibilidade.
- Fase 4: 492 testes aprovados, 4 falhas historicas de testes/documentacao antes da limpeza experimental; sem validacao no Neptune.

## Regras de retomada
- Ler estes documentos e inspecionar codigo ANTES de alterar.
- Preservar backup e manter CAMPANARIO_MEMORY_ENVIRONMENT=desenvolvimento durante testes.
- Nunca incorporar .env, credenciais, SQLite, caches, historicos privados ou pesos de modelos ao ZIP.
- Cada entrega: listar mudancas, testes executados, falhas e pendencias; atualizar este arquivo.
- Se o novo chat nao tiver acesso ao ZIP, solicitar o arquivo: texto sozinho nao permite editar o projeto.
'''


def main() -> None:
    TARGET.write_text(build_handoff(), encoding='utf-8')
    print(f'Continuidade atualizada: {TARGET}')


if __name__ == '__main__':
    main()
