# 17 - Truth Contract, output inteiro e mega teste

## O que mudou na v1.5.7

A v1.5.7 fecha tres classes de erro observadas no Ollama real:

1. **Truth Contract**: pedir para a IA nunca contrariar/corrigir/contradizer mesmo diante de falsidade nao desativa o compromisso com fatos. Preferencias podem mudar estilo, nao verdade.
2. **Whole-output validation**: em pedidos como `exatamente duas frases`, qualquer preambulo extra tambem conta como parte da saida e pode reprovar o contrato.
3. **Factual mechanism hardening**: os testes factuais procuram mecanismo plausivel e contradicoes, nao apenas palavras relacionadas ao tema.

O runtime nao recebeu respostas factuais prontas para perguntas de teste.

## Teste padrao

Execute `TESTAR_COMPORTAMENTO.bat`. Revise `test_reports/behavioral_e2e/latest.html`. Um PASS automatico ainda exige leitura humana do transcript.

## Mega teste

Somente depois de standard verde + revisao humana favoravel, execute `TESTAR_COMPORTAMENTO_MEGA.bat`.

A bateria mega usa seis lotes full com seeds derivados. Ela testa muitas combinacoes de greeting, social, reaction, acknowledgement, topic-drop, criativo->factual, factual anchors, verdade, correction, self-awareness e tecnico, com ordem/lexico variados.

## Depois do mega teste

Se o resultado amplo estiver satisfatorio, nao adicione Todd/Morgana imediatamente. O proximo passo obrigatorio e refatorar a estrutura do projeto para separar claramente runtime conversacional, pragmatica, contratos, contexto/memoria, guards, E2E, configuracao e documentacao.
