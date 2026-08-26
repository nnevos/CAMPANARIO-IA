from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import ExtractedEbook, SourceSegment


def _clean(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def extract_ebook(filename: str, payload: bytes) -> ExtractedEbook:
    suffix = Path(filename).suffix.lower()
    if suffix == ".docx":
        return _extract_docx(filename, payload)
    if suffix == ".pdf":
        return _extract_pdf(filename, payload)
    if suffix in {".txt", ".md"}:
        text = _clean(payload.decode("utf-8-sig", errors="replace"))
        segments = _chunk_plain(text, "text")
        return ExtractedEbook(filename, _title_hint(text, filename), tuple(segments), _normalize_for_match(text))
    raise ValueError("Formato não suportado. Use DOCX, PDF, TXT ou MD.")


def _extract_docx(filename: str, payload: bytes) -> ExtractedEbook:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ValueError("DOCX inválido ou corrompido.") from exc
    root = ET.fromstring(xml)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    units: list[str] = []
    # w:p is traversed in document order, including paragraphs inside tables.
    for paragraph in root.iter(ns + "p"):
        pieces = [(node.text or "") for node in paragraph.iter(ns + "t")]
        text = _clean("".join(pieces))
        if text:
            units.append(text)
    segments: list[SourceSegment] = []
    buffer: list[str] = []
    start_unit = 1
    for unit_no, text in enumerate(units, start=1):
        buffer.append(text)
        if sum(len(x) for x in buffer) >= 4500:
            segments.append(SourceSegment(f"docx:u{start_unit}-u{unit_no}", "\n".join(buffer)))
            buffer = []
            start_unit = unit_no + 1
    if buffer:
        segments.append(SourceSegment(f"docx:u{start_unit}-u{len(units)}", "\n".join(buffer)))
    text = "\n".join(units)
    if len(text) < 300:
        raise ValueError("O DOCX não contém texto suficiente para gerar um jogo.")
    return ExtractedEbook(filename, _title_hint(text, filename), tuple(segments), _normalize_for_match(text))


def _extract_pdf(filename: str, payload: bytes) -> ExtractedEbook:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF requer o pacote opcional pypdf. Use DOCX, TXT ou MD nesta instalação.") from exc

    reader = PdfReader(io.BytesIO(payload))
    segments: list[SourceSegment] = []
    all_text: list[str] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = _clean(page.extract_text() or "")
        if not text:
            continue
        all_text.append(text)
        segments.append(SourceSegment(f"pdf:p{idx}", text))
    text = "\n".join(all_text)
    if len(text) < 300:
        raise ValueError("O PDF não contém texto extraível suficiente.")
    return ExtractedEbook(filename, _title_hint(text, filename), tuple(segments), _normalize_for_match(text))


def _chunk_plain(text: str, prefix: str) -> list[SourceSegment]:
    chunks: list[SourceSegment] = []
    for idx in range(0, len(text), 4500):
        chunks.append(SourceSegment(f"{prefix}:{idx // 4500 + 1}", text[idx : idx + 4500]))
    return chunks


def _title_hint(text: str, filename: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:30]:
        lowered = line.casefold()
        if "nome da unidade" in lowered and ":" in line:
            value = line.split(":", 1)[1].strip()
            if value:
                return value
    candidate = next((line for line in lines[:12] if 6 <= len(line) <= 140 and "unidade" not in line.casefold()), "")
    return candidate or Path(filename).stem


__all__ = ["extract_ebook", "_normalize_for_match"]
