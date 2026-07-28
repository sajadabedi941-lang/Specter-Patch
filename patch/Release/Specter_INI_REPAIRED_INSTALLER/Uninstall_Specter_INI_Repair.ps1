param(
  [Parameter(Mandatory = $false)]
  [Alias("GameRoot", "Path")]
  [string]$LiteralPath,

  [Parameter(Mandatory = $false)]
  [string]$ScriptDir
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

Write-Host "[1/3] Detecting game folder..."

$GameRoot = $null
if ($LiteralPath) {
  $GameRoot = $LiteralPath.Trim().TrimEnd('\', '/')
} else {
  $GameRoot = Find-GameRoot $ScriptDir
}
if (-not $GameRoot -or -not (Test-GameRoot $GameRoot)) {
  try {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select Generals Zero Hour / Specter game folder"
    $dialog.ShowNewFolderButton = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
      throw "Game folder selection cancelled."
    }
    $GameRoot = $dialog.SelectedPath.TrimEnd('\', '/')
  } catch {
    if ($_.Exception.Message -match 'cancelled') { throw }
    throw "Could not detect game folder."
  }
}
if (-not (Test-GameRoot $GameRoot)) {
  throw "Invalid game folder (missing Data\INI\Object\Specter\): $GameRoot"
}

Write-Host ("        Game root: " + $GameRoot)
$specterRoot = Join-Path $GameRoot "Data\INI\Object\Specter"

Write-Host "[2/3] Locating backup..."
$stamp = Join-Path $GameRoot "Specter_INI_REPAIR_INSTALL.stamp"
$backupRoot = $null
if (Test-Path -LiteralPath $stamp) {
  foreach ($ln in (Get-Content -LiteralPath $stamp -Encoding UTF8)) {
    if ($ln.StartsWith("Backup=")) { $backupRoot = $ln.Substring(7).Trim() }
  }
}
if (-not $backupRoot -or -not (Test-Path -LiteralPath $backupRoot)) {
  $bakParent = Join-Path $GameRoot "Specter_INI_Backup"
  if (Test-Path -LiteralPath $bakParent) {
    $latest = Get-ChildItem -LiteralPath $bakParent -Directory -Filter "INI_REPAIR_*" |
      Sort-Object Name -Descending |
      Select-Object -First 1
    if ($latest) { $backupRoot = $latest.FullName }
  }
}
if (-not $backupRoot -or -not (Test-Path -LiteralPath $backupRoot)) {
  throw "No Specter_INI_Backup\INI_REPAIR_* folder found. Nothing to restore."
}
Write-Host ("        Backup: " + $backupRoot)

# Prefer files listed in install manifest; else restore everything under backup
$rels = @()
$manifest = Join-Path $backupRoot "InstallManifest.txt"
if (Test-Path -LiteralPath $manifest) {
  $inFiles = $false
  foreach ($ln in (Get-Content -LiteralPath $manifest -Encoding UTF8)) {
    if ($ln -eq 'FILES') { $inFiles = $true; continue }
    if (-not $inFiles) { continue }
    if ($ln -match '^(FilesInstalled|FilesBackedUp|FilesSkipped)=') { continue }
    if ($ln.Trim()) { $rels += ($ln.Trim() -replace '/', '\') }
  }
}
if ($rels.Count -lt 1) {
  Get-ChildItem -LiteralPath $backupRoot -Recurse -File -Filter *.ini | ForEach-Object {
    $rel = $_.FullName.Substring($backupRoot.Length).TrimStart('\', '/')
    if ($rel -and ($rel -ne 'PlacementMap.txt')) { $rels += $rel }
  }
}

Write-Host "[3/3] Restoring backup..."
$restored = 0
$removed = 0
foreach ($rel in $rels) {
  $bak = Join-Path $backupRoot $rel
  $dst = Join-Path $specterRoot $rel
  if (Test-Path -LiteralPath $bak) {
    Ensure-Directory (Split-Path -Parent $dst)
    Copy-Item -LiteralPath $bak -Destination $dst -Force
    $restored++
    Write-Host ("  [RESTORE] " + $rel)
  } elseif (Test-Path -LiteralPath $dst) {
    # Installed as new file with no prior backup copy — remove patch-only file
    Remove-Item -LiteralPath $dst -Force
    $removed++
    Write-Host ("  [REMOVE]  " + $rel + " (was new)")
  }
}

if (Test-Path -LiteralPath $stamp) {
  Remove-Item -LiteralPath $stamp -Force
}

Write-Host ""
Write-Host ("Restored: " + $restored)
Write-Host ("Removed : " + $removed)
Write-Host ("Backup  : " + $backupRoot)
