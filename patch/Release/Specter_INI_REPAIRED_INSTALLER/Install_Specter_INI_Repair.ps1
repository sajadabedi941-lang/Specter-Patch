param(
  [Parameter(Mandatory = $false)]
  [Alias("GameRoot", "Path")]
  [string]$LiteralPath,

  [Parameter(Mandatory = $false)]
  [string]$ScriptDir,

  [Parameter(Mandatory = $false)]
  [string]$OverwriteMode
  # OverwriteMode: All | Skip | Ask  (Ask = prompt once for batch overwrite)
)

$ErrorActionPreference = "Stop"

function Ensure-Directory([string]$DirPath) {
  if (-not $DirPath) { return }
  [void][System.IO.Directory]::CreateDirectory($DirPath)
}

function Test-GameRoot([string]$path) {
  if (-not $path) { return $false }
  if (-not (Test-Path -LiteralPath $path)) { return $false }
  $specter = Join-Path $path "Data\INI\Object\Specter"
  return (Test-Path -LiteralPath $specter)
}

function Find-GameRoot([string]$startDir) {
  $candidates = @()
  if ($startDir) { $candidates += $startDir }
  $cursor = $startDir
  for ($i = 0; $i -lt 6; $i++) {
    if (-not $cursor) { break }
    $parent = Split-Path -Parent $cursor
    if ($parent -and ($parent -ne $cursor)) {
      $candidates += $parent
      $cursor = $parent
    } else { break }
  }
  foreach ($c in $candidates) {
    if (Test-GameRoot $c) { return $c.TrimEnd('\', '/') }
  }
  return $null
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

Write-Host "[1/4] Detecting game folder..."

$GameRoot = $null
if ($LiteralPath) {
  $GameRoot = $LiteralPath.Trim().TrimEnd('\', '/')
  if (-not (Test-GameRoot $GameRoot)) {
    throw "Game folder invalid (missing Data\INI\Object\Specter\): $GameRoot"
  }
} else {
  $GameRoot = Find-GameRoot $ScriptDir
}

if (-not $GameRoot) {
  try {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter\)"
    $dialog.ShowNewFolderButton = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
      throw "Game folder selection cancelled."
    }
    $GameRoot = $dialog.SelectedPath.TrimEnd('\', '/')
  } catch {
    if ($_.Exception.Message -match 'cancelled') { throw }
    throw "Could not detect game folder. Place this package inside the game folder and re-run."
  }
  if (-not (Test-GameRoot $GameRoot)) {
    throw "Selected folder is missing Data\INI\Object\Specter\: $GameRoot"
  }
}

Write-Host ("        Game root: " + $GameRoot)
$specterRoot = Join-Path $GameRoot "Data\INI\Object\Specter"
Write-Host ("        Specter:   " + $specterRoot)

$payloadDir = Join-Path $ScriptDir "Specter_INI_REPAIRED"
$mapFile = Join-Path $ScriptDir "PlacementMap.txt"
if (-not (Test-Path -LiteralPath $payloadDir)) {
  throw "Specter_INI_REPAIRED folder not found next to installer: $payloadDir"
}
if (-not (Test-Path -LiteralPath $mapFile)) {
  throw "PlacementMap.txt not found next to installer: $mapFile"
}

$placements = @()
Get-Content -LiteralPath $mapFile -Encoding UTF8 | ForEach-Object {
  $ln = $_.Trim()
  if (-not $ln -or $ln.StartsWith('#')) { return }
  $parts = $ln.Split('|', 2)
  if ($parts.Count -ne 2) { return }
  $placements += [pscustomobject]@{ Name = $parts[0].Trim(); Rel = ($parts[1].Trim() -replace '/', '\') }
}
if ($placements.Count -lt 1) { throw "PlacementMap.txt is empty." }

# Determine which targets already exist
$existing = @()
foreach ($p in $placements) {
  $dst = Join-Path $specterRoot $p.Rel
  if (Test-Path -LiteralPath $dst) { $existing += $p }
}

if (-not $OverwriteMode) {
  if ($existing.Count -gt 0) {
    Write-Host ""
    Write-Host ("Found " + $existing.Count + " existing file(s) that would be replaced.")
    Write-Host "Overwrite existing files? [Y]es / [N]o (skip existing) / [C]ancel"
    $ans = Read-Host "Choice"
    switch -Regex ($ans.Trim().ToUpperInvariant()) {
      '^(Y|YES)$' { $OverwriteMode = 'All' }
      '^(N|NO)$'  { $OverwriteMode = 'Skip' }
      default     { throw "Install cancelled by user." }
    }
  } else {
    $OverwriteMode = 'All'
  }
}

Write-Host ""
Write-Host "[2/4] Creating backup..."
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $GameRoot ("Specter_INI_Backup\INI_REPAIR_" + $ts)
Ensure-Directory $backupRoot
$backed = 0
$skipped = 0
$installed = 0
$missingSrc = 0

$manifestLines = @()
$manifestLines += "Specter INI Repair install stamp"
$manifestLines += ("GameRoot=" + $GameRoot)
$manifestLines += ("Backup=" + $backupRoot)
$manifestLines += ("InstalledUtc=" + (Get-Date).ToUniversalTime().ToString("o"))
$manifestLines += ("OverwriteMode=" + $OverwriteMode)
$manifestLines += "FILES"

Write-Host ""
Write-Host "[3/4] Installing repaired INI files..."

foreach ($p in $placements) {
  $src = Join-Path $payloadDir $p.Name
  $dst = Join-Path $specterRoot $p.Rel

  if (-not (Test-Path -LiteralPath $src)) {
    Write-Host ("  [WARN] Missing source: " + $p.Name)
    $missingSrc++
    continue
  }

  $exists = Test-Path -LiteralPath $dst
  if ($exists -and $OverwriteMode -eq 'Skip') {
    Write-Host ("  [SKIP] " + $p.Rel)
    $skipped++
    continue
  }

  if ($exists) {
    $bak = Join-Path $backupRoot $p.Rel
    Ensure-Directory (Split-Path -Parent $bak)
    Copy-Item -LiteralPath $dst -Destination $bak -Force
    $backed++
  }

  Ensure-Directory (Split-Path -Parent $dst)
  Copy-Item -LiteralPath $src -Destination $dst -Force
  $installed++
  $manifestLines += ($p.Rel)
  Write-Host ("  [OK]   " + $p.Rel)
}

# Save map + manifest into backup for uninstall
Copy-Item -LiteralPath $mapFile -Destination (Join-Path $backupRoot "PlacementMap.txt") -Force
$stamp = Join-Path $GameRoot "Specter_INI_REPAIR_INSTALL.stamp"
$manifestLines += ("FilesInstalled=" + $installed)
$manifestLines += ("FilesBackedUp=" + $backed)
$manifestLines += ("FilesSkipped=" + $skipped)
Set-Content -LiteralPath $stamp -Value ($manifestLines -join [Environment]::NewLine) -Encoding UTF8
Set-Content -LiteralPath (Join-Path $backupRoot "InstallManifest.txt") -Value ($manifestLines -join [Environment]::NewLine) -Encoding UTF8

Write-Host ""
Write-Host "[4/4] Verifying installation..."
$verified = 0
$verifyFail = 0
foreach ($p in $placements) {
  $dst = Join-Path $specterRoot $p.Rel
  $src = Join-Path $payloadDir $p.Name
  if (-not (Test-Path -LiteralPath $src)) { continue }
  if ($OverwriteMode -eq 'Skip' -and -not (Test-Path -LiteralPath $dst)) { continue }
  if (Test-Path -LiteralPath $dst) {
    $verified++
  } else {
    Write-Host ("  [FAIL] missing after install: " + $p.Rel)
    $verifyFail++
  }
}

Write-Host ""
Write-Host ("Backed up : " + $backed)
Write-Host ("Installed : " + $installed)
Write-Host ("Skipped   : " + $skipped)
Write-Host ("Verified  : " + $verified)
Write-Host ("Backup    : " + $backupRoot)

if ($verifyFail -gt 0) {
  throw ("Verification failed for " + $verifyFail + " file(s).")
}
if ($installed -lt 1 -and $skipped -lt 1) {
  throw "Nothing was installed."
}
