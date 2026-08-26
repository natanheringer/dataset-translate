#!/usr/bin/env python3
"""Verify that accepted translations preserved their original document body."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load_json(line: bytes):
    try:
        import orjson

        return orjson.loads(line)
    except ImportError:
        return json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--translated", type=Path, required=True)
    args = parser.parse_args()

    source_bodies = {}
    with args.source.open("rb") as source:
        for index, line in enumerate(source):
            if line.strip():
                text = load_json(line).get("text") or ""
                source_bodies[index] = text.split("\n\n", 1)[1] if "\n\n" in text else ""

    checked = 0
    failures = []
    with args.translated.open("rb") as translated:
        for line in translated:
            record = load_json(line)
            index = record.get("source_index")
            body = (record.get("text") or "").split("\n\n", 1)[1] if "\n\n" in (record.get("text") or "") else ""
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            expected = source_bodies.get(index)
            if expected is None or body != expected or digest != record.get("body_sha256"):
                failures.append(index)
            checked += 1

    print(f"checked={checked} failures={len(failures)}")
    if failures:
        print("failed_source_indices=" + ",".join(map(str, failures[:20])))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
