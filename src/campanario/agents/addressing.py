from __future__ import annotations

import re
import unicodedata


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def directly_addressed_agent(text: str) -> str | None:
    """Return a directly addressed agent in common call-style vocative positions.

    Supports both leading vocatives ("Morgana, ...") and natural trailing vocatives
    ("... quanto, Morgana?" / "... resume em uma frase, Morgana."). A name merely
    mentioned inside the sentence is not treated as an address.
    """
    folded = fold_text(text)
    leading = re.match(r"^(todd|morgana)(?:\b|\s*[:,.!?-])", folded)
    if leading:
        return leading.group(1)

    # In spoken calls users very often place the vocative at the end. Restrict this to the
    # final token so "a Morgana disse..." remains a reference, not an address.
    trailing = re.search(r"(?:^|[\s,;:])(?P<agent>todd|morgana)\s*[?.!]*$", folded)
    if trailing:
        return trailing.group("agent")
    return None


def standalone_wake_target(text: str, registered_agents=()) -> str | None:
    """Recognize a short *call* to this system or a configured chat agent.

    Unlike a factual question about a name, a bare vocative (``Todd?``)
    needs conversational routing, not retrieval. Matching the complete
    utterance prevents bypassing source checks in ``Todd, quem foi X?``.
    The registry, not an internet-entity catalogue, supplies agent names.
    """
    utterance = fold_text(text).strip().strip('?!.,:; \t\r\n')
    if not utterance:
        return None
    # Spoken vocatives may begin with one greeting; never strip arbitrary
    # prefixes such as "e" (which can be a factual follow-up about a name).
    for prefix in ('oi', 'ola', 'ei', 'alo', 'hey'):
        if utterance.startswith(prefix) and utterance[len(prefix):len(prefix)+1] in (' ', ',', ':', ';'):
            utterance = utterance[len(prefix):].lstrip(' ,:;')
            break
    if utterance == 'campanario':
        return 'campanario'  # System wake, not a fabricated third persona.
    for profile in registered_agents:
        agent_id = getattr(profile, 'id', '')
        agent_name = getattr(profile, 'name', '')
        if utterance in {fold_text(agent_id), fold_text(agent_name)}:
            return agent_id
    return None
