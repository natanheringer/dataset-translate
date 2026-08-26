from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Record:
    source_index: int
    anchor: str
    body: str
    pieces: list[str]
