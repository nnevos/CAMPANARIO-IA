# ADR-0007 — Resumo de contexto estruturado e consciente da fonte

**Status:** Aceito em 2026-08-24.

## Contexto

O teste manual da sumarização persistida mostrou dois modos de falha:

1. fatos explicitamente declarados pelo usuário foram distorcidos por sugestões anteriores do próprio assistant (os livros `astronomia`, `história` e `programação` viraram gêneros sugeridos pelo assistant);
2. após reinício, o modelo chegou a afirmar que havia perdido o contexto mesmo quando o resumo persistido ainda continha fatos antigos.

Um resumo livre mistura fontes com níveis de confiança diferentes e pode promover texto gerado pelo próprio modelo a evidência factual.

## Decisão

O `ContextSummary.content` continua na mesma tabela/coluna, mas passa a armazenar JSON estruturado versão 1 com:

- `first_user_message`;
- `user_facts`;
- `user_preferences`;
- `user_plans`;
- `user_constraints`;
- `conversation_topics`;
- `assistant_context`.

Regras:

- a extração dos campos `user_*` ocorre em uma chamada que recebe apenas mensagens `USER` e contexto autoritativo anterior;
- `assistant_context` é resumido em uma segunda chamada que recebe apenas mensagens `ASSISTANT`;
- `assistant_context` é explicitamente não autoritativo e não pode sobrescrever campos derivados do usuário;
- a primeira mensagem do usuário é calculada deterministicamente do histórico e sobrescreve qualquer versão produzida pelo modelo de sumarização;
- resumos legados em texto livre são considerados não confiáveis e reconstruídos do histórico original na primeira oportunidade;
- saída inválida/não JSON da sumarização não é persistida e mantém o fallback existente para a janela recente;
- o contexto final informa explicitamente que o resumo vem do armazenamento da sessão e pode sobreviver a reinícios.

## Consequências

- nenhuma migration adicional é necessária: o formato muda dentro da coluna `content` existente;
- o histórico original continua sendo a evidência final e permanece intacto;
- isto ainda é Context Manager, não memória cognitiva/episódica/semântica;
- a qualidade da extração ainda depende do modelo local, portanto o próximo gate continua sendo validação manual no Windows/Ollama com fatos conflitantes e reinício.
