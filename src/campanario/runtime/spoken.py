from __future__ import annotations

import re
from dataclasses import dataclass, field

# Visual-only Unicode that should never be pronounced by a speech synthesizer.  Keep this
# deliberately separate from the assistant text stored in history/UI: sanitization is a media
# concern, not a semantic rewrite of the agent response.
_EMOJI_RE = re.compile(
    "["
    "\\U0001F1E6-\\U0001F1FF"  # flags
    "\\U0001F300-\\U0001F5FF"  # symbols & pictographs
    "\\U0001F600-\\U0001F64F"  # emoticons
    "\\U0001F680-\\U0001F6FF"  # transport & map
    "\\U0001F700-\\U0001F77F"
    "\\U0001F780-\\U0001F7FF"
    "\\U0001F800-\\U0001F8FF"
    "\\U0001F900-\\U0001F9FF"
    "\\U0001FA00-\\U0001FAFF"
    "\\u2600-\\u26FF"          # misc symbols
    "\\u2700-\\u27BF"          # dingbats
    "]+",
    flags=re.UNICODE,
)
_VARIATION_RE = re.compile(r"[\uFE0E\uFE0F\u200D]")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")
_HTML_RE = re.compile(r"<[^>]+>")
_LINE_MARKER_RE = re.compile(r"(?m)^\s{0,3}(?:#{1,6}\s+|[-*+]\s+|>\s+|\d+[.)]\s+)")
_MARKDOWN_PUNCT_RE = re.compile(r"(?:\*\*|__|~~|`{1,3})")


def sanitize_for_tts(text: str) -> str:
    """Return a speakable rendering while leaving the canonical response untouched elsewhere."""
    value = text.replace("\r", "\n")
    value = _MARKDOWN_LINK_RE.sub(r"\1", value)
    value = _URL_RE.sub("", value)
    value = _HTML_RE.sub(" ", value)
    value = _LINE_MARKER_RE.sub("", value)
    value = _MARKDOWN_PUNCT_RE.sub("", value)
    value = _EMOJI_RE.sub("", value)
    value = _VARIATION_RE.sub("", value)
    # Keycap combining mark and stray control-ish whitespace are also visual-only for SAPI.
    value = value.replace("\u20e3", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s*\n\s*", " ", value)
    return value.strip(" \t\n-–—•")


@dataclass(slots=True)
class SpokenOutputBuffer:
    """Turn model chunks into natural speech units instead of synthesizing token/chunk fragments.

    The model/UI stream remains untouched.  This buffer only controls when text crosses into TTS.
    Complete sentence boundaries are preferred; a bounded character fallback prevents a very long
    punctuation-free answer from delaying speech indefinitely.
    """

    max_chars: int = 220
    _by_agent: dict[str, str] = field(default_factory=dict, init=False)

    def push(self, agent_id: str, text: str) -> tuple[str, ...]:
        if not text:
            return ()
        current = self._by_agent.get(agent_id, "") + text
        ready: list[str] = []
        while current:
            cut = self._sentence_cut(current)
            if cut is None and len(current) >= self.max_chars:
                cut = self._soft_cut(current, self.max_chars)
            if cut is None:
                break
            piece, current = current[:cut], current[cut:]
            spoken = sanitize_for_tts(piece)
            if spoken:
                ready.append(spoken)
        self._by_agent[agent_id] = current
        return tuple(ready)

    def flush(self, agent_id: str) -> tuple[str, ...]:
        value = self._by_agent.pop(agent_id, "")
        spoken = sanitize_for_tts(value)
        return (spoken,) if spoken else ()

    def clear(self) -> None:
        self._by_agent.clear()

    @staticmethod
    def _sentence_cut(text: str) -> int | None:
        # Require punctuation plus following whitespace/end. Avoid cutting decimals such as 3.14.
        match = re.search(r"(?<!\d)[.!?](?:[\"')\]]+)?(?=\s|$)", text)
        return match.end() if match else None

    @staticmethod
    def _soft_cut(text: str, limit: int) -> int:
        window = text[:limit]
        candidates = [window.rfind(mark) for mark in (", ", "; ", ": ", " ")]
        cut = max(candidates)
        return (cut + 1) if cut >= max(40, limit // 2) else limit
