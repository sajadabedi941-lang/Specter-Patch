#Requires -Version 5.0
<#
.SYNOPSIS
  Specter Ultimate Warfare Expansion — Safe Rollback / Uninstall

.DESCRIPTION
  Restores originals from SpecterPatch_Backup and removes tracked overlay files.
  Never deletes .big / Data.zip / _SPEC_* / Specter_Data* / payload.rar.
#>

[CmdletBinding()]
param(
  [string]$GameRoot = "",
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PatchRoot = $PSScriptRoot
if (-not $PatchRoot) { $PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }

$StateDirName = "SpecterPatch_InstallState"
$BackupRootName = "SpecterPatch_Backup"

function Write-Step([string]$Message) {
  Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message) -ForegroundColor Cyan
}
function Write-Ok([string]$Message) {
  Write-Host ("  OK  {0}" -f $Message) -ForegroundColor Green
}
function Write-WarnLine([string]$Message) {
  Write-Host ("  WARN {0}" -f $Message) -ForegroundColor Yellow
}
function Write-ErrLine([string]$Message) {
  Write-Host ("  ERR  {0}" -f $Message) -ForegroundColor Red
}

function Test-LooksLikeGameRoot([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
  $hits = 0
  foreach ($m in @("generals.exe","Generals.exe","generalszh.exe","GeneralsZH.exe","Data.zip","Art","Data",$StateDirName,$BackupRootName)) {
    if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ }
  }
  return ($hits -ge 1)
}

function Find-GameRoot([string]$Hint) {
  if ($Hint -and (Test-Path -LiteralPath $Hint)) { return (Resolve-Path -LiteralPath $Hint).Path }
  $parent = Split-Path -Parent $PatchRoot
  if (Test-LooksLikeGameRoot $parent) { return $parent }
  return $null
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host " Specter Patch — Rollback / Uninstall" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White
Write-Host ""

$resolvedRoot = Find-GameRoot $GameRoot
if (-not $resolvedRoot) {
  Write-Host "Enter game root path (folder that contains SpecterPatch_InstallState):"
  $inputPath = (Read-Host "Game root").Trim().Trim('"')
  if (-not $inputPath) { throw "No game root provided." }
  $resolvedRoot = (Resolve-Path -LiteralPath $inputPath).Path
}
Write-Ok "Game root: $resolvedRoot"

$stateDir = Join-Path $resolvedRoot $StateDirName
$activeStamp = Join-Path $stateDir "ACTIVE_BACKUP.txt"
$installedList = Join-Path $stateDir "installed_files.txt"
$backupMap = Join-Path $stateDir "backup_map.txt"

if (-not (Test-Path -LiteralPath $stateDir)) {
  throw "No install state found at $stateDir — nothing to uninstall (or wrong game root)."
}

$backupRoot = $null
if (Test-Path -LiteralPath $activeStamp) {
  $backupRoot = (Get-Content -LiteralPath $activeStamp -Raw).Trim()
}
if (-not $backupRoot -or -not (Test-Path -LiteralPath $backupRoot)) {
  # Fall back to newest backup folder
  $backupParent = Join-Path $resolvedRoot $BackupRootName
  if (Test-Path -LiteralPath $backupParent) {
    $newest = Get-ChildItem -LiteralPath $backupParent -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($newest) { $backupRoot = $newest.FullName }
  }
}
if (-not $backupRoot) {
  Write-WarnLine "No backup folder found. Will only remove tracked overlay files (cannot restore priors)."
} else {
  Write-Ok "Backup folder: $backupRoot"
  if (-not (Test-Path -LiteralPath $installedList)) {
    $alt = Join-Path $backupRoot "installed_files.txt"
    if (Test-Path -LiteralPath $alt) { $installedList = $alt }
  }
  if (-not (Test-Path -LiteralPath $backupMap)) {
    $alt = Join-Path $backupRoot "backup_map.txt"
    if (Test-Path -LiteralPath $alt) { $backupMap = $alt }
  }
}

if (-not $Force) {
  $confirm = Read-Host "Restore originals and remove patch overlay files? (Y/N)"
  if ($confirm -notmatch '^[Yy]') { throw "Uninstall cancelled." }
}

# 1) Restore backed-up originals
$restored = 0
if (Test-Path -LiteralPath $backupMap) {
  Write-Step "Restoring backed-up original files..."
  Get-Content -LiteralPath $backupMap -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    $parts = $line.Split('|', 2)
    if ($parts.Count -lt 2) { return }
    $relDest = $parts[0]
    $backupFile = $parts[1]
    $dest = Join-Path $resolvedRoot $relDest
    if (Test-Path -LiteralPath $backupFile -PathType Leaf) {
      $destDir = Split-Path -Parent $dest
      if (-not (Test-Path -LiteralPath $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
      }
      Copy-Item -LiteralPath $backupFile -Destination $dest -Force
      $restored++
    } else {
      Write-WarnLine "Backup missing for $relDest"
    }
  }
  Write-Ok ("Restored {0} original file(s)" -f $restored)
}

# 2) Remove overlay files that were NOT in the backup map (newly added by patch)
$removed = 0
$backedRel = @{}
if (Test-Path -LiteralPath $backupMap) {
  Get-Content -LiteralPath $backupMap -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    $rel = ($line.Split('|', 2)[0])
    $backedRel[$rel] = $true
  }
}

