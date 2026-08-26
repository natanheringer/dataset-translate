from __future__ import annotations

import argparse
import itertools
import time
from pathlib import Path

from .core.batching import batches, tokenized_records
from .core.engine import create_translator, load_sentencepiece, translate_batch
from .core.io import dumps, iter_records, output_record, read_progress
from .profiles.code_anchor_en_pt import CodeAnchorEnPt


def run_source(args, translator, source_sp, target_sp, profile, name: str) -> None:
    source_path = args.raw_dir / f"{name}.jsonl"
    if not source_path.exists():
        print(f"[{name}] missing: {source_path}", flush=True)
        return
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.out_dir / f"{name}_pt.jsonl"
    reject_path = args.out_dir / f"{name}_pt.rejects.jsonl"
    progress_path = args.out_dir / f"{name}_pt.progress"
    start_after = read_progress(progress_path) if args.resume else -1
    if start_after >= 0:
        print(f"[{name}] resuming after input line {start_after}", flush=True)

    records = iter_records(
        source_path,
        lambda index, text: profile.prepare(index, text, args.extract_code),
        start_after,
    )
    if args.limit > 0:
        records = itertools.islice(records, args.limit)
    records = tokenized_records(
        records,
        lambda record: profile.tokenize(record, source_sp),
        args.tokenizer_threads,
        args.tokenizer_chunk,
    )
    pending = []
    stats = {"submitted": 0, "kept": 0, "rejected": 0, "retried": 0, "input_tokens": 0, "output_tokens": 0}
    started = time.monotonic()

    with output_path.open("ab" if args.resume else "wb", buffering=4 * 1024 * 1024) as out, reject_path.open(
        "ab" if args.resume else "wb", buffering=4 * 1024 * 1024
    ) as rejects:
        def consume(batch, async_results):
            results = [item.result() for item in async_results]
            retry = []
            for record, result in zip(batch, results):
                pieces = result.hypotheses[0]
                text = profile.normalize(target_sp.DecodePieces(pieces), record.anchor)
                if args.repair_terms and name == "tiny_codes":
                    text = profile.repair(text)
                stats["output_tokens"] += len(pieces)
                if args.retry_repetitions and profile.pathological_repetition(pieces):
                    retry.append(record)
                    continue
                ok, reason = profile.validate(text, record.anchor)
                if ok:
                    out.write(dumps(output_record(record, text)))
                    stats["kept"] += 1
                else:
                    rejects.write(dumps({"source_index": record.source_index, "reason": reason, "anchor": record.anchor, "output": text, "body": record.body}))
                    stats["rejected"] += 1
            if retry:
                stats["retried"] += len(retry)
                for record, result in zip(
                    retry,
                    translate_batch(translator, retry, args, asynchronous=False, no_repeat=args.fallback_no_repeat),
                ):
                    pieces = result.hypotheses[0]
                    text = profile.normalize(target_sp.DecodePieces(pieces), record.anchor)
                    if args.repair_terms and name == "tiny_codes":
                        text = profile.repair(text)
                    stats["output_tokens"] += len(pieces)
                    ok, reason = profile.validate(text, record.anchor)
                    if ok and not profile.pathological_repetition(pieces):
                        out.write(dumps(output_record(record, text)))
                        stats["kept"] += 1
                    else:
                        rejects.write(dumps({"source_index": record.source_index, "reason": "repetition_collapse" if profile.pathological_repetition(pieces) else reason, "anchor": record.anchor, "output": text, "body": record.body}))
                        stats["rejected"] += 1
            out.flush()
            rejects.flush()
            progress_path.write_text(f"{max(record.source_index for record in batch)}\n", encoding="ascii")

        for batch in batches(records, args.batch_tokens, args.max_batch_items, args.length_ratio):
            pending.append((batch, translate_batch(translator, batch, args)))
            stats["submitted"] += len(batch)
            stats["input_tokens"] += sum(len(record.pieces) for record in batch)
            if len(pending) >= args.inflight:
                consume(*pending.pop(0))
        for item in pending:
            consume(*item)

    elapsed = max(time.monotonic() - started, 1e-6)
    print(f"[{name}] kept={stats['kept']} rejected={stats['rejected']} submitted={stats['submitted']} input_tok={stats['input_tokens']} output_tok={stats['output_tokens']} retried={stats['retried']} {stats['output_tokens'] / elapsed:.0f} output_tok/s", flush=True)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--src", nargs="+", required=True)
    p.add_argument("--raw-dir", type=Path, default=Path("data"))
    p.add_argument("--out-dir", type=Path, default=Path("outputs"))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--model-dir", required=True)
    p.add_argument("--source-spm", required=True)
    p.add_argument("--target-spm", required=True)
    p.add_argument("--compute-type", default="int8_float16")
    p.add_argument("--batch-tokens", type=int, default=32768)
    p.add_argument("--max-batch-items", type=int, default=1024)
    p.add_argument("--length-ratio", type=float, default=2.0)
    p.add_argument("--inflight", type=int, default=6)
    p.add_argument("--inter-threads", type=int, default=2)
    p.add_argument("--max-queued-batches", type=int, default=12)
    p.add_argument("--beam", type=int, default=2)
    p.add_argument("--no-repeat-ngram-size", type=int, default=0)
    p.add_argument("--fallback-no-repeat", type=int, default=5)
    p.add_argument("--retry-repetitions", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--repair-terms", action="store_true")
    p.add_argument("--extract-code", action="store_true")
    p.add_argument("--tokenizer-threads", type=int, default=4)
    p.add_argument("--tokenizer-chunk", type=int, default=2048)
    p.add_argument("--max-decoding-length", type=int, default=512)
    p.add_argument("--max-decoding-ratio", type=float, default=4.0)
    p.add_argument("--min-decoding-length", type=int, default=1)
    p.add_argument("--max-input-length", type=int, default=0)
    p.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    p.add_argument("--device-index", type=int, default=0)
    p.add_argument("--flash-attention", action="store_true")
    p.add_argument("--use-vmap", action="store_true")
    p.add_argument("--repetition-penalty", type=float, default=1.0)
    p.add_argument("--resume", action="store_true")
    return p


def main() -> None:
    args = parser().parse_args()
    profile = CodeAnchorEnPt()
    source_sp = load_sentencepiece(Path(args.source_spm))
    target_sp = load_sentencepiece(Path(args.target_spm))
    translator = create_translator(args)
    for name in args.src:
        run_source(args, translator, source_sp, target_sp, profile, name)
