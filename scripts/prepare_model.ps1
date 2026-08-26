param(
    [string]$RawDir = "models/opus-mt-tc-big-en-pt",
    [string]$OutputDir = "models/opus-mt-tc-big-en-pt-ct2",
    [string]$Quantization = "int8_float16"
)

$ErrorActionPreference = "Stop"
python scripts/prepare_model.py `
    --raw-dir $RawDir `
    --output-dir $OutputDir `
    --quantization $Quantization
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
