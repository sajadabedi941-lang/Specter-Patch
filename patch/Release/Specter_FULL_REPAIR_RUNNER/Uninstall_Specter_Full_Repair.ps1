param(
  [Parameter(Mandatory = $true)]
  [string]$GameRoot,
  [Parameter(Mandatory = $true)]
  [string]$ScriptDir
)

$ErrorActionPreference = "Stop"

$GameRoot = $GameRoot.Trim().TrimEnd('\', '/')
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

$dstData = Join-Path $GameRoot "Data"
$stamp = Join-Path $GameRoot "Specter_FULL_REPAIR_INSTALL.stamp"

if (-not (Test-Path -LiteralPath $dstData)) {
  throw "Data folder not found: $dstData"
}

$backupRoot = $null
if (Test-Path -LiteralPath $stamp) {
  foreach ($ln in (Get-Content -LiteralPath $stamp -Encoding UTF8)) {
    if ($ln.StartsWith("Backup=")) {
      $backupRoot = $ln.Substring(7).Trim()
    }
  }
}

if (-not $backupRoot -or -not (Test-Path -LiteralPath $backupRoot)) {
  $bakParent = Join-Path $GameRoot "SpecterPatch_Backup"
  if (Test-Path -LiteralPath $bakParent) {
    $latest = Get-ChildItem -LiteralPath $bakParent -Directory -Filter "FULL_REPAIR_*" |
      Sort-Object Name -Descending |
      Select-Object -First 1
    if ($latest) { $backupRoot = $latest.FullName }
  }
}

$manifestCandidates = @()
if ($backupRoot) {
  $manifestCandidates += (Join-Path $backupRoot "RepairManifest.txt")
}
$manifestCandidates += (Join-Path $ScriptDir "RepairManifest.txt")

$manifest = $null
foreach ($m in $manifestCandidates) {
  if (Test-Path -LiteralPath $m) {
    $manifest = $m
    break
  }
}
if (-not $manifest) {
  throw "RepairManifest.txt not found. Cannot uninstall safely."
}

$lines = @(
  Get-Content -LiteralPath $manifest -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ }
)

$restored = 0
$removed = 0

foreach ($rel in $lines) {
  $relWin = $rel -replace "/", "\"
  $dst = Join-Path $dstData $relWin
  $bak = $null
  if ($backupRoot) {
    $bak = Join-Path $backupRoot $relWin
  }

  if ($bak -and (Test-Path -LiteralPath $bak)) {
    $dstParent = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dstParent)) {
      New-Item -ItemType Directory -Force -LiteralPath $dstParent | Out-Null
    }
    Copy-Item -LiteralPath $bak -Destination $dst -Force
    $restored++
  }
  elseif (Test-Path -LiteralPath $dst) {
    Remove-Item -LiteralPath $dst -Force
    $removed++
    Write-Host "  Removed patch-only file: Data\$relWin"
  }
}

if ($backupRoot) {
  Get-ChildItem -LiteralPath $backupRoot -File -Filter "FLAT_INI__*" -ErrorAction SilentlyContinue | ForEach-Object {
    $name = $_.Name.Substring("FLAT_INI__".Length)
    $flat = Join-Path (Join-Path $dstData "INI") $name
    Copy-Item -LiteralPath $_.FullName -Destination $flat -Force
    $restored++
    Write-Host "  Restored flat Data\INI\$name"
  }

  foreach ($dirName in @("Economy", "New folder")) {
    $src = Join-Path $backupRoot ($dirName -replace " ", "_")
    $dst = Join-Path (Join-Path $dstData "INI") $dirName
    if (Test-Path -LiteralPath $src) {
      if (Test-Path -LiteralPath $dst) {
        Remove-Item -LiteralPath $dst -Recurse -Force
      }
      Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
      Write-Host "  Restored Data\INI\$dirName"
    }
  }
}

if (Test-Path -LiteralPath $stamp) {
  Remove-Item -LiteralPath $stamp -Force
}

Write-Host ("Restored: " + $restored + " file(s)")
Write-Host ("Removed patch-only: " + $removed + " file(s)")
if ($backupRoot) {
  Write-Host ("Used backup: " + $backupRoot)
}
