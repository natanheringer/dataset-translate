#!/usr/bin/env python3
"""Download and convert an OPUS-MT checkpoint for the bulk translator.

The Hugging Face OPUS-MT repositories expose Transformers-format Marian
checkpoints. ``ct2-opus-mt-converter`` expects the older native Marian layout
with decoder.yml, so this script intentionally uses the Transformers converter.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="Helsinki-NLP/opus-mt-tc-big-en-pt")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--quantization", default="int8_float16")
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        args.repo,
        local_dir=str(args.raw_dir),
        allow_patterns=[
            "config.json",
            "generation_config.json",
            "model.safetensors",
            "source.spm",
            "target.spm",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.json",
        ],
    )

    converter = shutil.which("ct2-transformers-converter")
    if converter is None:
        raise SystemExit("ct2-transformers-converter not found; install ctranslate2")
    subprocess.run(
        [
            converter,
            "--model",
            str(args.raw_dir),
            "--output_dir",
            str(args.output_dir),
            "--quantization",
            args.quantization,
            "--copy_files",
            "source.spm",
            "target.spm",
        ],
        check=True,
    )
    required = [args.output_dir / name for name in ("config.json", "model.bin", "source.spm", "target.spm")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("conversion completed without required files: " + ", ".join(missing))
    print(f"ready: {args.output_dir}")


if __name__ == "__main__":
    main()
