<#
.SYNOPSIS
  Scan-only tool for Generals ZH Specter Object INIs.
  Does NOT delete or modify any game files.
  Writes INI_ERROR_REPORT.txt and copies broken files into a backup folder.
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

function Get-SuggestedFix([string]$code) {
  switch ($code) {
    "EMPTY_FILE"             { return "Restore this INI from a known-good backup, or remove it from the load path if unused." }
    "READ_ERROR"             { return "Fix file permissions / unlock the file, then re-scan." }
    "MISSING_END"            { return "Add a matching 'End' line to close the open Object/module/state block." }
    "MISSING_FINAL_END"      { return "Ensure the last code line of the Object is a bare 'End' (no trailing text)." }
    "MALFORMED_OBJECT"       { return "Use: Object ObjectName   (one name, no '=', no quotes, no commas)." }
    "DUPLICATE_OBJECT"       { return "Keep one definition only; rename or remove the duplicate Object." }
    "INVALID_SYNTAX_CHAR"    { return "Remove { } or other invalid characters from the code portion of the line." }
    "INVALID_QUOTES"         { return "Balance or remove mismatched double-quotes on this line." }
    "END_TRAILING_COMMENT"   { return "Change 'End; comment' into two lines: 'End' then '; comment'." }
    "UPPERCASE_END"          { return "Replace 'END' with 'End' (capital E only)." }
    "UNCLOSED_BEFORE_OBJECT" { return "Close previous blocks with 'End' before starting a new Object." }
    "BARE_SCALE"             { return "Change 'Scale value' to 'Scale = value'." }
    "INVALID_BUILDCOMPLETION"{ return "Change PLACE_ON_GROUND to PLACED_BY_PLAYER." }
    default                  { return "Inspect the line and compare with a known-good Specter INI of the same type." }
  }
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

Write-Host ""
Write-Host "============================================================"
Write-Host " Specter INI SCAN (read-only — no deletes, no overwrites)"
Write-Host "============================================================"
Write-Host ""

if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found. Copy this folder next to Data\ (need Data\INI\Object\Specter\)."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"

if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "INI_ERROR_REPORT.txt"
}

$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupRoot = Join-Path $GameRoot ("Specter_INI_SCAN_BACKUP\" + $ts)

Write-Host ("GameRoot : " + $GameRoot)
Write-Host ("Specter  : " + $Specter)
Write-Host ("Report   : " + $ReportPath)
Write-Host ("Backup   : " + $BackupRoot + " (broken files only, copies)")
Write-Host ""

$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File -ErrorAction Stop)
Write-Host ("Scanning " + $files.Count + " INI files...")

$issues = New-Object System.Collections.Generic.List[object]
$objectIndex = @{}  # objectName -> list of @{File=; Line=}
$brokenRels = New-Object System.Collections.Generic.HashSet[string]

function Add-Issue([string]$fullPath, [string]$rel, [int]$line, [string]$code, [string]$detail) {
  $issues.Add([pscustomobject]@{
    FullPath = $fullPath
    Rel      = $rel
    Line     = $line
    Code     = $code
    Detail   = $detail
    Fix      = (Get-SuggestedFix $code)
  }) | Out-Null
  [void]$brokenRels.Add($rel)
}

