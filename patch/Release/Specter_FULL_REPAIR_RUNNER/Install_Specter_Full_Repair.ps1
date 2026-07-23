param(
  [Parameter(Mandatory = $true)]
  [string]$GameRoot,
  [Parameter(Mandatory = $true)]
  [string]$ScriptDir
)

$ErrorActionPreference = "Stop"

$GameRoot = $GameRoot.Trim().TrimEnd('\', '/')
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

# Payload is Specter_FULL_REPAIR_Data\ (same layout as Data\) so it does not
# collide with the live game Data\ folder when this package sits in GameRoot.
$srcData = Join-Path $ScriptDir "Specter_FULL_REPAIR_Data"
if (-not (Test-Path -LiteralPath $srcData)) {
  # Fallback for older layouts
  $srcData = Join-Path $ScriptDir "Data"
}
$dstData = Join-Path $GameRoot "Data"
$manifest = Join-Path $ScriptDir "RepairManifest.txt"
$blacklist = Join-Path $ScriptDir "FlatIniBlacklist.txt"

if (-not (Test-Path -LiteralPath $dstData)) {
  throw "Data folder not found: $dstData"
}
if (-not (Test-Path -LiteralPath $srcData)) {
  throw "Patch payload folder not found: Specter_FULL_REPAIR_Data" 
}
if (-not (Test-Path -LiteralPath $manifest)) {
  throw "RepairManifest.txt not found: $manifest"
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $GameRoot ("SpecterPatch_Backup\FULL_REPAIR_" + $ts)
New-Item -ItemType Directory -Force -LiteralPath $backupRoot | Out-Null

$stamp = Join-Path $GameRoot "Specter_FULL_REPAIR_INSTALL.stamp"
$lines = @(
  Get-Content -LiteralPath $manifest -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ }
)

$backed = 0
$copied = 0

foreach ($rel in $lines) {
  $relWin = $rel -replace "/", "\"
  $src = Join-Path $srcData $relWin
  $dst = Join-Path $dstData $relWin

  if (-not (Test-Path -LiteralPath $src)) {
    Write-Host "[WARN] Missing source: $relWin"
    continue
  }

  # Never copy a file onto itself (can happen if payload was wrongly merged into Data)
  $srcFull = [System.IO.Path]::GetFullPath($src)
  $dstFull = [System.IO.Path]::GetFullPath($dst)
  if ($srcFull -eq $dstFull) {
    Write-Host "[WARN] Source and destination are the same file, skipping copy: $relWin"
    continue
  }

  if (Test-Path -LiteralPath $dst) {
    $bak = Join-Path $backupRoot $relWin
    $bakParent = Split-Path -Parent $bak
    if (-not (Test-Path -LiteralPath $bakParent)) {
      New-Item -ItemType Directory -Force -LiteralPath $bakParent | Out-Null
    }
    Copy-Item -LiteralPath $dst -Destination $bak -Force
    $backed++
  }

  $dstParent = Split-Path -Parent $dst
  if (-not (Test-Path -LiteralPath $dstParent)) {
    New-Item -ItemType Directory -Force -LiteralPath $dstParent | Out-Null
  }
  Copy-Item -LiteralPath $src -Destination $dst -Force
  $copied++
}

$iniRoot = Join-Path $dstData "INI"
$removed = 0

if (Test-Path -LiteralPath $blacklist) {
  $names = @(
    Get-Content -LiteralPath $blacklist -Encoding UTF8 |
      ForEach-Object { $_.Trim() } |
      Where-Object { $_ }
  )
  foreach ($name in $names) {
    $flat = Join-Path $iniRoot $name
    if (Test-Path -LiteralPath $flat) {
      $flatBak = Join-Path $backupRoot ("FLAT_INI__" + $name)
      Copy-Item -LiteralPath $flat -Destination $flatBak -Force
      Remove-Item -LiteralPath $flat -Force
      $removed++
      Write-Host "  Removed flat Data\INI\$name"
    }
  }
}

foreach ($dirName in @("Economy", "New folder")) {
  $d = Join-Path $iniRoot $dirName
  if (Test-Path -LiteralPath $d) {
    $bak = Join-Path $backupRoot ($dirName -replace " ", "_")
    Copy-Item -LiteralPath $d -Destination $bak -Recurse -Force
    Remove-Item -LiteralPath $d -Recurse -Force
    Write-Host "  Removed Data\INI\$dirName"
  }
}

$stampText = @(
  "Specter FULL INI Repair install stamp",
  ("GameRoot=" + $GameRoot),
  ("Backup=" + $backupRoot),
  ("InstalledUtc=" + (Get-Date).ToUniversalTime().ToString("o")),
  ("FilesCopied=" + $copied),
  ("FilesBackedUp=" + $backed),
  ("FlatRemoved=" + $removed)
) -join [Environment]::NewLine

Set-Content -LiteralPath $stamp -Value $stampText -Encoding UTF8
Copy-Item -LiteralPath $manifest -Destination (Join-Path $backupRoot "RepairManifest.txt") -Force

Write-Host ("Backed up: " + $backed + " file(s)")
Write-Host ("Installed: " + $copied + " file(s)")
Write-Host ("Flat purged: " + $removed + " file(s)")
Write-Host ("Backup folder: " + $backupRoot)
