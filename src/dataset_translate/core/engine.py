from __future__ import annotations

from pathlib import Path


def load_sentencepiece(path: Path):
    import sentencepiece as spm

    if not path.is_file():
        raise SystemExit(
            f"SentencePiece file not found: {path}\n"
            "Run 'python scripts/prepare_model.py' first, or pass the path "
            "to an existing converted model."
        )
    processor = spm.SentencePieceProcessor()
    if not processor.Load(str(path)):
        raise RuntimeError(f"could not load SentencePiece model: {path}")
    return processor


def create_translator(args):
    import ctranslate2

    if not Path(args.model_dir).is_dir():
        raise SystemExit(
            f"CTranslate2 model directory not found: {args.model_dir}\n"
            "Run 'python scripts/prepare_model.py' first."
        )
    if args.device == "cuda":
        try:
            supported = ctranslate2.get_supported_compute_types("cuda", args.device_index)
        except TypeError:
            supported = ctranslate2.get_supported_compute_types("cuda")
        print(f"CTranslate2 CUDA compute types: {sorted(supported)}", flush=True)
        if args.compute_type not in supported:
            raise SystemExit(f"unsupported compute type: {args.compute_type}")
    return ctranslate2.Translator(
        args.model_dir,
        device=args.device,
        device_index=args.device_index,
        compute_type=args.compute_type,
        inter_threads=args.inter_threads,
        max_queued_batches=args.max_queued_batches,
        flash_attention=args.flash_attention,
    )


def translate_batch(translator, batch, args, *, asynchronous=True, no_repeat=None):
    source_max = max(len(record.pieces) for record in batch)
    dynamic_max = min(
        args.max_decoding_length,
        max(args.min_decoding_length, int(source_max * args.max_decoding_ratio + 16)),
    )
    return translator.translate_batch(
        [record.pieces for record in batch],
        asynchronous=asynchronous,
        beam_size=args.beam,
        max_decoding_length=dynamic_max,
        min_decoding_length=args.min_decoding_length,
        no_repeat_ngram_size=args.no_repeat_ngram_size if no_repeat is None else no_repeat,
        repetition_penalty=args.repetition_penalty,
        batch_type="tokens",
        max_batch_size=args.batch_tokens,
        max_input_length=args.max_input_length,
        return_scores=False,
        use_vmap=args.use_vmap,
    )
