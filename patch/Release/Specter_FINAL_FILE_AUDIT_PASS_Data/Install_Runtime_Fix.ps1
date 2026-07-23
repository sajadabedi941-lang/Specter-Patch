param(
  [string]$GameRoot = ""
)
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host ""
Write-Host "============================================================"
Write-Host " Specter FINAL FILE AUDIT PASS - Installer"
Write-Host " Purge flat Data\INI duplicates + merge corrected paths"
Write-Host "============================================================"
Write-Host ""

if (-not $GameRoot) {
  $GameRoot = Read-Host "Enter GameRoot (folder containing Data\ and generals.exe)"
}
$GameRoot = $GameRoot.Trim().Trim('"')
if (-not $GameRoot) { throw "GameRoot not set" }
$DataIni = Join-Path $GameRoot "Data\INI"
$Specter = Join-Path $DataIni "Object\Specter"
if (-not (Test-Path -LiteralPath $DataIni)) {
  Write-Host "[ERROR] Wrong folder selected. Data\ not found in: $GameRoot"
  throw "Not found: $DataIni"
}

Write-Host "[OK] Game detected: $GameRoot"

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $GameRoot "SpecterPatch_Backup\RuntimeCrashFixV2_$ts"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Write-Host "[OK] Backup created: $Backup"
Write-Host ""
Write-Host "Patch installing..."
Write-Host ""

$blacklist = @{}
$blacklistPath = Join-Path $ScriptDir "FlatIniBlacklist.txt"
if (Test-Path -LiteralPath $blacklistPath) {
  Get-Content -LiteralPath $blacklistPath | ForEach-Object {
    $n = $_.Trim()
    if ($n) { $blacklist[$n.ToLowerInvariant()] = $true }
  }
}

$specterLeaf = @{}
$specterObj = @{}
if (Test-Path -LiteralPath $Specter) {
  Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File | ForEach-Object {
    $specterLeaf[$_.Name.ToLowerInvariant()] = $true
    try {
      $txt = [System.IO.File]::ReadAllText($_.FullName)
      foreach ($m in [regex]::Matches($txt, '(?m)^Object\s+(\S+)')) {
        $specterObj[$m.Groups[1].Value] = $true
      }
    } catch {}
  }
}
Write-Host ("Indexed Specter leaves={0} objects={1}" -f $specterLeaf.Count, $specterObj.Count)

function Backup-And-Delete([string]$path, [string]$reason) {
  if (-not (Test-Path -LiteralPath $path)) { return $false }
  $name = [System.IO.Path]::GetFileName($path)
  $dest = Join-Path $Backup $name
  if (Test-Path -LiteralPath $dest) {
    $dest = Join-Path $Backup ($name + "." + ([guid]::NewGuid().ToString("N").Substring(0,8)))
  }
  Copy-Item -LiteralPath $path -Destination $dest -Force
  Remove-Item -LiteralPath $path -Force
  Write-Host ("  REMOVED  {0}  ({1})" -f $name, $reason)
  return $true
}

Write-Host ""
Write-Host "[1/4] Purging flat Data\INI\*.ini Object dumps ..."
$removed = 0
$toolNames = @(
  "countrybalance.ini",
  "globalbuildlimits_specterpatch.ini",
  "commandbutton_runtimefix_russiar24.ini",
  "commandbutton_runtimefix_russias24.ini",
  "advancedairbaseaircraft_aab_global.ini"
)
Get-ChildItem -LiteralPath $DataIni -File -ErrorAction SilentlyContinue | ForEach-Object {
  $leaf = $_.Name
  $low = $leaf.ToLowerInvariant()
  $kill = $false
  $reason = ""

  if ($blacklist.ContainsKey($low) -or $specterLeaf.ContainsKey($low) -or ($toolNames -contains $low)) {
    $kill = $true
    $reason = "flat duplicate of Specter Object-tree / tool schema"
  } elseif ($low.EndsWith(".ini")) {
    try {
      $txt = [System.IO.File]::ReadAllText($_.FullName)
      if ($txt -match '(?m)^Object\s+') {
        foreach ($m in [regex]::Matches($txt, '(?m)^Object\s+(\S+)')) {
          $o = $m.Groups[1].Value
          if ($specterObj.ContainsKey($o)) {
            $kill = $true
            $reason = "defines Object $o already under Object\Specter"
            break
          }
        }
      }
    } catch {}
  }

  if ($kill) {
    if (Backup-And-Delete $_.FullName $reason) { $removed++ }
  }
}
Write-Host ("  Removed {0} flat file(s)." -f $removed)

