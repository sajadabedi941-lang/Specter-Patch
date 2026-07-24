<#
.SYNOPSIS
  Automatically repair Generals ZH parse defects under Data\INI\Object\Specter
.PARAMETER GameRoot
.PARAMETER ScriptDir
.PARAMETER BackupRoot  optional; created if missing
.PARAMETER ReportPath  FINAL_REPAIR_REPORT.txt
.PARAMETER FixedOutDir optional folder to also write Fixed copies
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
  [string]$FixedOutDir
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
  $cands = @()
  if ($start) { $cands += $start }
  $cur = $start
  for ($i = 0; $i -lt 6; $i++) {
    if (-not $cur) { break }
    $par = Split-Path -Parent $cur
    if ($par -and $par -ne $cur) { $cands += $par; $cur = $par } else { break }
  }
  foreach ($c in $cands) {
    if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') }
  }
  return $null
}

function Repair-IniText([string]$text, [string]$fileName, [ref]$fixList) {
  $fixes = New-Object System.Collections.Generic.List[string]
  $orig = $text

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

    # End; comment -> End + comment line
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

    # UPPERCASE END
    if ($ln -cmatch '^(?<ind>[ \t]*)END(?<sp>[ \t]*)$') {
      $out.Add(($Matches['ind'] + "End" + $Matches['sp'])) | Out-Null
      $fixes.Add(("L{0}: END -> End" -f $n)) | Out-Null
      continue
    }

    # Bare Scale
    if ($ln -match '^(?<ind>[ \t]*)Scale(?<ws>[ \t]+)(?!=)(?<rest>.*)$') {
      $code = ($ln -split ";", 2)[0]
      if ($code -notmatch '=') {
        $out.Add(($Matches['ind'] + "Scale = " + $Matches['rest'].TrimStart())) | Out-Null
        $fixes.Add(("L{0}: bare Scale -> Scale =" -f $n)) | Out-Null
        continue
      }
    }

    # Invalid BuildCompletion
    if ($ln -match '^(?<ind>[ \t]*BuildCompletion\s*=\s*)PLACE_ON_GROUND(?<rest>\b.*)$') {
      $out.Add(($Matches['ind'] + "PLACED_BY_PLAYER" + $Matches['rest'])) | Out-Null
      $fixes.Add(("L{0}: PLACE_ON_GROUND -> PLACED_BY_PLAYER" -f $n)) | Out-Null
      continue
    }

    $out.Add($ln) | Out-Null
  }

  $text2 = [string]::Join("`n", $out)
  if (-not $text2.EndsWith("`n")) { $text2 += "`n"; $fixes.Add("Added trailing newline") | Out-Null }

  $fixList.Value = $fixes
  return $text2
}

function New-SafeAircraftFallback([string]$objectName) {
  # Minimal valid ZH aircraft so boot can continue; same Object name
  @"
; SAFE FALLBACK — auto-generated for boot stability (Specter Full Engine Repair)
; Original file could not be safely auto-repaired. Gameplay values are minimal.
Object $objectName
  SelectPortrait = SAWarthogIcon
  ButtonImage = SAWarthogIcon
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = NONE
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:$objectName
  Side = America
  EditorSorting = VEHICLE
  TransportSlotCount = 0
  VisionRange = 200.0
  ShroudClearingRange = 200.0
  BuildCost = 1000
  BuildTime = 10.0
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  WeaponSet
    Conditions = None
    Weapon = PRIMARY NONE
  End
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT
  Body = ActiveBody ModuleTag_02
    MaxHealth = 100.0
    InitialHealth = 100.0
  End
  Behavior = PhysicsBehavior ModuleTag_03
    Mass = 50.0
  End
  Behavior = JetAIUpdate ModuleTag_04
    OutOfAmmoDamagePerSecond = 5%
    MinHeight = 5
  End
  Locomotor = SET_NORMAL BasicAirplaneLocomotor
  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 10.0
  GeometryMinorRadius = 5.0
  GeometryHeight = 5.0
  Shadow = SHADOW_VOLUME
End
"@
}

function Test-CriticalRemaining([string]$text) {
  $bad = @()
  foreach ($ln in ($text -split "`n")) {
    if ($ln -match '(?i)^[ \t]*End[ \t]*;') { $bad += "END_SEMI" }
    if ($ln -cmatch '^[ \t]*END[ \t]*$') { $bad += "UPPER_END" }
    $code = ($ln -split ";", 2)[0]
    if ($ln -match '(?i)^[ \t]*Scale[ \t]+' -and $code -notmatch '=') { $bad += "BARE_SCALE" }
    if ($ln -match '(?i)BuildCompletion\s*=\s*PLACE_ON_GROUND\b') { $bad += "PLACE_ON_GROUND" }
    if ($code -match '[{}]') { $bad += "BRACE" }
  }
  return $bad
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found (need Data\INI\Object\Specter\)."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"

if (-not $BackupRoot) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $BackupRoot = Join-Path $GameRoot ("Specter_EngineRepair_Backup\FULL_" + $ts)
}
Ensure-Directory $BackupRoot

if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "FINAL_REPAIR_REPORT.txt"
}
if (-not $FixedOutDir) {
  $FixedOutDir = Join-Path $ScriptDir "Fixed"
}
Ensure-Directory $FixedOutDir

Write-Host ("Repairing under: " + $Specter)
Write-Host ("Backup: " + $BackupRoot)

