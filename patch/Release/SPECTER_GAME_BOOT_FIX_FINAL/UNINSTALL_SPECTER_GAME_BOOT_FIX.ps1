<#
.SYNOPSIS
  Restore newest Specter_GAME_BOOT_FIX_BACKUP over Data\INI\Object\Specter
#>
param(
  [Parameter(Mandatory = $false)][string]$GameRoot,
  [Parameter(Mandatory = $false)][string]$ScriptDir
)
$ErrorActionPreference = "Stop"
function Test-SpecterRoot([string]$root) {
  if (-not $root) { return $false }
  return (Test-Path -LiteralPath (Join-Path $root "Data\INI\Object\Specter"))
}
function Find-GameRoot([string]$start) {
  $cands = @(); if ($start) { $cands += $start }
  $cur = $start
  for ($i = 0; $i -lt 8; $i++) {
    if (-not $cur) { break }
    $par = Split-Path -Parent $cur
    if ($par -and $par -ne $cur) { $cands += $par; $cur = $par } else { break }
  }
  foreach ($c in $cands) { if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') } }
  return $null
}
if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot } else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) { throw "GameRoot not found." }
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
$bakRoot = Join-Path $GameRoot "Specter_GAME_BOOT_FIX_BACKUP"
if (-not (Test-Path -LiteralPath $bakRoot)) { throw "No Specter_GAME_BOOT_FIX_BACKUP folder." }
$dirs = @(Get-ChildItem -LiteralPath $bakRoot -Directory | Sort-Object Name -Descending)
if ($dirs.Count -eq 0) { throw "Backup folder empty." }
$latest = $dirs[0].FullName
Write-Host ("Restoring from: " + $latest)
$n = 0
foreach ($f in @(Get-ChildItem -LiteralPath $latest -Recurse -Filter *.ini -File)) {
  $rel = $f.FullName.Substring($latest.Length).TrimStart('\', '/')
  $dest = Join-Path $Specter $rel
  [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
  Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
  $n++; Write-Host ("  RESTORED: " + $rel)
}
Write-Host ("Restored $n files.")
exit 0
