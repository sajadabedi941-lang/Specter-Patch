<#
.SYNOPSIS
  Specter FULL ENGINE INI REPAIR — scan, backup, repair, verify.
  Only modifies real INI files that fail verification. No fake files.
.PARAMETER GameRoot
.PARAMETER ScriptDir
.PARAMETER ReportPath
#>
param(
  [Parameter(Mandatory = $false)]
  [Alias("LiteralPath", "Path")]
  [string]$GameRoot,

  [Parameter(Mandatory = $false)]
  [string]$ScriptDir,

  [Parameter(Mandatory = $false)]
  [string]$ReportPath
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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

function Get-RelPath([string]$full, [string]$root) {
  return $full.Substring($root.Length).TrimStart('\', '/')
}

# ---------------------------------------------------------------------------
# Verification (detect parse defects)
# ---------------------------------------------------------------------------
function Test-IniFile([string]$text, [string]$rel) {
  $issues = New-Object System.Collections.Generic.List[object]
  function Add-I([int]$line, [string]$code, [string]$detail, [string]$sev) {
    $issues.Add([pscustomobject]@{
      File = $rel; Line = $line; Code = $code; Detail = $detail; Severity = $sev
    }) | Out-Null
  }

  if ([string]::IsNullOrWhiteSpace($text)) {
    Add-I 0 "EMPTY_FILE" "File is empty" "Critical"
    return $issues
  }

  $lines = $text -split "`r?`n", -1
  $hasObject = $false
  $stack = New-Object System.Collections.Generic.List[object]
  $inMultiComment = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    $n = $i + 1
    $s = $ln.Trim()

    # Corrupted / odd comment markers
    if ($s -match '^/\*' -or $s -match '\*/') {
      Add-I $n "CORRUPTED_COMMENT" "C-style comment markers are not valid in ZH INI" "Critical"
    }
    if ($s -match '^<!--' -or $s -match '-->') {
      Add-I $n "CORRUPTED_COMMENT" "HTML/XML comment markers are not valid in ZH INI" "Critical"
    }

    if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }

    $codePart = ($s -split ";", 2)[0]

    # Braces never valid in ZH Object INI code
    if ($codePart -match '[{}]') {
      Add-I $n "MISSING_BRACE_OR_INVALID" $s "Critical"
    }

    # Unbalanced quotes on code portion
    $qCount = ([regex]::Matches($codePart, '"')).Count
    if (($qCount % 2) -ne 0) {
      Add-I $n "INVALID_QUOTES" $s "Critical"
    }

    # Uppercase END
    if ($s -cmatch '^END\s*$') {
      Add-I $n "UPPERCASE_END" "Use End not END" "Critical"
    }

    # End; trailing junk (classic ReleaseCrashInfo parse crash)
    if ($s -match '(?i)^End[ \t]*;') {
      Add-I $n "END_TRAILING_COMMENT" $s "Critical"
    }

    # Bare Scale without =
    if ($s -match '(?i)^Scale[ \t]+' -and ($codePart -notmatch '=')) {
      Add-I $n "BARE_SCALE" $s "Critical"
    }

    # Invalid BuildCompletion enum
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') {
      Add-I $n "INVALID_PARAMETER" "PLACE_ON_GROUND is invalid; use PLACED_BY_PLAYER" "Critical"
    }

    # Broken ModuleTag (must be identifier after module type)
    if ($s -match '(?i)^(Behavior|Draw|Body|ClientUpdate|AI)\s*=\s*(\S+)\s+(\S+)') {
      $tag = $Matches[3]
      if ($tag -notmatch '(?i)^ModuleTag_' -and $tag -notmatch '(?i)^[A-Za-z_][A-Za-z0-9_]*$') {
        Add-I $n "BROKEN_MODULETAG" $s "Critical"
      }
    }
    if ($s -match '(?i)^(Behavior|Draw|Body|ClientUpdate|AI)\s*=\s*$') {
      Add-I $n "BROKEN_MODULETAG" "Module line missing type/tag: $s" "Critical"
    }

    # Malformed CommandButton / CommandSet style lines
    if ($s -match '(?i)^Command(Button|Set)\s*$') {
      Add-I $n "MALFORMED_COMMAND" "CommandButton/Set header missing name" "Critical"
    }
    if ($s -match '(?i)^Command(Button|Set)\s*=\s*$') {
      Add-I $n "MALFORMED_COMMAND" "Empty CommandButton/Set assignment" "Critical"
    }
    if ($s -match '(?i)^CommandButton\s+[^=\s]+\s*$' -and $s -notmatch '(?i)^CommandButton\s+\S+$') {
      # allow CommandButton NAME as block header in some schemas; flag junk
    }
    if ($s -match '(?i)^Button\s*=\s*$' -or $s -match '(?i)^CommandSet\s*=\s*$') {
      Add-I $n "MALFORMED_COMMAND" $s "Warning"
    }

    # Object header
    if ($s -match '(?i)^Object\s+(\S+)\s*$') {
      $hasObject = $true
      $oname = $Matches[1]
      if ($oname -eq '=' -or $oname -eq '' -or $oname -match '[,"]') {
        Add-I $n "INVALID_OBJECT_SYNTAX" $s "Critical"
      }
      foreach ($st in $stack) {
        Add-I $n "DUPLICATED_BEGIN_END" ("Still open " + $st.Kind + " from L" + $st.Line + " before Object " + $oname) "Critical"
      }
      $stack.Clear()
      $stack.Add(@{ Line = $n; Kind = "Object"; Name = $oname }) | Out-Null
      continue
    }
    if ($s -match '(?i)^Object\s*$') {
      Add-I $n "INVALID_OBJECT_SYNTAX" "Object with no name" "Critical"
      continue
    }

    # End
    if ($s -match '(?i)^End\b') {
      if ($stack.Count -gt 0) {
        $null = $stack.RemoveAt($stack.Count - 1)
      }
      continue
    }

    # Block openers
    if ($s -match '(?i)^(Behavior|Draw|Body|ClientUpdate|AI)\s*=') {
      $stack.Add(@{ Line = $n; Kind = "Module"; Name = $s }) | Out-Null
      continue
    }
    if ($s -match '(?i)^AliasConditionState\b') { continue }
    if ($s -match '(?i)^(ConditionState|TransitionState|WeaponSet|ArmorSet|UnitSpecificSounds|Prerequisites|DefaultConditionState)\b') {
      $stack.Add(@{ Line = $n; Kind = "State"; Name = $s }) | Out-Null
      continue
    }
  }

  foreach ($st in $stack) {
    if ($st.Kind -eq "Object") {
      Add-I $st.Line "MISSING_END" ("Object " + $st.Name + " missing final End") "Critical"
    } elseif ($st.Kind -eq "Module") {
      Add-I $st.Line "MISSING_END" ("Module block not closed: " + $st.Name) "Warning"
    }
  }

  if ($hasObject) {
    $codeLines = @()
    foreach ($ln2 in $lines) {
      $t2 = $ln2.Trim()
      if ($t2 -and -not $t2.StartsWith(";") -and -not $t2.StartsWith("//")) { $codeLines += $t2 }
    }
    if ($codeLines.Count -gt 0 -and $codeLines[-1] -notmatch '(?i)^End\s*$') {
      Add-I $lines.Count "MISSING_END" ("Last code line: " + $codeLines[-1]) "Critical"
    }
  }

  return $issues
}

