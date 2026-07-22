#Requires -Version 5.0
<#
.SYNOPSIS
  Specter Ultimate Warfare Expansion — Safe Patch Installer (Phases A–I)

.DESCRIPTION
  Merges patch\Data and patch\Art into a Generals Zero Hour / Specter game root.
  - Backs up any overwritten originals before replace
  - Never touches .big / Data.zip / _SPEC_* / payload.rar archives
  - Verifies installed files against SYNC_MANIFEST.sha256
  - Writes PATCH_INSTALLED.txt and a rollback manifest

.NOTES
  Compatible with Command & Conquer Generals Zero Hour Specter loose-file overlays.
  Multiplayer: every lobby client must install the same package (same SYNC_MANIFEST).
#>

[CmdletBinding()]
param(
  [string]$GameRoot = "",
  [switch]$Force,
  [switch]$SkipVerify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PatchRoot = $PSScriptRoot
if (-not $PatchRoot) { $PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }

$ManifestPath = Join-Path $PatchRoot "SYNC_MANIFEST.sha256"
$VersionPath  = Join-Path $PatchRoot "VERSION"
$DataSrc      = Join-Path $PatchRoot "Data"
$ArtSrc       = Join-Path $PatchRoot "Art"

$ProtectedNamePatterns = @(
  "*.big", "*.BIG",
  "Data.zip", "data.zip",
  "_SPEC_*",
  "Specter_Data*",
  "payload.rar", "Payload.rar"
)

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

function Test-IsProtectedPath([string]$RelativePath) {
  $name = Split-Path -Leaf $RelativePath
  foreach ($pat in $ProtectedNamePatterns) {
    if ($name -like $pat) { return $true }
  }
  # Also block archive folders commonly used by Specter
  if ($RelativePath -match '(?i)(^|\\)_SPEC_|\\Specter_Data|\\BIG\\') { return $true }
  return $false
}

function Test-LooksLikeGameRoot([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
  $markers = @(
    "generals.exe", "Generals.exe",
    "generalszh.exe", "generalsZH.exe", "GeneralsZH.exe",
    "Data.zip", "data.zip",
    "Art", "Data"
  )
  $hits = 0
  foreach ($m in $markers) {
    if (Test-Path -LiteralPath (Join-Path $Path $m)) { $hits++ }
  }
  # Specter often has Data.zip + Art + Data or exe
  return ($hits -ge 2)
}

function Find-GameRoot {
  param([string]$Hint)

  if ($Hint -and (Test-LooksLikeGameRoot $Hint)) { return (Resolve-Path -LiteralPath $Hint).Path }

  # 1) Installer lives in <GameRoot>\patch\
  $parent = Split-Path -Parent $PatchRoot
  if (Test-LooksLikeGameRoot $parent) { return $parent }

  # 2) Installer lives next to game (sibling patch folder already is PatchRoot; parent checked)
  # 3) Common install paths
  $candidates = @(
    "${env:ProgramFiles(x86)}\EA Games\Command & Conquer Generals Zero Hour",
    "${env:ProgramFiles}\EA Games\Command & Conquer Generals Zero Hour",
    "${env:ProgramFiles(x86)}\Command & Conquer Generals Zero Hour",
    "${env:ProgramFiles}\Command & Conquer Generals Zero Hour",
    "C:\Program Files (x86)\EA Games\Command & Conquer Generals Zero Hour",
    "C:\Program Files\EA Games\Command & Conquer Generals Zero Hour",
    "C:\Games\Command & Conquer Generals Zero Hour",
    "C:\Games\Specter",
    "D:\Games\Command & Conquer Generals Zero Hour",
    "D:\Games\Specter"
  )
  foreach ($c in $candidates) {
    if ($c -and (Test-LooksLikeGameRoot $c)) { return $c }
  }

  # 4) Registry (EA / Origin / retail)
  $regPaths = @(
    "HKLM:\SOFTWARE\WOW6432Node\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour",
    "HKLM:\SOFTWARE\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour",
    "HKCU:\SOFTWARE\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour"
  )
  foreach ($rp in $regPaths) {
    if (Test-Path -LiteralPath $rp) {
      try {
        $props = Get-ItemProperty -LiteralPath $rp -ErrorAction SilentlyContinue
        foreach ($key in @("InstallDir", "Install Path", "Path", "DisplayIcon")) {
          $val = $props.$key
          if ($val) {
            $dir = $val
            if ($dir -match '\.exe$') { $dir = Split-Path -Parent $dir }
            if (Test-LooksLikeGameRoot $dir) { return $dir }
          }
        }
      } catch {}
    }
  }

  return $null
}

function Prompt-GameRoot {
  Write-Host ""
  Write-Host "Could not auto-detect the Specter / Zero Hour game folder." -ForegroundColor Yellow
  Write-Host "Enter the full path to your game root (folder containing Data and/or Art),"
  Write-Host "or drag-drop the folder here and press Enter:"
  $inputPath = Read-Host "Game root"
  $inputPath = $inputPath.Trim().Trim('"')
  if (-not $inputPath) { throw "No game root provided." }
  if (-not (Test-LooksLikeGameRoot $inputPath)) {
    Write-WarnLine "Path does not look like a full game root. Continuing only if -Force was set."
    if (-not $Force) {
      $confirm = Read-Host "Use this path anyway? (Y/N)"
      if ($confirm -notmatch '^[Yy]') { throw "Installation cancelled." }
    }
  }
  return (Resolve-Path -LiteralPath $inputPath).Path
}

function Get-FileSha256([string]$FilePath) {
  $hash = Get-FileHash -LiteralPath $FilePath -Algorithm SHA256
  return $hash.Hash.ToLowerInvariant()
}

function Read-SyncManifest([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "SYNC_MANIFEST.sha256 missing at $Path"
  }
  $entries = @()
  $package = $null
  Get-Content -LiteralPath $Path -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
      if ($line -match 'PackageSHA256\s+([0-9a-fA-F]{64})') {
        $package = $Matches[1].ToLowerInvariant()
      }
      return
    }
    # format: <sha256>  <relative/path>
    if ($line -match '^([0-9a-fA-F]{64})\s{2}(.+)$') {
      $entries += [pscustomobject]@{
        Hash = $Matches[1].ToLowerInvariant()
        Rel  = ($Matches[2] -replace '/', '\').Trim()
      }
    }
  }
  return @{ PackageSHA256 = $package; Entries = $entries }
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Get-RelativePath([string]$Base, [string]$Full) {
  $baseFull = (Resolve-Path -LiteralPath $Base).Path.TrimEnd('\')
  $fullPath = (Resolve-Path -LiteralPath $Full).Path
  if ($fullPath.StartsWith($baseFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $fullPath.Substring($baseFull.Length).TrimStart('\')
  }
  return $null
}

# -------------------- main --------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host " Specter Ultimate Warfare Expansion — Safe Installer" -ForegroundColor White
Write-Host " Activates Phase A–I patch content (land/air/missile/drone/AD)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White
Write-Host ""

if (-not (Test-Path -LiteralPath $DataSrc -PathType Container)) {
  throw "Missing patch Data folder: $DataSrc"
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
  throw "Missing SYNC_MANIFEST.sha256 — refuse to install unverified package."
}

Write-Step "Detecting game root..."
$resolvedRoot = Find-GameRoot -Hint $GameRoot
if (-not $resolvedRoot) {
  $resolvedRoot = Prompt-GameRoot
}
Write-Ok "Game root: $resolvedRoot"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $resolvedRoot ("{0}\{1}" -f $BackupRootName, $timestamp)
$stateDir   = Join-Path $resolvedRoot $StateDirName
Ensure-Dir $backupRoot
Ensure-Dir $stateDir

$installedListPath = Join-Path $stateDir "installed_files.txt"
$backupMapPath     = Join-Path $stateDir "backup_map.txt"
$activeStampPath   = Join-Path $stateDir "ACTIVE_BACKUP.txt"
$reportPath        = Join-Path $resolvedRoot "PATCH_INSTALLED.txt"
$reportPathPatch   = Join-Path $PatchRoot "PATCH_INSTALLED.txt"

# Collect source files (Data + Art only)
Write-Step "Scanning patch package..."
$sources = @()
foreach ($pair in @(
  @{ Src = $DataSrc; DestRootName = "Data"; Prefix = "Data" },
  @{ Src = $ArtSrc;  DestRootName = "Art";  Prefix = "Art" }
)) {
  if (-not (Test-Path -LiteralPath $pair.Src -PathType Container)) {
    Write-WarnLine "Optional source missing: $($pair.Src)"
    continue
  }
  Get-ChildItem -LiteralPath $pair.Src -Recurse -File | ForEach-Object {
    $relUnder = Get-RelativePath -Base $pair.Src -Full $_.FullName
    $relPackage = Join-Path $pair.Prefix $relUnder
    if (Test-IsProtectedPath $relPackage) {
      Write-WarnLine "Skipping protected path in package: $relPackage"
      return
    }
    $dest = Join-Path (Join-Path $resolvedRoot $pair.DestRootName) $relUnder
    $sources += [pscustomobject]@{
      Source      = $_.FullName
      Dest        = $dest
      RelPackage  = $relPackage
      RelDest     = (Join-Path $pair.DestRootName $relUnder)
      Size        = $_.Length
    }
  }
}

$total = $sources.Count
if ($total -lt 1) { throw "No installable files found under patch\Data / patch\Art." }
Write-Ok ("Found {0} files to merge" -f $total)

# Precompute source hashes for progress / optional precheck
Write-Step "Installing with backup (never touches archives)..."
$installed = New-Object System.Collections.Generic.List[string]
$backedUp  = New-Object System.Collections.Generic.List[string]
$errors    = New-Object System.Collections.Generic.List[string]
$i = 0

foreach ($item in $sources) {
  $i++
  $pct = [math]::Round(($i / $total) * 100, 1)
  Write-Progress -Activity "Installing Specter Patch (Phases A–I)" -Status ("{0}%  {1}" -f $pct, $item.RelDest) -PercentComplete ([math]::Min(100, $pct))

  try {
    $destDir = Split-Path -Parent $item.Dest
    Ensure-Dir $destDir

    if (Test-Path -LiteralPath $item.Dest -PathType Leaf) {
      # Backup original before overwrite
      $backupTarget = Join-Path $backupRoot $item.RelDest
      Ensure-Dir (Split-Path -Parent $backupTarget)
      Copy-Item -LiteralPath $item.Dest -Destination $backupTarget -Force
      $backedUp.Add(("{0}|{1}" -f $item.RelDest, $backupTarget)) | Out-Null
    }

    Copy-Item -LiteralPath $item.Source -Destination $item.Dest -Force
    $installed.Add($item.RelDest) | Out-Null
  }
  catch {
    $errors.Add(("{0} :: {1}" -f $item.RelDest, $_.Exception.Message)) | Out-Null
    Write-ErrLine ("Failed: {0}" -f $item.RelDest)
  }
}
Write-Progress -Activity "Installing Specter Patch (Phases A–I)" -Completed

# Persist install state for uninstall
$installed | Set-Content -LiteralPath $installedListPath -Encoding UTF8
$backedUp  | Set-Content -LiteralPath $backupMapPath -Encoding UTF8
$backupRoot | Set-Content -LiteralPath $activeStampPath -Encoding UTF8
# Also keep a copy inside this backup snapshot
Copy-Item -LiteralPath $installedListPath -Destination (Join-Path $backupRoot "installed_files.txt") -Force
Copy-Item -LiteralPath $backupMapPath -Destination (Join-Path $backupRoot "backup_map.txt") -Force

Write-Ok ("Installed/merged: {0}" -f $installed.Count)
Write-Ok ("Originals backed up: {0} -> {1}" -f $backedUp.Count, $backupRoot)
if ($errors.Count -gt 0) {
  Write-WarnLine ("{0} file errors during copy" -f $errors.Count)
}

# Verify against SYNC_MANIFEST
$verifyOk = $true
$verifyFail = New-Object System.Collections.Generic.List[string]
$verifySkip = New-Object System.Collections.Generic.List[string]
$verifyPass = 0

if (-not $SkipVerify) {
  Write-Step "Verifying installed files against SYNC_MANIFEST.sha256..."
  $manifest = Read-SyncManifest -Path $ManifestPath
  $vTotal = $manifest.Entries.Count
  $vi = 0
  foreach ($entry in $manifest.Entries) {
    $vi++
    $pct = [math]::Round(($vi / [math]::Max(1, $vTotal)) * 100, 1)
    Write-Progress -Activity "Verifying SYNC_MANIFEST" -Status ("{0}%  {1}" -f $pct, $entry.Rel) -PercentComplete ([math]::Min(100, $pct))

    # Only verify Data/ and Art/ entries that we install
    if ($entry.Rel -notmatch '^(?i)(Data|Art)\\') {
      $verifySkip.Add($entry.Rel) | Out-Null
      continue
    }
    if (Test-IsProtectedPath $entry.Rel) {
      $verifySkip.Add($entry.Rel) | Out-Null
      continue
    }

    $target = Join-Path $resolvedRoot $entry.Rel
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
      # Also accept files still only in package path if merge skipped — count fail
      $verifyFail.Add(("MISSING {0}" -f $entry.Rel)) | Out-Null
      $verifyOk = $false
      continue
    }
    $actual = Get-FileSha256 $target
    if ($actual -ne $entry.Hash) {
      $verifyFail.Add(("HASH_MISMATCH {0}" -f $entry.Rel)) | Out-Null
      $verifyOk = $false
    } else {
      $verifyPass++
    }
  }
  Write-Progress -Activity "Verifying SYNC_MANIFEST" -Completed

  if ($verifyOk) {
    Write-Ok ("Manifest verify PASS ({0} files matched)" -f $verifyPass)
  } else {
    Write-ErrLine ("Manifest verify FAIL ({0} issues)" -f $verifyFail.Count)
    $verifyFail | Select-Object -First 20 | ForEach-Object { Write-ErrLine $_ }
  }
} else {
  Write-WarnLine "Verification skipped (-SkipVerify)."
}

# Version text
$versionText = if (Test-Path -LiteralPath $VersionPath) {
  (Get-Content -LiteralPath $VersionPath -Raw).Trim()
} else { "Specter Ultimate Warfare Expansion (Phases A–I)" }

$pkgHash = $null
try { $pkgHash = (Read-SyncManifest -Path $ManifestPath).PackageSHA256 } catch {}

$report = @"
Specter Ultimate Warfare Expansion — PATCH INSTALLED
====================================================
InstalledAtUTC     : $((Get-Date).ToUniversalTime().ToString("o"))
PatchRoot          : $PatchRoot
GameRoot           : $resolvedRoot
Version            : $versionText
PackageSHA256      : $pkgHash
PhasesActivated    : A B C D F F+ G H I
FilesMerged        : $($installed.Count)
OriginalsBackedUp  : $($backedUp.Count)
BackupFolder       : $backupRoot
InstallStateDir    : $stateDir
ManifestVerify     : $(if ($SkipVerify) { "SKIPPED" } elseif ($verifyOk) { "PASS" } else { "FAIL" })
ManifestMatched    : $verifyPass
ManifestIssues     : $($verifyFail.Count)
CopyErrors         : $($errors.Count)

Safety rules honored
--------------------
- Originals backed up before overwrite
- No .big / Data.zip / _SPEC_* / Specter_Data* / payload.rar modifications
- Loose Data\ and Art\ overlay merge (Specter / ZH compatible)
- Multiplayer: all lobby clients must use this same package + SYNC_MANIFEST.sha256

Rollback
--------
Run Uninstall_SpecterPatch.bat from the patch folder to restore backed-up originals
and remove newly added overlay files tracked by this install.

Issues (first 50)
-----------------
$(($verifyFail + $errors | Select-Object -First 50) -join [Environment]::NewLine)
"@

$report | Set-Content -LiteralPath $reportPath -Encoding UTF8
$report | Set-Content -LiteralPath $reportPathPatch -Encoding UTF8
Write-Ok "Wrote $reportPath"
Write-Ok "Wrote $reportPathPatch"

Write-Host ""
if ($errors.Count -eq 0 -and ($SkipVerify -or $verifyOk)) {
  Write-Host "INSTALLATION SUCCESSFUL — Phase A–I content activated." -ForegroundColor Green
  Write-Host "Use Uninstall_SpecterPatch.bat to roll back." -ForegroundColor Green
  exit 0
} elseif ($errors.Count -eq 0 -and -not $verifyOk) {
  Write-Host "INSTALLATION COMPLETED WITH VERIFY WARNINGS." -ForegroundColor Yellow
  Write-Host "Files were merged and originals backed up. Review PATCH_INSTALLED.txt." -ForegroundColor Yellow
  exit 2
} else {
  Write-Host "INSTALLATION COMPLETED WITH ERRORS." -ForegroundColor Red
  exit 1
}
