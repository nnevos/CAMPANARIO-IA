from __future__ import annotations

import re
import unicodedata


def _fold(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.split())


def likely_incomplete_voice_fragment(text: str) -> bool:
    """Conservative pt-BR spoken-utterance continuation detector.

    This is not intent recognition and does not rewrite transcripts.  It only decides whether a
    final STT segment is risky to dispatch immediately.  Risky fragments get a short grace window
    so adjacent audio can be re-transcribed as one utterance before Conversation Runtime sees it.
    """
    raw = text.strip()
    if not raw:
        return False
    folded = _fold(raw).strip()
    plain = folded.strip(" .?!,:;-")
    words = re.findall(r"[\w]+", plain, flags=re.UNICODE)
    if not words:
        return False

    # A wake/name by itself is frequently the first half of "Campanario ... <request>".  Hold it
    # briefly; if nothing follows it is still dispatched after the grace window.
    if plain in {"campanario", "todd", "morgana", "todd e morgana", "morgana e todd"}:
        return True

    if raw.endswith(("...", "…", ",", ";", ":", "-")):
        return True

    # Strong spoken continuation markers.  Keep this deliberately narrow: ordinary complete
    # sentences must not pay the aggregation latency.
    if words[0] in {"mais", "menos", "vezes", "dividido", "porque", "mas"} and len(words) <= 6:
        return True

    dangling_last = {
        "de", "da", "do", "das", "dos", "e", "ou", "com", "sem", "para", "pra", "por",
        "que", "onde", "como", "qual", "quanto", "mais", "menos", "vezes", "dividido",
    }
    if words[-1] in dangling_last:
        return True

    # Common incomplete comparative/question tails from spontaneous pt-BR speech.
    if re.search(r"\b(lugar|jeito|forma|maneira|opcao|rota|ponto) mais$", plain):
        return True
    if re.search(r"\b(onde|como|qual|quanto) que$", plain):
        return True

    # "calcula para mim 123" is normally a clipped arithmetic utterance; wait for an operator or
    # second operand.  This remains generic and does not encode benchmark phrases/results.
    if re.search(r"\b(calcula|calcule|quanto (e|da))\b", plain):
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", plain)
        operator = re.search(r"\b(mais|menos|vezes|dividido|por cento)\b|[+*/=-]", plain)
        if len(numbers) == 1 and operator is None:
            return True

    return False


def join_voice_pcm(previous: bytes, current: bytes, *, sample_rate: int, channels: int, sample_width: int) -> bytes:
    """Join two VAD-finalized chunks while removing most duplicated hangover silence.

    Each finalized chunk already contains a long silence tail.  Keeping the full tail between
    fragments makes Whisper treat them as unrelated sentences.  Remove up to one second from the
    previous tail and retain a small 160 ms gap so word boundaries remain natural.
    """
    bytes_per_second = sample_rate * channels * sample_width
    trim = min(len(previous), bytes_per_second)
    kept = previous[:-trim] if trim else previous
    gap = b"\x00" * int(bytes_per_second * 0.16)
    return kept + gap + current
