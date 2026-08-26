from campanario.runtime.spoken import SpokenOutputBuffer, sanitize_for_tts


def test_tts_sanitizer_removes_emoji_markdown_and_urls_without_changing_words() -> None:
    text = "**Claro!** 😄 Veja [isso](https://example.com) — https://x.test 🚀"
    assert sanitize_for_tts(text) == "Claro! Veja isso"


def test_tts_sanitizer_removes_list_and_heading_markers() -> None:
    assert sanitize_for_tts("## Ideia\n- primeira coisa\n- segunda coisa") == "Ideia primeira coisa segunda coisa"


def test_spoken_output_buffers_model_chunks_until_sentence_boundary() -> None:
    buffer = SpokenOutputBuffer()
    assert buffer.push("morgana", "Isso e uma res") == ()
    assert buffer.push("morgana", "posta inteira. E outra") == ("Isso e uma resposta inteira.",)
    assert buffer.flush("morgana") == ("E outra",)


def test_spoken_output_discards_visual_only_chunk() -> None:
    buffer = SpokenOutputBuffer()
    assert buffer.push("todd", "😄 ") == ()
    assert buffer.push("todd", "Pronto.") == ("Pronto.",)
    assert buffer.flush("todd") == ()
