<#
.SYNOPSIS
  Auto-repair Generals ZH parse defects under Data\INI\Object\Specter.
  Replaces broken files in-place, mirrors repaired copies into Fixed\, writes Repair_Report.txt.
#>
param(
  [Parameter(Mandatory = $false)]
  [Alias("LiteralPath", "Path")]
  [string]$GameRoot,

  [Parameter(Mandatory = $false)]
  [string]$ScriptDir,

  [Parameter(Mandatory = $false)]
  [string]$BackupRoot,

  [Parameter(Mandatory = $false)]
  [string]$ReportPath,

  [Parameter(Mandatory = $false)]
  [string]$FixedOutDir,

  [Parameter(Mandatory = $false)]
  [switch]$ApplyFixedPayload
)

$ErrorActionPreference = "Stop"

function Ensure-Directory([string]$DirPath) {
  if (-not $DirPath) { return }
  [void][System.IO.Directory]::CreateDirectory($DirPath)
}

function Test-SpecterRoot([string]$root) {
  if (-not $root) { return $false }
  return (Test-Path -LiteralPath (Join-Path $root "Data\INI\Object\Specter"))
}

function Find-GameRoot([string]$start) {
  $cands = New-Object System.Collections.Generic.List[string]
  if ($start) { $cands.Add($start) | Out-Null }
  $cur = $start
  for ($i = 0; $i -lt 8; $i++) {
    if (-not $cur) { break }
    $par = Split-Path -Parent $cur
    if ($par -and $par -ne $cur) { $cands.Add($par) | Out-Null; $cur = $par } else { break }
  }
  foreach ($c in $cands) {
    if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') }
  }
  return $null
}

function Repair-IniText([string]$text, [ref]$FixList) {
  $fixes = New-Object System.Collections.Generic.List[string]
  if ($text.StartsWith([char]0xFEFF)) {
    $text = $text.TrimStart([char]0xFEFF)
    $fixes.Add("Removed UTF-8 BOM") | Out-Null
  }
  $text = $text -replace "`r`n", "`n" -replace "`r", "`n"
  $lines = $text -split "`n", -1
  $out = New-Object System.Collections.Generic.List[string]

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    $n = $i + 1

    if ($ln -match '^(?<ind>[ \t]*)End[ \t]*;(?<rest>.*)$') {
      $ind = $Matches['ind']
      $rest = $Matches['rest'].Trim()
      $out.Add(($ind + "End")) | Out-Null
      if ($rest) {
        if (-not $rest.StartsWith(";")) { $rest = "; " + $rest }
        $out.Add(($ind + $rest)) | Out-Null
      }
      $fixes.Add(("L{0}: End; trailing comment -> End + comment line" -f $n)) | Out-Null
      continue
    }

    if ($ln -cmatch '^(?<ind>[ \t]*)END(?<sp>[ \t]*)$') {
      $out.Add(($Matches['ind'] + "End" + $Matches['sp'])) | Out-Null
      $fixes.Add(("L{0}: END -> End" -f $n)) | Out-Null
      continue
    }

    if ($ln -match '^(?<ind>[ \t]*)Scale(?<ws>[ \t]+)(?!=)(?<rest>.*)$') {
      $code = ($ln -split ";", 2)[0]
      if ($code -notmatch '=') {
        $out.Add(($Matches['ind'] + "Scale = " + $Matches['rest'].TrimStart())) | Out-Null
        $fixes.Add(("L{0}: bare Scale -> Scale =" -f $n)) | Out-Null
        continue
      }
    }

    if ($ln -match '^(?<ind>[ \t]*BuildCompletion\s*=\s*)PLACE_ON_GROUND(?<rest>\b.*)$') {
      $out.Add(($Matches['ind'] + "PLACED_BY_PLAYER" + $Matches['rest'])) | Out-Null
      $fixes.Add(("L{0}: PLACE_ON_GROUND -> PLACED_BY_PLAYER" -f $n)) | Out-Null
      continue
    }

    $out.Add($ln) | Out-Null
  }

  $text2 = [string]::Join("`n", $out)
  if (-not $text2.EndsWith("`n")) {
    $text2 += "`n"
    $fixes.Add("Added trailing newline") | Out-Null
  }
  $FixList.Value = $fixes
  return $text2
}

function Test-CriticalRemaining([string]$text) {
  $bad = New-Object System.Collections.Generic.List[string]
  foreach ($ln in ($text -split "`n")) {
    $s = $ln.Trim()
    if ($s -match '(?i)^End[ \t]*;') { $bad.Add("END_SEMI") | Out-Null }
    if ($s -cmatch '^END\s*$') { $bad.Add("UPPER_END") | Out-Null }
    $code = ($ln -split ";", 2)[0]
    if ($s -match '(?i)^Scale[ \t]+' -and $code -notmatch '=') { $bad.Add("BARE_SCALE") | Out-Null }
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') { $bad.Add("PLACE_ON_GROUND") | Out-Null }
    if ($code -match '[{}]') { $bad.Add("BRACE") | Out-Null }
  }
  return @($bad)
}