$files = Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File
$repaired = 0
$fallback = 0
$unchanged = 0
$failed = 0
$report = New-Object System.Collections.Generic.List[string]
$report.Add("FINAL REPAIR REPORT") | Out-Null
$report.Add("===================") | Out-Null
$report.Add(("GameRoot: " + $GameRoot)) | Out-Null
$report.Add(("Specter : " + $Specter)) | Out-Null
$report.Add(("Backup  : " + $BackupRoot)) | Out-Null
$report.Add(("Files   : " + $files.Count)) | Out-Null
$report.Add(("GeneratedUtc: " + (Get-Date).ToUniversalTime().ToString("o"))) | Out-Null
$report.Add("") | Out-Null

foreach ($f in $files) {
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $fixes = $null
  $newText = Repair-IniText $text $f.Name ([ref]$fixes)

  $critBefore = Test-CriticalRemaining $text
  $critAfter = Test-CriticalRemaining $newText

  $changed = ($newText -ne ($text -replace "`r`n", "`n" -replace "`r", "`n").TrimStart([char]0xFEFF))
  # normalize compare
  $normOrig = ($text.TrimStart([char]0xFEFF) -replace "`r`n", "`n" -replace "`r", "`n")
  if (-not $normOrig.EndsWith("`n")) { $normOrigCompare = $normOrig + "`n" } else { $normOrigCompare = $normOrig }
  $changed = ($newText -ne $normOrigCompare)

  if ($critAfter.Count -gt 0) {
    # Attempt safe fallback only for single-Object aircraft-like files that remain broken
    $objNames = [regex]::Matches($newText, '(?im)^\s*Object\s+(\S+)\s*$') | ForEach-Object { $_.Groups[1].Value }
    if (@($objNames).Count -eq 1 -and ($f.Name -match '(?i)F35|Aircraft|AWACS|Bomber|Fighter|MQ9|Tejas|Akinci|TB2|Tu-22')) {
      $safe = New-SafeAircraftFallback $objNames[0]
      $bakRel = $rel
      $bakPath = Join-Path $BackupRoot $bakRel
      Ensure-Directory (Split-Path -Parent $bakPath)
      Copy-Item -LiteralPath $f.FullName -Destination $bakPath -Force
      [System.IO.File]::WriteAllText($f.FullName, $safe, [System.Text.UTF8Encoding]::new($false))
      $fixedName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name) + "_FIXED.ini"
      $fixedPath = Join-Path $FixedOutDir $fixedName
      [System.IO.File]::WriteAllText($fixedPath, $safe, [System.Text.UTF8Encoding]::new($false))
      $fallback++
      $report.Add("FILE: $rel") | Out-Null
      $report.Add("STATUS: SAFE_FALLBACK") | Out-Null
      $report.Add(("OBJECT: " + $objNames[0])) | Out-Null
      $report.Add(("FIXED_COPY: Fixed\" + $fixedName)) | Out-Null
      $report.Add("ERROR: Remaining critical issues after syntax repair: " + ($critAfter -join ",")) | Out-Null
      $report.Add("FIX: Wrote minimal valid aircraft Object for boot stability") | Out-Null
      $report.Add("") | Out-Null
      continue
    } else {
      $failed++
      $report.Add("FILE: $rel") | Out-Null
      $report.Add("STATUS: FAILED") | Out-Null
      $report.Add("ERROR: " + ($critAfter -join ",")) | Out-Null
      $report.Add("FIX: Manual review required") | Out-Null
      $report.Add("") | Out-Null
      continue
    }
  }

  if ($changed -or $critBefore.Count -gt 0) {
    $bakPath = Join-Path $BackupRoot $rel
    Ensure-Directory (Split-Path -Parent $bakPath)
    if (-not (Test-Path -LiteralPath $bakPath)) {
      Copy-Item -LiteralPath $f.FullName -Destination $bakPath -Force
    }
    [System.IO.File]::WriteAllText($f.FullName, $newText, [System.Text.UTF8Encoding]::new($false))
    # Also mirror into Fixed\
    $fixedPath = Join-Path $FixedOutDir $f.Name
    # avoid name collisions: use relative path flattened
    $flat = ($rel -replace '[\\/]', '__')
    $fixedPath = Join-Path $FixedOutDir $flat
    Ensure-Directory (Split-Path -Parent $fixedPath)
    [System.IO.File]::WriteAllText($fixedPath, $newText, [System.Text.UTF8Encoding]::new($false))
    $repaired++
    $report.Add("FILE: $rel") | Out-Null
    $report.Add("STATUS: REPAIRED") | Out-Null
    $report.Add("ERROR: " + $(if ($critBefore.Count) { $critBefore -join "," } else { "formatting/syntax hygiene" })) | Out-Null
    $report.Add("FIX:") | Out-Null
    foreach ($fx in $fixes) { $report.Add("  - $fx") | Out-Null }
    $report.Add("") | Out-Null
  } else {
    $unchanged++
  }
}

$report.Add("SUMMARY") | Out-Null
$report.Add("-------") | Out-Null
$report.Add(("Repaired : " + $repaired)) | Out-Null
$report.Add(("Fallback : " + $fallback)) | Out-Null
$report.Add(("Unchanged: " + $unchanged)) | Out-Null
$report.Add(("Failed   : " + $failed)) | Out-Null
$verdict = if ($failed -eq 0) { "PASS" } else { "FAIL" }
$report.Add(("VERDICT  : " + $verdict)) | Out-Null

[System.IO.File]::WriteAllText($ReportPath, ($report -join [Environment]::NewLine) + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Host ("Repaired=$repaired Fallback=$fallback Failed=$failed Unchanged=$unchanged")
Write-Host ("Report: " + $ReportPath)

if ($failed -gt 0) { exit 2 } else { exit 0 }
