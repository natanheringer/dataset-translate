from __future__ import annotations

from ..policies import code


class CodeAnchorEnPt:
    """Translate the natural-language anchor and preserve the document body."""

    name = "code_anchor_en_pt"

    def prepare(self, index: int, text: str, extract_code: bool):
        return code.prepare_anchor(index, text, extract_code)

    def tokenize(self, record, source_sp):
        return code.tokenize(record, source_sp)

    def normalize(self, text: str, source: str) -> str:
        return code.normalize(text, source)

    def validate(self, text: str, source: str):
        return code.validate(text, source)

    def pathological_repetition(self, pieces):
        return code.pathological_repetition(pieces)

    def repair(self, text: str) -> str:
        return code.repair_terms(text)
