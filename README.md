# dataset-translate

Batch translation for datasets that contain natural language and code.

The pipeline translates only the natural-language parts and keeps protected code unchanged. It processes JSONL files incrementally, writes progress files, and can resume an interrupted run.

## Requirements

- Python 3.11 or newer
- A converted CTranslate2 model
- CUDA is optional; CPU mode is supported

## Install

Run this from the repository directory:

```bash
python -m pip install -e ".[dev]"
```

On Windows, use `python` rather than `py -3.11` when Python 3.13 is installed. A virtual environment is optional.

## Prepare the Model

Download and convert the model once:

```bash
python scripts/prepare_model.py \
  --raw-dir models/opus-mt-tc-big-en-pt \
  --output-dir models/opus-mt-tc-big-en-pt-ct2
```

Model files are ignored by Git. Each machine must prepare or receive its own model files.

## Translate a Dataset

Place the input at `data/<name>.jsonl`. Then run:

```bash
python scripts/translate_anchors.py \
  --src <name> \
  --raw-dir data \
  --out-dir outputs/<name> \
  --model-dir models/opus-mt-tc-big-en-pt-ct2 \
  --source-spm models/opus-mt-tc-big-en-pt-ct2/source.spm \
  --target-spm models/opus-mt-tc-big-en-pt-ct2/target.spm \
  --extract-code \
  --resume
```

The accepted records, rejected records, and progress data are written under `outputs/<name>/`.

The repository includes `data/example.jsonl` and `data/example_templates.jsonl` for testing. For the larger sample, replace `<name>` with `example_templates`.

## Windows

Use the PowerShell wrapper:

```powershell
.\scripts\translate_windows.ps1 `
  -Source <name> `
  -RawDir data `
  -OutDir outputs\<name> `
  -Resume
```

The default `-Device auto` tries CUDA first and retries with CPU if CUDA or cuBLAS is unavailable. To use CPU directly:

```powershell
.\scripts\translate_windows.ps1 `
  -Device cpu `
  -Source <name> `
  -RawDir data `
  -OutDir outputs\<name> `
  -Resume
```

Use `-Device cuda` to require CUDA. The Windows defaults are conservative for limited GPU memory. Lower `-BatchTokens` if the GPU runs out of memory.

## Audit Code

After translation, compare the source and translated output:

```bash
python scripts/audit_code_integrity.py \
  --source data/<name>.jsonl \
  --translated outputs/<name>/<name>_pt.jsonl
```

Code-containing data should have zero audit failures before entering training.

## Layout

```text
src/dataset_translate/  pipeline code
scripts/                command-line tools
configs/                example settings
data/                   small versioned fixtures
tests/                  test fixtures
```

Do not commit model files, large datasets, generated outputs, credentials, or machine-specific paths.
