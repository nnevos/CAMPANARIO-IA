"""Provider boundary for the next voice engine. No legacy Whisper/SAPI auto-loading."""
from campanario.runtime.media import unconfigured_voice_media


def build_voice_media(settings):
    """Keep existing voice/call contracts, but report an unconfigured physical provider."""
    return unconfigured_voice_media()
