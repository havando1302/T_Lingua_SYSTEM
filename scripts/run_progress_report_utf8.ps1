$ErrorActionPreference = "Stop"
$sourcePath = Join-Path $PSScriptRoot "generate_progress_report_docx.ps1"
try {
    $sourceText = Get-Content -Raw -Encoding UTF8 -LiteralPath $sourcePath
    Invoke-Expression $sourceText
}
catch {
    Write-Output ($_.Exception.ToString())
    Write-Output $_.InvocationInfo.PositionMessage
    Write-Output $_.ScriptStackTrace
    exit 1
}
