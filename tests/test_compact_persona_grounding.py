from campanario.chat.prompts import COMPACT_BEHAVIOR_PROMPT


def test_compact_prompt_prioritizes_context_and_no_fake_actions():
    prompt = COMPACT_BEHAVIOR_PROMPT.lower()
    assert "referente na conversa" in prompt
    assert "leu logs" in prompt
    assert "nao recite" in prompt
    assert "memoria pessoal" in prompt
