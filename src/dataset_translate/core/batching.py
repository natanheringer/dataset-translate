from __future__ import annotations

import itertools
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

from .types import Record


def tokenized_records(records: Iterable[Record], tokenize, workers: int, chunk_size: int):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while True:
            chunk = list(itertools.islice(records, chunk_size))
            if not chunk:
                return
            yield from pool.map(tokenize, chunk)


def batches(records: Iterable[Record], max_tokens: int, max_items: int, length_ratio: float):
    pending: list[Record] = []
    token_count = 0
    max_length = 0
    for record in records:
        size = max(len(record.pieces), 1)
        length_break = pending and (
            size > max_length * length_ratio or max_length > size * length_ratio
        )
        if pending and (token_count + size > max_tokens or len(pending) >= max_items or length_break):
            yield sorted(pending, key=lambda item: len(item.pieces), reverse=True)
            pending, token_count, max_length = [], 0, 0
        pending.append(record)
        token_count += size
        max_length = max(max_length, size)
    if pending:
        yield sorted(pending, key=lambda item: len(item.pieces), reverse=True)
