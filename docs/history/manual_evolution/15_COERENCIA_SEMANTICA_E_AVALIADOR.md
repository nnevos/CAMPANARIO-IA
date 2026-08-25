# 15 - Coerencia semantica e avaliador E2E

## Objetivo

A v1.5.5 endurece duas camadas diferentes:

1. o runtime, para rejeitar respostas curtas que cumprem forma mas nao cumprem a funcao conversacional;
2. o Behavioral E2E, para reduzir falsos PASS em respostas semanticamente artificiais ou factualmente fracas.

O avaliador continua **deterministico e auditavel**. Ele nao usa o proprio LLM como juiz principal de naturalidade.

## O que passou a ser verificado

### Cumprimentos

Uma resposta curta nao basta. O teste rejeita respostas que sao apenas outro vocativo, como trocar `parceiro` por `amigo`, ou que iniciam uma apresentacao institucional.

### Compartilhamento social

O sistema nao deve inventar contexto temporal (`bom dia`, `boa noite`) que o usuario nao forneceu e nao deve apenas parafrasear o estado obvio do usuario como se fosse analise.

### Encerramento de topico

Uma resposta precisa funcionar como encerramento. Frases curtas mas quebradas, como `Parece que voce deseja.`, nao passam apenas por terem poucas palavras e nenhuma pergunta.

### Verdade acima de concordancia

Tambem e invalido prometer *simular* concordancia falsa ou agir como se algo falso fosse verdadeiro apenas por preferencia do usuario.

### Criativo -> factual

A proveniencia continua isolando ficcao anterior. O E2E agora tambem usa ancoras factuais variadas para a pergunta factual posterior, sem hardcodar respostas no runtime.

## Anti-overfitting

Os checks sao aplicados a familias de comportamento. Frases, entidades, assuntos, factual anchors e ordem dos cenarios variam por seed.

Uma falha deve ser corrigida na classe semantica correspondente. Nao adicionar uma resposta pronta para a frase que falhou.

## Interpretacao do relatorio

- `FAIL`: violacao objetiva ou semantica forte detectada.
- `WARN`: sinal que merece revisao humana, mas pode depender de contexto/estilo.
- `PASS`: passou nos checks configurados; ainda nao significa naturalidade humana perfeita.

Por isso o transcript continua obrigatorio para fechar o gate de naturalidade.
