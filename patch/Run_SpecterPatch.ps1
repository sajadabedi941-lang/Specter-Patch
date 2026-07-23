# Specter Ultimate Warfare Expansion — one-click patch activator
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Write-Host "Specter Ultimate Warfare Expansion — activating patch overlay..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'Install_SpecterPatch.ps1') @args
exit $LASTEXITCODE
