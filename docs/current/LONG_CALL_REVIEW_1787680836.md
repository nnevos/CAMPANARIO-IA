# Long Call review — seed 1787680836

Suite: `agent_long_call` · model: `gemma3:12b`

Result: **WARN** · 0 PASS / 3 WARN / 0 FAIL scenarios · **244 PASS / 12 WARN / 0 FAIL checks**.

## What improved

- speaker provenance and direct addressing remained stable;
- arithmetic correction remained correct;
- continuous-presence semantics and thinking-aloud silence were materially better;
- closure no longer opened a new question;
- no hard runtime failure occurred.

## Remaining structural issue

P2.4 successfully compiled a typed dialogue state, but Gemma could still treat that state as descriptive context rather than a binding answer obligation. The failures were concentrated in pragmatic reference/answer binding:

- `proximo passo` could still request context already present;
- `sequencia curta` could answer generically rather than remain on the latency investigation;
- `resume a decisao` could explain summarization instead of summarizing the actual decision;
- `aterrissa isso` / `mesma pergunta` could lose an immediately available referent;
- product cut/preserve/synthesis could drift toward agent traits or meta-concepts instead of the user-owned product branch.

Latency also regressed relative to the prior seed, so any additional mechanism must remain deterministic and avoid a second interpretation LLM.

## P2.4.1 response

Add `AnswerContract` after persona/social/output guidance and validate only critical observable bindings locally. One regeneration is permitted when the model violates a resolved contract. This keeps Dialogue State as interpretation and Answer Contract as execution obligation.

Next gate: rerun `tools/windows/TESTAR_LONG_CALL.bat` with Gemma 3 12B. Do not start F3 Platform Foundation before this revalidation and F2 freeze decision.
