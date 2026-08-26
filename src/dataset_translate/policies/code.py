from __future__ import annotations

import difflib
import re

from ..core.types import Record

BAD = re.compile(
    r"^(aqui está|segue|claro|certamente|tradução|here is|here's|sure|translation)"
    r"|^```|\bcomo posso\b|\bnão posso\b|\bI cannot\b",
    re.I,
)
FENCED_CODE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]+`")


def prepare_anchor(index: int, text: str, extract_code: bool) -> Record | None:
    parts = text.split("\n\n", 1)
    if len(parts) != 2:
        return None
    anchor, body = parts[0].strip(), parts[1]
    if not anchor:
        return None
    if extract_code:
        anchor = FENCED_CODE.sub(" ", anchor)
        anchor = INLINE_CODE.sub(" ", anchor)
        anchor = re.sub(r"\s+", " ", anchor).strip() or parts[0].strip()
    return Record(index, anchor, body, [])


def tokenize(record: Record, source_sp) -> Record:
    record.pieces = source_sp.EncodeAsPieces(record.anchor)
    return record


def repair_terms(text: str) -> str:
    text = re.sub(r"\bse\s*mudar\s*/\s*caso\b", "switch/case", text, flags=re.I)
    text = re.sub(r"\bmudar\s*/\s*caso\b", "switch/case", text, flags=re.I)
    return re.sub(r"\bse\s*/\s*", "if/else ", text, flags=re.I)


def collapse_duplicate_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept: list[str] = []
    for sentence in sentences:
        normalized = re.sub(r"[^\w]+", " ", sentence.casefold()).strip()
        if kept:
            previous = re.sub(r"[^\w]+", " ", kept[-1].casefold()).strip()
            if len(normalized) >= 20 and difflib.SequenceMatcher(None, previous, normalized).ratio() >= 0.92:
                continue
        kept.append(sentence)
    return " ".join(kept)


def trim_repeated_tail(text: str, source: str) -> str:
    if len(text) <= len(source) * 2.5:
        return text
    words = text.split()
    for width in (4, 3):
        first: dict[tuple[str, ...], int] = {}
        for index in range(len(words) - width + 1):
            key = tuple(words[index : index + width])
            if key in first and index - first[key] >= width:
                return " ".join(words[:index]).strip(" ,;:")
            first[key] = index
    return text


def normalize(text: str, source: str) -> str:
    text = collapse_duplicate_sentences(text.strip())
    source_count = max(1, len(re.findall(r"[.!?](?:\s|$)", source)))
    if source_count == 1:
        text = re.split(r"(?<=[.!?])\s+", text)[0].strip()
    return trim_repeated_tail(text, source)


def pathological_repetition(pieces: list[str]) -> bool:
    if len(pieces) < 16:
        return False
    if any(pieces[i] == pieces[i + 1] == pieces[i + 2] == pieces[i + 3] for i in range(len(pieces) - 3)):
        return True
    seen: dict[tuple[str, ...], int] = {}
    for index in range(len(pieces) - 2):
        key = tuple(pieces[index : index + 3])
        seen[key] = seen.get(key, 0) + 1
        if seen[key] >= 5:
            return True
    return False


def validate(text: str, source: str) -> tuple[bool, str]:
    if not text:
        return False, "empty"
    if BAD.search(text):
        return False, "preamble_or_refusal"
    if len(text) < len(source) * 0.4 or len(text) > len(source) * 2.5:
        return False, "implausible_length"
    if text.strip('"').lower() == source.strip('"').lower():
        return False, "unchanged"
    return True, "ok"
