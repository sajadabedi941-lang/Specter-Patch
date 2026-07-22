#Requires -Version 5.0
<#
.SYNOPSIS
  Verify an installed Specter patch against SYNC_MANIFEST.sha256
#>
[CmdletBinding()]
param([string]$GameRoot = "")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PatchRoot = $PSScriptRoot
$ManifestPath = Join-Path $PatchRoot "SYNC_MANIFEST.sha256"

function Test-LooksLikeGameRoot([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
  foreach ($m in @("Data","Art","Data.zip","generals.exe","GeneralsZH.exe","SpecterPatch_InstallState")) {
    if (Test-Path -LiteralPath (Join-Path $Path $m)) { return $true }
  }
  return $false
}

if (-not $GameRoot) {
  $parent = Split-Path -Parent $PatchRoot
  if (Test-LooksLikeGameRoot $parent) { $GameRoot = $parent }
}
if (-not $GameRoot) {
  $GameRoot = (Read-Host "Game root").Trim().Trim('"')
}
$GameRoot = (Resolve-Path -LiteralPath $GameRoot).Path
Write-Host "Game root: $GameRoot"
Write-Host "Manifest : $ManifestPath"

$fail = 0
$pass = 0
Get-Content -LiteralPath $ManifestPath -Encoding UTF8 | ForEach-Object {
  $line = $_.Trim()
  if (-not $line -or $line.StartsWith("#")) { return }
  if ($line -notmatch '^([0-9a-fA-F]{64})\s{2}(.+)$') { return }
  $hash = $Matches[1].ToLowerInvariant()
  $rel  = ($Matches[2] -replace '/', '\').Trim()
  if ($rel -notmatch '^(?i)(Data|Art)\\') { return }
  $path = Join-Path $GameRoot $rel
  if (-not (Test-Path -LiteralPath $path)) {
    Write-Host "MISSING $rel" -ForegroundColor Red
    $fail++
    return
  }
  $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $hash) {
    Write-Host "HASH_MISMATCH $rel" -ForegroundColor Red
    $fail++
  } else {
    $pass++
  }
}

Write-Host ""
Write-Host ("Matched: {0}  Failed: {1}" -f $pass, $fail)
if ($fail -eq 0) { Write-Host "VERIFY PASS" -ForegroundColor Green; exit 0 }
Write-Host "VERIFY FAIL" -ForegroundColor Red
exit 1