function Normalize-Compare([string]$text) {
  $t = $text.TrimStart([char]0xFEFF) -replace "`r`n", "`n" -replace "`r", "`n"
  if (-not $t.EndsWith("`n")) { $t += "`n" }
  return $t
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

Write-Host ""
Write-Host "============================================================"
Write-Host " AUTO_REPAIR_ENGINE — Specter INI repair + replace"
Write-Host "============================================================"
Write-Host ""

if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found (need Data\INI\Object\Specter\)."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"

if (-not $BackupRoot) {
  $ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $BackupRoot = Join-Path $GameRoot ("Specter_ENGINE_REPAIR_BACKUP\" + $ts)
}
Ensure-Directory $BackupRoot

if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "Repair_Report.txt"
}
if (-not $FixedOutDir) {
  $FixedOutDir = Join-Path $ScriptDir "Fixed"
}
Ensure-Directory $FixedOutDir

$report = New-Object System.Collections.Generic.List[string]
$report.Add("SPECTER ENGINE REPAIR REPORT") | Out-Null
$report.Add("============================") | Out-Null
$report.Add(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o"))) | Out-Null
$report.Add(("GameRoot     : " + $GameRoot)) | Out-Null
$report.Add(("Specter      : " + $Specter)) | Out-Null
$report.Add(("Backup       : " + $BackupRoot)) | Out-Null
$report.Add(("FixedOut     : " + $FixedOutDir)) | Out-Null
$report.Add("") | Out-Null

$replaced = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$payloadApplied = New-Object System.Collections.Generic.List[string]

# -----------------------------------------------------------------
# Optional: deploy pre-bundled Fixed\ payload into the game first
# -----------------------------------------------------------------
if ($ApplyFixedPayload) {
  Write-Host "[A] Applying Fixed\ payload into game Specter tree..."
  $payloadFiles = @()
  if (Test-Path -LiteralPath $FixedOutDir) {
    $payloadFiles = @(Get-ChildItem -LiteralPath $FixedOutDir -Recurse -Filter *.ini -File)
  }
  foreach ($pf in $payloadFiles) {
    $rel = $pf.FullName.Substring($FixedOutDir.Length).TrimStart('\', '/')
    $dest = Join-Path $Specter $rel
    $destDir = Split-Path -Parent $dest
    Ensure-Directory $destDir
    if (Test-Path -LiteralPath $dest) {
      $bak = Join-Path $BackupRoot $rel
      Ensure-Directory (Split-Path -Parent $bak)
      if (-not (Test-Path -LiteralPath $bak)) {
        Copy-Item -LiteralPath $dest -Destination $bak -Force
      }
    }
    Copy-Item -LiteralPath $pf.FullName -Destination $dest -Force
    $payloadApplied.Add($rel) | Out-Null
    Write-Host ("     REPLACED: " + $rel)
  }
  Write-Host ("     Payload files applied: " + $payloadApplied.Count)
  Write-Host ""
}

Write-Host ("[B] Scanning + repairing under: " + $Specter)
$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File -ErrorAction Stop)
$report.Add(("Scanned      : " + $files.Count + " INI files")) | Out-Null
Write-Host ("     Found " + $files.Count + " INI files")

$idx = 0
foreach ($f in $files) {
  $idx++
  if (($idx % 200) -eq 0 -or $idx -eq $files.Count) {
    Write-Host ("     Progress: $idx / $($files.Count)")
  }
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $critBefore = Test-CriticalRemaining $text
  $fixes = $null
  $newText = Repair-IniText $text ([ref]$fixes)
  $critAfter = Test-CriticalRemaining $newText
  $changed = ((Normalize-Compare $text) -ne $newText)

  if ($critAfter.Count -gt 0) {
    $skipped.Add([pscustomobject]@{
      File = $rel
      Reason = ("Still critical after auto-repair: " + ($critAfter -join ","))
    }) | Out-Null
    continue
  }

  # Only replace real files that were broken / need hygiene after failing critical check
  if ($critBefore.Count -eq 0 -and -not $changed) { continue }
  if ($critBefore.Count -eq 0 -and $changed) {
    # hygiene-only (BOM/newline) — skip unless it had critical issues
    # Still allow if End;/etc were fixed (critBefore would be >0)
    continue
  }
  if (-not $changed) {
    $skipped.Add([pscustomobject]@{
      File = $rel
      Reason = "Verification failed but no safe automatic fix available"
    }) | Out-Null
    continue
  }

  # Backup then REPLACE in game
  $bakPath = Join-Path $BackupRoot $rel
  Ensure-Directory (Split-Path -Parent $bakPath)
  if (-not (Test-Path -LiteralPath $bakPath)) {
    Copy-Item -LiteralPath $f.FullName -Destination $bakPath -Force
  }
  [System.IO.File]::WriteAllText($f.FullName, $newText, [System.Text.UTF8Encoding]::new($false))

  # Mirror into Fixed\
  $fixedPath = Join-Path $FixedOutDir $rel
  Ensure-Directory (Split-Path -Parent $fixedPath)
  [System.IO.File]::WriteAllText($fixedPath, $newText, [System.Text.UTF8Encoding]::new($false))

  $replaced.Add([pscustomobject]@{
    File = $rel
    Errors = ($critBefore -join ",")
    Fixes = ($fixes -join " | ")
  }) | Out-Null
  Write-Host ("     REPAIRED+REPLACED: " + $rel)
}

Write-Host ""
Write-Host "[C] Final verification..."
$verifyFail = New-Object System.Collections.Generic.List[string]
$vIdx = 0
foreach ($f in $files) {
  $vIdx++
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $crit = Test-CriticalRemaining $text
  if ($crit.Count -gt 0) { $verifyFail.Add($rel) | Out-Null }
}
$verdict = if ($verifyFail.Count -eq 0) { "PASS" } else { "FAIL" }
Write-Host ("     Critical remaining: " + $verifyFail.Count + "  VERDICT: " + $verdict)

$known = @(
  "British Armed Forces\Airforce\Britain_F35B.ini",
  "Turkey Armed Forces\Turkey_WeaponObjects.ini",
  "Israel Defense Forces\Buildings\Israel_CommandCenter.ini",
  "Israel Defense Forces\Buildings\Israel_MilitaryHQ.ini"
)
$report.Add("") | Out-Null
$report.Add("KNOWN TARGETS") | Out-Null
$report.Add("-------------") | Out-Null
foreach ($k in $known) {
  $kp = Join-Path $Specter $k
  if (-not (Test-Path -LiteralPath $kp)) {
    $report.Add("  NOT FOUND  $k") | Out-Null
  } else {
    $c = Test-CriticalRemaining ([System.IO.File]::ReadAllText($kp))
    $st = if ($c.Count -eq 0) { "OK" } else { "FAIL (" + ($c -join ",") + ")" }
    $report.Add("  $st  $k") | Out-Null
  }
}

$report.Add("") | Out-Null
$report.Add("FIXED PAYLOAD APPLIED") | Out-Null
$report.Add("---------------------") | Out-Null
if ($payloadApplied.Count -eq 0) {
  $report.Add("  (none / skipped)") | Out-Null
} else {
  foreach ($p in $payloadApplied) { $report.Add("  REPLACED: $p") | Out-Null }
}

$report.Add("") | Out-Null
$report.Add("REPAIRED + REPLACED FILES") | Out-Null
$report.Add("-------------------------") | Out-Null
if ($replaced.Count -eq 0) {
  $report.Add("  (none additional — payload and/or tree already clean)") | Out-Null
} else {
  foreach ($r in $replaced) {
    $report.Add("FILE: $($r.File)") | Out-Null
    $report.Add("ERROR: $($r.Errors)") | Out-Null
    $report.Add("FIX: $($r.Fixes)") | Out-Null
    $report.Add("ACTION: Backed up + replaced in game + wrote Fixed\") | Out-Null
    $report.Add("") | Out-Null
  }
}

$report.Add("SKIPPED FILES") | Out-Null
$report.Add("-------------") | Out-Null
if ($skipped.Count -eq 0) {
  $report.Add("  (none)") | Out-Null
} else {
  foreach ($s in $skipped) {
    $report.Add("FILE: $($s.File)") | Out-Null
    $report.Add("REASON: $($s.Reason)") | Out-Null
    $report.Add("") | Out-Null
  }
}

$report.Add("") | Out-Null
$report.Add("SUMMARY") | Out-Null
$report.Add("-------") | Out-Null
$report.Add(("PayloadApplied : " + $payloadApplied.Count)) | Out-Null
$report.Add(("RepairedReplace: " + $replaced.Count)) | Out-Null
$report.Add(("Skipped        : " + $skipped.Count)) | Out-Null
$report.Add(("CriticalRemain : " + $verifyFail.Count)) | Out-Null
$report.Add(("VERDICT        : " + $verdict)) | Out-Null

if ($verifyFail.Count -gt 0) {
  $report.Add("") | Out-Null
  $report.Add("Still failing:") | Out-Null
  foreach ($vf in $verifyFail) { $report.Add("  - $vf") | Out-Null }
}

[System.IO.File]::WriteAllText($ReportPath, (($report -join [Environment]::NewLine) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
Write-Host ("Report: " + $ReportPath)
Write-Host ("Replaced=$($replaced.Count) Payload=$($payloadApplied.Count) Skipped=$($skipped.Count) Verdict=$verdict")

if ($verdict -ne "PASS") { exit 2 } else { exit 0 }