Write-Host ""
Write-Host "[2/4] Removing Data\INI\Economy and Data\INI\New folder if present ..."
foreach ($dirName in @("Economy", "New folder")) {
  $d = Join-Path $DataIni $dirName
  if (Test-Path -LiteralPath $d) {
    $bak = Join-Path $Backup ($dirName -replace ' ', '_')
    Copy-Item -LiteralPath $d -Destination $bak -Recurse -Force
    Remove-Item -LiteralPath $d -Recurse -Force
    Write-Host ("  REMOVED Data\INI\{0}" -f $dirName)
  }
}

Write-Host ""
Write-Host "[3/4] Merging corrected files into Object\Specter\ paths ..."
$pkgData = Join-Path $ScriptDir "Data"
$merged = 0
if (Test-Path -LiteralPath $pkgData) {
  Get-ChildItem -LiteralPath $pkgData -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($pkgData.Length).TrimStart('\', '/')
    $target = Join-Path (Join-Path $GameRoot "Data") $rel
    $parent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $parent)) {
      New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    if (Test-Path -LiteralPath $target) {
      $bakName = "merge_" + ($rel -replace '[\\/]', '__')
      Copy-Item -LiteralPath $target -Destination (Join-Path $Backup $bakName) -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    $merged++
  }
  Write-Host ("  Merged {0} file(s)." -f $merged)
} else {
  Write-Host "  WARNING: package Data\ missing (purge-only)."
}

Write-Host ""
Write-Host "[4/4] Final flat-root Object duplicate check ..."
$still = 0
Get-ChildItem -LiteralPath $DataIni -File -Filter *.ini -ErrorAction SilentlyContinue | ForEach-Object {
  $flatPath = $_.FullName
  $flatName = $_.Name
  try {
    $txt = [System.IO.File]::ReadAllText($flatPath)
    foreach ($m in [regex]::Matches($txt, '(?m)^Object\s+(\S+)')) {
      $o = $m.Groups[1].Value
      if ($specterObj.ContainsKey($o)) {
        Write-Host ("  FINAL PURGE {0} (Object {1})" -f $flatName, $o)
        if (Backup-And-Delete $flatPath ("final Object dup " + $o)) { $still++ }
        break
      }
    }
  } catch {}
}

# Specific named audits echo
Write-Host ""
Write-Host "Specific path checks (must exist under Object\Specter, NOT flat):"
$checks = @(
  "Object\Specter\Turkey Armed Forces\Wheeled\AbbasLauncher.ini",
  "Object\Specter\Turkey Armed Forces\Infantry\SpecialForces.ini",
  "Object\Specter\Turkey Armed Forces\Airforce\Turkey_Akinci.ini",
  "Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16Block70.ini",
  "Object\Specter\Turkey Armed Forces\Airforce\Turkey_TB2.ini",
  "Object\Specter\Turkey Armed Forces\Airforce\Turkey_Tu-22M3.ini",
  "Object\Specter\Turkey Armed Forces\Buildings\Turkey_CommandCenter.ini",
  "Object\Specter\Turkey Armed Forces\Turkey_WeaponObjects.ini",
  "Object\Specter\PatchSystems\AdvancedAirBase\Aircraft_AAB_Global.ini",
  "Object\Specter\PatchSystems\MilitaryHQ\MilitaryHQ_StockFactions.ini"
)
foreach ($c in $checks) {
  $p = Join-Path $DataIni $c
  $flat = Join-Path $DataIni ([System.IO.Path]::GetFileName($c))
  $ok = Test-Path -LiteralPath $p
  $flatBad = Test-Path -LiteralPath $flat
  if ($flatBad) {
    Backup-And-Delete $flat "specific audit flat copy"
    $flatBad = $false
  }
  Write-Host ("  {0}  specter={1}  flat={2}" -f ([System.IO.Path]::GetFileName($c)), $ok, $flatBad)
}

Write-Host ""
Write-Host "[OK] Installation completed."
Write-Host "     Backup kept at: $Backup"
Write-Host "     No SHA256 verification (by design)."
Write-Host "     Launch Generals Zero Hour / Specter now."
Write-Host ""