if (Test-Path -LiteralPath $installedList) {
  Write-Step "Removing patch-added overlay files..."
  $lines = Get-Content -LiteralPath $installedList -Encoding UTF8
  $total = @($lines).Count
  $i = 0
  foreach ($rel in $lines) {
    $i++
    $rel = $rel.Trim()
    if (-not $rel) { continue }
    if ($backedRel.ContainsKey($rel)) {
      # Already restored from backup — leave restored original in place
      continue
    }
    $pct = [math]::Round(($i / [math]::Max(1,$total)) * 100, 1)
    Write-Progress -Activity "Uninstalling Specter Patch" -Status ("{0}%  {1}" -f $pct, $rel) -PercentComplete ([math]::Min(100, $pct))
    $target = Join-Path $resolvedRoot $rel
    # Safety: never delete archives
    $leaf = Split-Path -Leaf $target
    if ($leaf -match '(?i)\.big$' -or $leaf -match '(?i)^Data\.zip$' -or $leaf -like '_SPEC_*' -or $leaf -like 'Specter_Data*' -or $leaf -match '(?i)payload\.rar') {
      Write-WarnLine "Refusing to delete protected archive: $rel"
      continue
    }
    if (Test-Path -LiteralPath $target -PathType Leaf) {
      Remove-Item -LiteralPath $target -Force
      $removed++
    }
  }
  Write-Progress -Activity "Uninstalling Specter Patch" -Completed
  Write-Ok ("Removed {0} patch-only overlay file(s)" -f $removed)
}

# 3) Clean install markers
$reportGame = Join-Path $resolvedRoot "PATCH_INSTALLED.txt"
$reportPatch = Join-Path $PatchRoot "PATCH_INSTALLED.txt"
foreach ($rp in @($reportGame, $reportPatch)) {
  if (Test-Path -LiteralPath $rp) {
    Remove-Item -LiteralPath $rp -Force
    Write-Ok "Removed $rp"
  }
}

# Keep backup folders for safety, but clear active state pointer
if (Test-Path -LiteralPath $activeStamp) {
  Remove-Item -LiteralPath $activeStamp -Force
}
$uninstallReport = Join-Path $stateDir ("UNINSTALLED_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
@"
Specter Patch uninstall completed
UTC: $((Get-Date).ToUniversalTime().ToString("o"))
GameRoot: $resolvedRoot
RestoredFromBackup: $restored
RemovedPatchOnlyFiles: $removed
BackupFolderKept: $backupRoot
"@ | Set-Content -LiteralPath $uninstallReport -Encoding UTF8

Write-Host ""
Write-Host "ROLLBACK COMPLETE." -ForegroundColor Green
Write-Host "Backup folder was kept at: $backupRoot" -ForegroundColor Green
exit 0