$idx = 0
foreach ($f in $files) {
  $idx++
  if (($idx % 200) -eq 0 -or $idx -eq $files.Count) {
    Write-Host ("  Progress: $idx / $($files.Count)")
  }

  $full = $f.FullName
  $rel = $full.Substring($Specter.Length).TrimStart('\', '/')

  try {
    $text = [System.IO.File]::ReadAllText($full)
  } catch {
    Add-Issue $full $rel 0 "READ_ERROR" $_.Exception.Message
    continue
  }

  if ([string]::IsNullOrWhiteSpace($text)) {
    Add-Issue $full $rel 0 "EMPTY_FILE" "File is empty"
    continue
  }

  $lines = $text -split "`r?`n", -1
  $hasObject = $false
  $stack = New-Object System.Collections.Generic.List[object]

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    $n = $i + 1
    $s = $ln.Trim()
    if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }

    $codePart = ($s -split ";", 2)[0]

    # Invalid syntax characters (braces never valid in ZH Object INI code)
    if ($codePart -match '[{}]') {
      Add-Issue $full $rel $n "INVALID_SYNTAX_CHAR" $s
    }

    # Unbalanced quotes
    $qCount = ([regex]::Matches($codePart, '"')).Count
    if (($qCount % 2) -ne 0) {
      Add-Issue $full $rel $n "INVALID_QUOTES" $s
    }

    # Common parse crash: End; comment
    if ($s -match '(?i)^End[ \t]*;') {
      Add-Issue $full $rel $n "END_TRAILING_COMMENT" $s
    }
    if ($s -cmatch '^END\s*$') {
      Add-Issue $full $rel $n "UPPERCASE_END" "Use End not END"
    }
    if ($s -match '(?i)^Scale[ \t]+' -and ($codePart -notmatch '=')) {
      Add-Issue $full $rel $n "BARE_SCALE" $s
    }
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') {
      Add-Issue $full $rel $n "INVALID_BUILDCOMPLETION" $s
    }

    # Malformed Object headers
    if ($s -match '(?i)^Object\s*$') {
      Add-Issue $full $rel $n "MALFORMED_OBJECT" "Object with no name"
      continue
    }
    if ($s -match '(?i)^Object\s*=') {
      # Prerequisite-style "Object = Name" inside Prerequisites — not a header
    }
    elseif ($s -match '(?i)^Object\b') {
      if ($s -match '(?i)^Object\s+(\S+)\s*$') {
        $oname = $Matches[1]
        if ($oname -eq '=' -or $oname -eq '' -or $oname -match '[,"\{\}]') {
          Add-Issue $full $rel $n "MALFORMED_OBJECT" $s
        } else {
          $hasObject = $true
          if (-not $objectIndex.ContainsKey($oname)) {
            $objectIndex[$oname] = New-Object System.Collections.Generic.List[object]
          }
          $objectIndex[$oname].Add(@{ File = $rel; FullPath = $full; Line = $n }) | Out-Null
          foreach ($st in $stack) {
            Add-Issue $full $rel $n "UNCLOSED_BEFORE_OBJECT" ("Still open " + $st.Kind + " from L" + $st.Line + " before Object " + $oname)
          }
          $stack.Clear()
          $stack.Add(@{ Line = $n; Kind = "Object"; Name = $oname }) | Out-Null
        }
      } else {
        Add-Issue $full $rel $n "MALFORMED_OBJECT" $s
      }
      continue
    }

    if ($s -match '(?i)^End\b') {
      if ($stack.Count -gt 0) { $null = $stack.RemoveAt($stack.Count - 1) }
      continue
    }

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

  # Missing End blocks (Object still open)
  foreach ($st in $stack) {
    if ($st.Kind -eq "Object") {
      Add-Issue $full $rel $st.Line "MISSING_END" ("Object " + $st.Name + " missing final End")
    } elseif ($st.Kind -eq "Module") {
      Add-Issue $full $rel $st.Line "MISSING_END" ("Module block not closed: " + $st.Name)
    }
  }

  if ($hasObject) {
    $codeLines = @()
    foreach ($ln2 in $lines) {
      $t2 = $ln2.Trim()
      if ($t2 -and -not $t2.StartsWith(";") -and -not $t2.StartsWith("//")) { $codeLines += $t2 }
    }
    if ($codeLines.Count -gt 0 -and $codeLines[-1] -notmatch '(?i)^End\s*$') {
      Add-Issue $full $rel $lines.Count "MISSING_FINAL_END" ("Last code line: " + $codeLines[-1])
    }
  }
}

