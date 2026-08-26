param(
    [Parameter(Mandatory = $true)] [string[]]$Source,
    [string]$RawDir = "data",
    [string]$OutDir = "outputs",
    [string]$ModelDir = "models/opus-mt-tc-big-en-pt-ct2",
    [string]$SourceSpm = "models/opus-mt-tc-big-en-pt-ct2/source.spm",
    [string]$TargetSpm = "models/opus-mt-tc-big-en-pt-ct2/target.spm",
    [int]$BatchTokens = 1024,
    [int]$Beam = 1,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
$arguments = @(
    "scripts/translate_anchors.py",
    "--src"; $Source,
    "--raw-dir"; $RawDir,
    "--out-dir"; $OutDir,
    "--model-dir"; $ModelDir,
    "--source-spm"; $SourceSpm,
    "--target-spm"; $TargetSpm,
    "--compute-type"; "int8_float16",
    "--batch-tokens"; $BatchTokens,
    "--max-batch-items"; "128",
    "--inflight"; "1",
    "--inter-threads"; "1",
    "--max-queued-batches"; "2",
    "--beam"; $Beam,
    "--max-decoding-length"; "256",
    "--max-decoding-ratio"; "3.0",
    "--tokenizer-threads"; "2",
    "--extract-code"
)
if ($Resume) { $arguments += "--resume" }
python @arguments
exit $LASTEXITCODE