function Get-CriticalIssues($issues) {
  return @($issues | Where-Object { $_.Severity -eq "Critical" })
}

# ---------------------------------------------------------------------------
# Repair (safe automatic fixes only)
# ---------------------------------------------------------------------------
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
  if (-not $text2.EndsWith("`n")) {
    $text2 += "`n"
    $fixes.Add("Added trailing newline") | Out-Null
  }

  $FixList.Value = $fixes
  return $text2
}

function Normalize-Compare([string]$text) {
  $t = $text.TrimStart([char]0xFEFF) -replace "`r`n", "`n" -replace "`r", "`n"
  if (-not $t.EndsWith("`n")) { $t += "`n" }
  return $t
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

Write-Host ""
Write-Host "============================================================"
Write-Host " Specter ENGINE REPAIR — AUTO_REPAIR_ENGINE"
Write-Host "============================================================"
Write-Host ""

if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found. Need Data\INI\Object\Specter\. Copy this package into the game folder."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"

if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "REPAIR_REPORT.txt"
}

$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupRoot = Join-Path $GameRoot ("Specter_ENGINE_REPAIR_BACKUP\" + $ts)
Ensure-Directory $BackupRoot

Write-Host ("[1/4] GameRoot : " + $GameRoot)
Write-Host ("       Specter : " + $Specter)
Write-Host ("       Backup  : " + $BackupRoot)
Write-Host ""

$knownTargets = @(
  "British Armed Forces\Airforce\Britain_F35B.ini",
  "British Armed Forces\Drones\Britain_CombatDrone.ini"
)

Write-Host "[2/4] Scanning ALL Specter INI files..."
$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File -ErrorAction Stop)
Write-Host ("       Found " + $files.Count + " INI files")

$allIssues = New-Object System.Collections.Generic.List[object]
$fileIssueMap = @{}  # rel -> issues
$failingFiles = New-Object System.Collections.Generic.List[string]

