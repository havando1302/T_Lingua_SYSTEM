param(
    [string]$AudioDir = "",
    [string]$Manifest = "",
    [string]$Cases = "",
    [string]$Baseline = "",
    [string]$OutputDir = "",
    [ValidateSet("auto", "cpu", "cuda")][string]$Device = "auto",
    [ValidateSet("auto", "cpu", "cuda")][string]$TtsDevice = "auto",
    [int]$Limit = 0,
    [int]$LimitPerLanguage = 0,
    [switch]$SaveTts,
    [switch]$NoXlsx,
    [switch]$ValidateOnly,
    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "backend\venv\Scripts\python.exe"
$tool = Join-Path $PSScriptRoot "run_audio_pipeline_evaluation.py"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Không tìm thấy Python của dự án: $python"
}

$arguments = @($tool, "--device", $Device, "--tts-device", $TtsDevice)
if ($AudioDir) { $arguments += @("--audio-dir", $AudioDir) }
if ($Manifest) { $arguments += @("--manifest", $Manifest) }
if ($Cases) { $arguments += @("--cases", $Cases) }
if ($Baseline) { $arguments += @("--baseline", $Baseline) }
if ($OutputDir) { $arguments += @("--output-dir", $OutputDir) }
if ($Limit -gt 0) { $arguments += @("--limit", $Limit) }
if ($LimitPerLanguage -gt 0) { $arguments += @("--limit-per-language", $LimitPerLanguage) }
if ($SaveTts) { $arguments += "--save-tts" }
if ($NoXlsx) { $arguments += "--no-xlsx" }
if ($ValidateOnly) { $arguments += "--validate-only" }
if ($Overwrite) { $arguments += "--overwrite" }

Push-Location $root
try {
    & $python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
