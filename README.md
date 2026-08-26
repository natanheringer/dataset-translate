# dataset-translate

Reproducible, auditable bulk translation for code and reasoning corpora.

The pipeline separates natural-language translation from code preservation. The neural model receives only the translatable anchor/prose. The original document body is copied byte-for-byte into the output and is accompanied by a source index and SHA-256 hash.

## Repository Layout

```text
src/dataset_translate/core/     streaming I/O, batching, CTranslate2 runtime
src/dataset_translate/profiles/ dataset shapes and translation profiles
src/dataset_translate/policies/ protected content, validation, repair rules
scripts/                        model preparation, CLI entry point, auditing
tests/fixtures/                 small reproducible inputs
```

The current profile is `code_anchor_en_pt`. It is a profile, not a requirement of the core: a future prose or reasoning profile can reuse the same streaming and neural runtime.

## Windows and 4 GB GPUs

Windows is supported through the same Python entry point and PowerShell wrappers. Install this package normally (a virtual environment is optional):

```powershell
python -m pip install -e ".[dev]"
```

Prepare the model with:

```powershell
.\scripts\prepare_model.ps1
```

Run a dataset with the conservative 4 GB profile:

```powershell
.\scripts\translate_windows.ps1 `
  -Source python_codes_25k `
  -RawDir data `
  -OutDir outputs\python_codes_25k `
  -Resume
```

The wrapper defaults to `-Device auto`: it tries CUDA with `int8_float16` and automatically retries with CPU `int8` when CUDA/cuBLAS is unavailable or fails. Use `-Device cpu` to skip CUDA, or `-Device cuda` to fail instead of falling back. The `configs/windows_gpu_4gb.yaml` values are intentionally conservative: INT8 weights, FP16 compute, one worker, one in-flight batch, beam 1, and 1024 source tokens per batch. A 4 GB GPU should be able to load the converted model, but long inputs and retry batches can still cause an out-of-memory error. Raise `BatchTokens` gradually (`1024` → `1536` → `2048`) only after a successful run. If it still fails, use `-BatchTokens 512` and `-Beam 1`.

For a CPU-only run:

```powershell
.\scripts\translate_windows.ps1 `
  -Device cpu `
  -Source example_templates `
  -RawDir data `
  -OutDir outputs\example_templates `
  -Resume
```

## Design

- CTranslate2 runs OPUS-MT/Marian on CUDA.
- `int8_float16` reduces model memory while retaining FP16 activations where needed.
- Batches are bounded by source token count and grouped by length.
- SentencePiece tokenization is pipelined in CPU threads.
- Translation is asynchronous and resumable through a progress sidecar.
- `no_repeat_ngram_size` is disabled by default; repetition recovery is adaptive.
- Code integrity is checked independently from translation quality.

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Prepare Model

```bash
python scripts/prepare_model.py \
  --raw-dir models/opus-mt-tc-big-en-pt \
  --output-dir models/opus-mt-tc-big-en-pt-ct2
```

The model files are intentionally ignored by Git. The repository records the model ID and conversion settings, not the checkpoint.

## Translate

### Quick Example

Prepare the model once:

```bash
python scripts/prepare_model.py \
  --raw-dir models/opus-mt-tc-big-en-pt \
  --output-dir models/opus-mt-tc-big-en-pt-ct2
```

Then translate the included four-record example:

```bash
python scripts/translate_anchors.py \
  --src example \
  --raw-dir data \
  --out-dir outputs/example \
  --model-dir models/opus-mt-tc-big-en-pt-ct2 \
  --source-spm models/opus-mt-tc-big-en-pt-ct2/source.spm \
  --target-spm models/opus-mt-tc-big-en-pt-ct2/target.spm \
  --extract-code \
  --limit 4
```

The source fixture is `data/example.jsonl`. The translated records are written to `outputs/example/example_pt.jsonl`; rejected records are written beside it with the `.rejects.jsonl` suffix.

### Template Showcase

For a more representative run, `data/example_templates.jsonl` contains 100 real synthetic templates sampled from the `tiny_codes` source. It is still small enough to commit, but exercises multiple languages, anchor lengths, batching, validation, and code preservation:

```bash
python scripts/translate_anchors.py \
  --src example_templates \
  --raw-dir data \
  --out-dir outputs/example_templates \
  --model-dir models/opus-mt-tc-big-en-pt-ct2 \
  --source-spm models/opus-mt-tc-big-en-pt-ct2/source.spm \
  --target-spm models/opus-mt-tc-big-en-pt-ct2/target.spm \
  --extract-code \
  --repair-terms \
  --limit 100
```

```bash
python scripts/translate_anchors.py \
  --src python_codes_25k \
  --raw-dir data \
  --out-dir outputs/python_codes_25k \
  --model-dir models/opus-mt-tc-big-en-pt-ct2 \
  --source-spm models/opus-mt-tc-big-en-pt-ct2/source.spm \
  --target-spm models/opus-mt-tc-big-en-pt-ct2/target.spm \
  --extract-code --resume
```

Correct the model path in the example if using a different directory. A run can be stopped and resumed with `--resume`; accepted records, rejects, and progress are separate files.

## Audit Code

```bash
python scripts/audit_code_integrity.py \
  --source data/python_codes_25k.jsonl \
  --translated outputs/python_codes_25k/python_codes_25k_pt.jsonl
```

The audit must report zero failures before translated code-containing data enters training.

## Reproducibility

Do not commit datasets, model weights, generated outputs, credentials, or machine-specific paths. Commit only scripts, fixtures, configs, dependency pins, and reports containing aggregate counts. Record the model repository revision and the command line used for every production run.