$idx = 0
foreach ($f in $files) {
  $idx++
  if (($idx % 100) -eq 0 -or $idx -eq $files.Count) {
    Write-Host ("       Progress: $idx / $($files.Count)")
  }
  $rel = Get-RelPath $f.FullName $Specter
  try {
    $text = [System.IO.File]::ReadAllText($f.FullName)
  } catch {
    $iss = [pscustomobject]@{ File = $rel; Line = 0; Code = "READ_ERROR"; Detail = $_.Exception.Message; Severity = "Critical" }
    $allIssues.Add($iss) | Out-Null
    $fileIssueMap[$rel] = @($iss)
    $failingFiles.Add($rel) | Out-Null
    continue
  }
  $issues = Test-IniFile $text $rel
  foreach ($iss in $issues) { $allIssues.Add($iss) | Out-Null }
  $fileIssueMap[$rel] = $issues
  $crit = Get-CriticalIssues $issues
  if ($crit.Count -gt 0) {
    $failingFiles.Add($rel) | Out-Null
  }
}

Write-Host ("       Files failing verification: " + $failingFiles.Count)
Write-Host ("       Total issues detected: " + $allIssues.Count)
Write-Host ""

Write-Host "[3/4] Repairing files that fail verification (real files only)..."
$repaired = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$unchangedOk = 0
$backedUp = 0

foreach ($rel in $failingFiles) {
  $full = Join-Path $Specter $rel
  if (-not (Test-Path -LiteralPath $full)) {
    $skipped.Add([pscustomobject]@{ File = $rel; Reason = "File missing at repair time" }) | Out-Null
    continue
  }

  $origText = [System.IO.File]::ReadAllText($full)
  $fixes = $null
  $newText = Repair-IniText $origText ([ref]$fixes)
  $issuesAfter = Test-IniFile $newText $rel
  $critAfter = Get-CriticalIssues $issuesAfter
  $critBefore = Get-CriticalIssues $fileIssueMap[$rel]

  # Only write if we actually fixed critical issues and content changed
  $changed = ((Normalize-Compare $origText) -ne $newText)

  if ($critAfter.Count -gt 0) {
    # Could not fully auto-repair — do NOT write fake content
    $skipped.Add([pscustomobject]@{
      File = $rel
      Reason = ("Still critical after auto-repair: " + (($critAfter | ForEach-Object { $_.Code }) -join ","))
      Before = (($critBefore | ForEach-Object { $_.Code }) -join ",")
    }) | Out-Null
    Write-Host ("       SKIP (needs manual): " + $rel)
    continue
  }

  if (-not $changed -and $critBefore.Count -eq 0) {
    $unchangedOk++
    continue
  }

  if (-not $changed) {
    # Critical flagged but repair produced identical text — skip, no fake write
    $skipped.Add([pscustomobject]@{
      File = $rel
      Reason = "Verification failed but no safe automatic fix available"
      Before = (($critBefore | ForEach-Object { $_.Code }) -join ",")
    }) | Out-Null
    Write-Host ("       SKIP (no safe fix): " + $rel)
    continue
  }

  # Backup then write
  $bakPath = Join-Path $BackupRoot $rel
  Ensure-Directory (Split-Path -Parent $bakPath)
  Copy-Item -LiteralPath $full -Destination $bakPath -Force
  $backedUp++
  [System.IO.File]::WriteAllText($full, $newText, [System.Text.UTF8Encoding]::new($false))

  $repaired.Add([pscustomobject]@{
    File = $rel
    Errors = (($critBefore | ForEach-Object { ("L" + $_.Line + " " + $_.Code + ": " + $_.Detail) }) -join " | ")
    Fixes = ($fixes -join " | ")
  }) | Out-Null
  Write-Host ("       REPAIRED: " + $rel)
}

Write-Host ""
Write-Host "[4/4] Final verification (re-parse every Specter INI)..."
$verifyIssues = New-Object System.Collections.Generic.List[object]
$verifyFail = New-Object System.Collections.Generic.List[string]
$vIdx = 0
foreach ($f in $files) {
  $vIdx++
  if (($vIdx % 100) -eq 0 -or $vIdx -eq $files.Count) {
    Write-Host ("       Verify progress: $vIdx / $($files.Count)")
  }
  $rel = Get-RelPath $f.FullName $Specter
  try {
    $text = [System.IO.File]::ReadAllText($f.FullName)
  } catch {
    $verifyIssues.Add([pscustomobject]@{ File = $rel; Line = 0; Code = "READ_ERROR"; Detail = $_.Exception.Message; Severity = "Critical" }) | Out-Null
    $verifyFail.Add($rel) | Out-Null
    continue
  }
  $iss = Test-IniFile $text $rel
  $crit = Get-CriticalIssues $iss
  foreach ($c in $crit) { $verifyIssues.Add($c) | Out-Null }
  if ($crit.Count -gt 0) { $verifyFail.Add($rel) | Out-Null }
}

