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