# Duplicate Object names across files
foreach ($kv in $objectIndex.GetEnumerator()) {
  $entries = @($kv.Value)
  $uniqFiles = @($entries | ForEach-Object { $_.File } | Select-Object -Unique)
  if ($uniqFiles.Count -gt 1) {
    foreach ($e in $entries) {
      $others = ($uniqFiles | Where-Object { $_ -ne $e.File }) -join ", "
      Add-Issue $e.FullPath $e.File $e.Line "DUPLICATE_OBJECT" ("Object '" + $kv.Key + "' also defined in: " + $others)
    }
  }
}

Write-Host ("Issues found: " + $issues.Count)
Write-Host ""

# Backup broken files ONLY (copies — never deletes / never overwrites originals)
if ($brokenRels.Count -gt 0) {
  Write-Host ("Creating backup of " + $brokenRels.Count + " broken file(s)...")
  Ensure-Directory $BackupRoot
  foreach ($rel in ($brokenRels | Sort-Object)) {
    $src = Join-Path $Specter $rel
    if (-not (Test-Path -LiteralPath $src)) { continue }
    $dst = Join-Path $BackupRoot $rel
    Ensure-Directory (Split-Path -Parent $dst)
    Copy-Item -LiteralPath $src -Destination $dst -Force
  }
  Write-Host ("Backup folder: " + $BackupRoot)
} else {
  Write-Host "No broken files — backup folder not created."
  $BackupRoot = "(not created — no errors)"
}

# Write INI_ERROR_REPORT.txt
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("SPECTER INI ERROR REPORT")
[void]$sb.AppendLine("========================")
[void]$sb.AppendLine(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine(("GameRoot     : " + $GameRoot))
[void]$sb.AppendLine(("Specter      : " + $Specter))
[void]$sb.AppendLine(("Scanned      : " + $files.Count + " INI files"))
[void]$sb.AppendLine(("Errors       : " + $issues.Count))
[void]$sb.AppendLine(("Broken files : " + $brokenRels.Count))
[void]$sb.AppendLine(("Backup       : " + $BackupRoot))
[void]$sb.AppendLine("Mode         : SCAN ONLY (no deletes, no modifications to game files)")
[void]$sb.AppendLine("")

$byCode = $issues | Group-Object Code | Sort-Object Count -Descending
[void]$sb.AppendLine("SUMMARY BY ERROR TYPE")
[void]$sb.AppendLine("---------------------")
if ($byCode) {
  foreach ($g in $byCode) {
    [void]$sb.AppendLine(("  {0,-28} {1}" -f $g.Name, $g.Count))
  }
} else {
  [void]$sb.AppendLine("  (none — all clear)")
}
[void]$sb.AppendLine("")

[void]$sb.AppendLine("DETAILS")
[void]$sb.AppendLine("-------")
if ($issues.Count -eq 0) {
  [void]$sb.AppendLine("No errors detected under Data\INI\Object\Specter.")
} else {
  foreach ($iss in ($issues | Sort-Object FullPath, Line, Code)) {
    [void]$sb.AppendLine(("FULL PATH      : {0}" -f $iss.FullPath))
    [void]$sb.AppendLine(("RELATIVE PATH  : {0}" -f $iss.Rel))
    [void]$sb.AppendLine(("ERROR TYPE     : {0}" -f $iss.Code))
    [void]$sb.AppendLine(("LINE NUMBER    : {0}" -f $iss.Line))
    [void]$sb.AppendLine(("DETAIL         : {0}" -f $iss.Detail))
    [void]$sb.AppendLine(("SUGGESTED FIX  : {0}" -f $iss.Fix))
    [void]$sb.AppendLine("")
  }
}

$verdict = if ($issues.Count -eq 0) { "PASS" } else { "FAIL" }
[void]$sb.AppendLine("FINAL VERDICT: $verdict")

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ""
Write-Host ("Report written: " + $ReportPath)
Write-Host ("VERDICT: " + $verdict)
Write-Host ""

if ($issues.Count -gt 0) { exit 2 } else { exit 0 }