$verdict = if ($verifyFail.Count -eq 0) { "PASS" } else { "FAIL" }
Write-Host ("       Final critical failures: " + $verifyFail.Count + "  VERDICT: " + $verdict)
Write-Host ""

# Known crash targets status
$knownStatus = New-Object System.Collections.Generic.List[string]
foreach ($kt in $knownTargets) {
  $kp = Join-Path $Specter $kt
  if (-not (Test-Path -LiteralPath $kp)) {
    $knownStatus.Add("$kt — NOT FOUND") | Out-Null
  } elseif ($verifyFail -contains ($kt -replace '\\', '/') -or $verifyFail -contains $kt) {
    $knownStatus.Add("$kt — STILL FAILING") | Out-Null
  } else {
    # normalize compare for path separators
    $failNorm = @($verifyFail | ForEach-Object { $_ -replace '/', '\' })
    if ($failNorm -contains $kt) {
      $knownStatus.Add("$kt — STILL FAILING") | Out-Null
    } else {
      $knownStatus.Add("$kt — OK") | Out-Null
    }
  }
}

# ---------------------------------------------------------------------------
# Write REPAIR_REPORT.txt
# ---------------------------------------------------------------------------
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("SPECTER ENGINE REPAIR REPORT")
[void]$sb.AppendLine("============================")
[void]$sb.AppendLine(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine(("GameRoot     : " + $GameRoot))
[void]$sb.AppendLine(("Specter      : " + $Specter))
[void]$sb.AppendLine(("Backup       : " + $BackupRoot))
[void]$sb.AppendLine(("Scanned      : " + $files.Count + " INI files"))
[void]$sb.AppendLine(("Backed up    : " + $backedUp + " files"))
[void]$sb.AppendLine(("Repaired     : " + $repaired.Count))
[void]$sb.AppendLine(("Skipped      : " + $skipped.Count))
[void]$sb.AppendLine(("Final verdict: " + $verdict))
[void]$sb.AppendLine("")

[void]$sb.AppendLine("KNOWN CRASH TARGETS (British Armed Forces)")
[void]$sb.AppendLine("------------------------------------------")
foreach ($ks in $knownStatus) { [void]$sb.AppendLine("  " + $ks) }
[void]$sb.AppendLine("")

[void]$sb.AppendLine("DETECTED ERRORS (before repair)")
[void]$sb.AppendLine("-------------------------------")
$byCode = $allIssues | Group-Object Code | Sort-Object Count -Descending
if ($byCode) {
  foreach ($g in $byCode) {
    [void]$sb.AppendLine(("  {0,-32} {1}" -f $g.Name, $g.Count))
  }
} else {
  [void]$sb.AppendLine("  (none)")
}
[void]$sb.AppendLine("")

[void]$sb.AppendLine("REPAIRED FILES")
[void]$sb.AppendLine("--------------")
if ($repaired.Count -eq 0) {
  [void]$sb.AppendLine("  (none — no failing files needed modification, or tree already clean)")
} else {
  foreach ($r in $repaired) {
    [void]$sb.AppendLine(("FILE: " + $r.File))
    [void]$sb.AppendLine(("ERROR: " + $r.Errors))
    [void]$sb.AppendLine(("FIX: " + $r.Fixes))
    [void]$sb.AppendLine("")
  }
}

[void]$sb.AppendLine("SKIPPED FILES")
[void]$sb.AppendLine("-------------")
if ($skipped.Count -eq 0) {
  [void]$sb.AppendLine("  (none)")
} else {
  foreach ($s in $skipped) {
    [void]$sb.AppendLine(("FILE: " + $s.File))
    [void]$sb.AppendLine(("REASON: " + $s.Reason))
    if ($s.Before) { [void]$sb.AppendLine(("BEFORE: " + $s.Before)) }
    [void]$sb.AppendLine("")
  }
}

[void]$sb.AppendLine("FINAL VERIFICATION RESULT")
[void]$sb.AppendLine("-------------------------")
[void]$sb.AppendLine(("Critical remaining: " + $verifyFail.Count))
[void]$sb.AppendLine(("VERDICT: " + $verdict))
if ($verifyFail.Count -gt 0) {
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("Still failing:")
  foreach ($vf in $verifyFail) {
    [void]$sb.AppendLine("  - " + $vf)
  }
  foreach ($vi in $verifyIssues) {
    [void]$sb.AppendLine(("  DETAIL {0} L{1} {2}: {3}" -f $vi.File, $vi.Line, $vi.Code, $vi.Detail))
  }
}

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ("Report written: " + $ReportPath)
Write-Host ""

if ($verdict -ne "PASS") { exit 2 } else { exit 0 }
