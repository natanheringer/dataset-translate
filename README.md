# dataset-translate

[English](#dataset-translate) | [Português (Brasil)](#português-brasil)

Batch translation for datasets that contain natural language and code.

The pipeline translates only the natural-language parts and keeps protected code unchanged. It processes JSONL files incrementally, writes progress files, and can resume an interrupted run.

## Requirements

- Python 3.11 or newer
- A converted CTranslate2 model
- CUDA is optional; CPU mode is supported

## Install

Run this from the repository directory:

```bash
python -m pip install -r requirements.txt
```

On Windows, run the same command in PowerShell from the repository directory:

```powershell
python -m pip install -r requirements.txt
```

## Prepare the Model

This project uses the [Helsinki-NLP/opus-mt-tc-big-en-pt model](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-pt).
See the [Hugging Face model catalog](https://huggingface.co/models?search=opus-mt-tc-big-en-pt)
to browse related models and conversions.

Download and convert the model once:

```bash
python scripts/prepare_model.py \
  --raw-dir models/opus-mt-tc-big-en-pt \
  --output-dir models/opus-mt-tc-big-en-pt-ct2
```

On Windows, use the PowerShell wrapper:

```powershell
.\scripts\prepare_model.ps1
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

Use the PowerShell wrapper from the repository directory:

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

---

## Português (Brasil)

Tradução em lote para datasets que contêm linguagem natural e código.

O pipeline traduz apenas as partes em linguagem natural e mantém o código protegido sem alterações. Ele processa arquivos JSONL de forma incremental, grava arquivos de progresso e pode continuar uma execução interrompida.

### Requisitos

- Python 3.11 ou mais recente
- Um modelo convertido para CTranslate2
- CUDA é opcional; o modo CPU é compatível

### Instalação

Execute a partir do diretório do repositório:

```bash
python -m pip install -r requirements.txt
```

No Windows, execute o mesmo comando no PowerShell a partir do diretório do repositório:

```powershell
python -m pip install -r requirements.txt
```

### Preparar o modelo

Este projeto usa o [modelo Helsinki-NLP/opus-mt-tc-big-en-pt](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-pt).
Consulte o [catálogo de modelos do Hugging Face](https://huggingface.co/models?search=opus-mt-tc-big-en-pt)
para encontrar modelos relacionados e conversões.

Baixe e converta o modelo uma vez:

```bash
python scripts/prepare_model.py \
  --raw-dir models/opus-mt-tc-big-en-pt \
  --output-dir models/opus-mt-tc-big-en-pt-ct2
```

No Windows, use o wrapper do PowerShell:

```powershell
.\scripts\prepare_model.ps1
```

Os arquivos do modelo são ignorados pelo Git. Cada máquina precisa preparar ou receber seus próprios arquivos de modelo.

### Traduzir um dataset

Coloque a entrada em `data/<name>.jsonl`. Depois execute:

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

Os registros aceitos, rejeitados e os dados de progresso são gravados em `outputs/<name>/`.

O repositório inclui `data/example.jsonl` e `data/example_templates.jsonl` para testes. Para usar o exemplo maior, substitua `<name>` por `example_templates`.

### Windows

Use o wrapper do PowerShell a partir do diretório do repositório:

```powershell
.\scripts\translate_windows.ps1 `
  -Source <name> `
  -RawDir data `
  -OutDir outputs\<name> `
  -Resume
```

Por padrão, `-Device auto` tenta usar CUDA primeiro e repete com CPU caso CUDA ou cuBLAS não estejam disponíveis. Para usar CPU diretamente:

```powershell
.\scripts\translate_windows.ps1 `
  -Device cpu `
  -Source <name> `
  -RawDir data `
  -OutDir outputs\<name> `
  -Resume
```

Use `-Device cuda` para exigir CUDA. Os valores padrão do Windows são conservadores para GPUs com pouca memória. Reduza `-BatchTokens` caso a GPU fique sem memória.

### Auditar o código

Depois da tradução, compare a origem com a saída traduzida:

```bash
python scripts/audit_code_integrity.py \
  --source data/<name>.jsonl \
  --translated outputs/<name>/<name>_pt.jsonl
```

Datasets que contêm código devem ter zero falhas na auditoria antes de serem usados no treinamento.

### Estrutura

```text
src/dataset_translate/  código do pipeline
scripts/                ferramentas de linha de comando
configs/                configurações de exemplo
data/                   fixtures pequenos versionados
tests/                  fixtures de teste
```
