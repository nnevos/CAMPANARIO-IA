# Conversa Humana Baseline

Use `tools/windows/TESTAR_CONVERSA_HUMANA.bat` para avaliar Todd e Morgana em conversas comuns, persistentes e sem objetivo técnico.

A suíte completa `agent_human_baseline` executa 10 episódios / 80 turnos: quatro roteiros pareados Todd × Morgana com exatamente as mesmas falas do usuário e duas salas compartilhadas com os dois presentes. A versão `agent_human_quick` executa 5 episódios / 40 turnos para smoke test.

O baseline cobre: se conhecer sem interrogatório; conversa sem pedido de ajuda; histórias pequenas; humor; discordância leve; mudança de assunto; retomada; memória local; callbacks; silêncio seletivo; ausência de fechamento de atendimento; e convivência Todd + Morgana.

O relatório normal contém checks automáticos de invariantes. `latest.blind.md` é a revisão cega: leia antes do relatório principal e tente identificar Todd/Morgana pelas respostas. Naturalidade é avaliada de 1 a 5 em continuidade, curiosidade proporcional, ausência de palestra/interrogatório, memória contextual, personalidade e vontade de continuar conversando.

Não use a suíte para hardcodar respostas. Um resultado ruim deve orientar ajustes de Personality Core/aplicação, protocolo social, contexto ou participação. O transcript humano é a evidência principal para naturalidade.
