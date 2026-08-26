from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from .types import Record


def loads(line: bytes) -> dict[str, Any]:
    try:
        import orjson
        return orjson.loads(line)
    except ImportError:
        return json.loads(line)


def dumps(value: dict[str, Any]) -> bytes:
    try:
        import orjson
        return orjson.dumps(value) + b"\n"
    except ImportError:
        return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def iter_jsonl(path: Path, start_after: int = -1) -> Iterable[tuple[int, str]]:
    with path.open("rb", buffering=4 * 1024 * 1024) as file:
        for index, line in enumerate(file):
            if index <= start_after or not line.strip():
                continue
            try:
                yield index, str(loads(line).get("text") or "")
            except Exception:
                continue


def iter_records(
    path: Path,
    prepare: Callable[[int, str], Record | None],
    start_after: int = -1,
) -> Iterable[Record]:
    for index, text in iter_jsonl(path, start_after):
        record = prepare(index, text)
        if record is not None:
            yield record


def read_progress(path: Path) -> int:
    try:
        return int(path.read_text(encoding="ascii").strip())
    except (FileNotFoundError, ValueError):
        return -1


def output_record(record: Record, anchor: str) -> dict[str, Any]:
    return {
        "text": f"{anchor}\n\n{record.body}",
        "source_index": record.source_index,
        "body_sha256": hashlib.sha256(record.body.encode("utf-8")).hexdigest(),
    }
