param(
    [Parameter(Mandatory = $true)] [string[]]$Source,
    [string]$RawDir = "data",
    [string]$OutDir = "outputs",
    [string]$ModelDir = "models/opus-mt-tc-big-en-pt-ct2",
    [string]$SourceSpm = "models/opus-mt-tc-big-en-pt-ct2/source.spm",
    [string]$TargetSpm = "models/opus-mt-tc-big-en-pt-ct2/target.spm",
    [int]$BatchTokens = 1024,
    [int]$Beam = 1,
    [ValidateSet("auto", "cuda", "cpu")]
    [string]$Device = "auto",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
$baseArguments = @(
    "scripts/translate_anchors.py",
    "--src"; $Source,
    "--raw-dir"; $RawDir,
    "--out-dir"; $OutDir,
    "--model-dir"; $ModelDir,
    "--source-spm"; $SourceSpm,
    "--target-spm"; $TargetSpm,
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
if ($Resume) { $baseArguments += "--resume" }

function Invoke-Translation([string]$TargetDevice, [string]$ComputeType) {
    $arguments = @($baseArguments + "--device" + $TargetDevice + "--compute-type" + $ComputeType)
    python @arguments
    return $LASTEXITCODE
}

if ($Device -eq "cpu") {
    exit (Invoke-Translation "cpu" "int8")
}

$exitCode = Invoke-Translation "cuda" "int8_float16"
if ($exitCode -eq 0 -or $Device -eq "cuda") {
    exit $exitCode
}

Write-Warning "CUDA translation failed (exit code $exitCode). Retrying with CPU int8."
exit (Invoke-Translation "cpu" "int8")
