<#
.SYNOPSIS
  Scan all Data\INI\Object\Specter\*.ini for Generals ZH parse defects.
.PARAMETER GameRoot
  Game root containing Data\INI\Object\Specter
.PARAMETER ScriptDir
  Folder containing this script (report output location)
.PARAMETER ReportPath
  Optional explicit report path
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

function Test-SpecterRoot([string]$root) {
  if (-not $root) { return $false }
  $p = Join-Path $root "Data\INI\Object\Specter"
  return (Test-Path -LiteralPath $p)
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

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

if (-not $GameRoot) {
  $GameRoot = Find-GameRoot $ScriptDir
}
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found (need Data\INI\Object\Specter\). Pass -GameRoot."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "FULL_INI_SCAN_REPORT.txt"
}

Write-Host ("Scanning: " + $Specter)

$files = Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File -ErrorAction Stop
$issues = New-Object System.Collections.Generic.List[object]
$objectIndex = @{}  # objectName -> list of files

function Add-Issue([string]$rel, [int]$line, [string]$code, [string]$detail) {
  $issues.Add([pscustomobject]@{
    File = $rel
    Line = $line
    Code = $code
    Detail = $detail
  }) | Out-Null
}

foreach ($f in $files) {
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  try {
    $text = [System.IO.File]::ReadAllText($f.FullName)
  } catch {
    Add-Issue $rel 0 "READ_ERROR" $_.Exception.Message
    continue
  }

  if ([string]::IsNullOrWhiteSpace($text)) {
    Add-Issue $rel 0 "EMPTY_FILE" "File is empty"
    continue
  }

  $lines = $text -split "`r?`n", -1
  $hasObject = $false
  $stack = New-Object System.Collections.Generic.List[object]
  # stack items: @{Line=; Kind=; Name=}

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    $n = $i + 1
    $s = $ln.Trim()
    if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }

    # braces in code portion
    $codePart = ($s -split ";", 2)[0]
    if ($codePart -match '[{}]') {
      Add-Issue $rel $n "INVALID_BRACE" $s
    }

    # uppercase END
    if ($s -cmatch '^END\s*$') {
      Add-Issue $rel $n "UPPERCASE_END" "Use End not END"
    }

    # End; trailing junk on same line
    if ($s -match '(?i)^End[ \t]*;') {
      Add-Issue $rel $n "END_TRAILING_COMMENT" $s
    }

    # bare Scale
    if ($s -match '(?i)^Scale[ \t]+' -and ($codePart -notmatch '=')) {
      Add-Issue $rel $n "BARE_SCALE" $s
    }

    # invalid BuildCompletion
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') {
      Add-Issue $rel $n "INVALID_BUILDCOMPLETION" "PLACE_ON_GROUND is not valid; use PLACED_BY_PLAYER"
    }

    # Object header
    if ($s -match '(?i)^Object\s+(\S+)\s*$') {
      $hasObject = $true
      $oname = $Matches[1]
      if ($oname -eq '=' -or $oname -eq '') {
        Add-Issue $rel $n "INVALID_OBJECT_HEADER" $s
      } else {
        if (-not $objectIndex.ContainsKey($oname)) { $objectIndex[$oname] = New-Object System.Collections.Generic.List[string] }
        $objectIndex[$oname].Add($rel) | Out-Null
      }
      # new top-level — record open blocks still on stack as unclosed
      foreach ($st in $stack) {
        Add-Issue $rel $n "UNCLOSED_BEFORE_OBJECT" ("Still open " + $st.Kind + " from L" + $st.Line + " before Object " + $oname)
      }
      $stack.Clear()
      $stack.Add(@{ Line = $n; Kind = "Object"; Name = $oname }) | Out-Null
      continue
    }
    if ($s -match '(?i)^Object\s*=') {
      # Prerequisite form Object = Name — valid inside Prerequisites, not a header
      # ignore
    }

    # End
    if ($s -match '(?i)^End\b') {
      if ($stack.Count -eq 0) {
        # May be false positive for ArmorSet-style if we didn't track — still note EXTRA_END lightly only if clearly wrong
        # Don't flood: only flag if End; form already flagged. Skip bare EXTRA_END noise.
      } else {
        $null = $stack.RemoveAt($stack.Count - 1)
      }
      continue
    }

    # Block openers (module / state)
    if ($s -match '(?i)^(Behavior|Draw|Body|ClientUpdate|AI)\s*=') {
      $stack.Add(@{ Line = $n; Kind = "Module"; Name = $s }) | Out-Null
      continue
    }
    if ($s -match '(?i)^(ConditionState|TransitionState|WeaponSet|ArmorSet|UnitSpecificSounds|Prerequisites|DefaultConditionState)\b') {
      # DefaultConditionState may have no =
      if ($s -match '(?i)^DefaultConditionState\s*$' -or $s -match '(?i)^(ConditionState|TransitionState|WeaponSet|ArmorSet|UnitSpecificSounds|Prerequisites)\b') {
        # ArmorSet / WeaponSet / Prerequisites / UnitSpecificSounds / ConditionState open blocks
        if ($s -match '(?i)^AliasConditionState\b') {
          # alias is NOT a block
        } else {
          $stack.Add(@{ Line = $n; Kind = "State"; Name = $s }) | Out-Null
        }
      }
      continue
    }
  }

  foreach ($st in $stack) {
    if ($st.Kind -eq "Object") {
      Add-Issue $rel $st.Line "MISSING_END" ("Object " + $st.Name + " missing final End")
    }
  }

  if ($hasObject) {
    $codeLines = @()
    foreach ($ln2 in $lines) {
      $t2 = $ln2.Trim()
      if ($t2 -and -not $t2.StartsWith(";")) { $codeLines += $t2 }
    }
    if ($codeLines.Count -gt 0 -and $codeLines[-1] -notmatch '(?i)^End\s*$') {
      Add-Issue $rel $lines.Count "MISSING_FINAL_END" ("Last code line: " + $codeLines[-1])
    }
  }

  # empty object bodies (Object ... End with nothing between except comments)
  $objMatches = [regex]::Matches($text, '(?im)^\s*Object\s+(\S+)\s*$')
  for ($oi = 0; $oi -lt $objMatches.Count; $oi++) {
    $m = $objMatches[$oi]
    $start = $m.Index + $m.Length
    $end = if ($oi + 1 -lt $objMatches.Count) { $objMatches[$oi + 1].Index } else { $text.Length }
    $body = $text.Substring($start, $end - $start)
    $bodyCode = @()
    foreach ($bl in ($body -split "`r?`n")) {
      $bt = $bl.Trim()
      if ($bt -and -not $bt.StartsWith(";") -and $bt -notmatch '(?i)^End\s*$') { $bodyCode += $bt }
    }
    if ($bodyCode.Count -eq 0) {
      Add-Issue $rel 0 "EMPTY_OBJECT" $m.Groups[1].Value
    }
  }
}

# Duplicate object names across files
foreach ($kv in $objectIndex.GetEnumerator()) {
  $uniq = $kv.Value | Select-Object -Unique
  if (@($uniq).Count -gt 1) {
    Add-Issue ($uniq -join " | ") 0 "DUPLICATE_OBJECT" ($kv.Key + " defined in " + (@($uniq).Count) + " files")
  }
}

# Write report
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("FULL INI SCAN REPORT")
[void]$sb.AppendLine("====================")
[void]$sb.AppendLine(("GameRoot: " + $GameRoot))
[void]$sb.AppendLine(("Specter : " + $Specter))
[void]$sb.AppendLine(("Scanned : " + $files.Count + " INI files"))
[void]$sb.AppendLine(("Issues  : " + $issues.Count))
[void]$sb.AppendLine(("GeneratedUtc: " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine("")

$byCode = $issues | Group-Object Code | Sort-Object Count -Descending
[void]$sb.AppendLine("SUMMARY BY CODE")
[void]$sb.AppendLine("---------------")
foreach ($g in $byCode) {
  [void]$sb.AppendLine(("  {0,-28} {1}" -f $g.Name, $g.Count))
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("DETAILS")
[void]$sb.AppendLine("-------")
foreach ($iss in ($issues | Sort-Object File, Line)) {
  [void]$sb.AppendLine(("FILE: {0}" -f $iss.File))
  [void]$sb.AppendLine(("LINE: {0}" -f $iss.Line))
  [void]$sb.AppendLine(("CODE: {0}" -f $iss.Code))
  [void]$sb.AppendLine(("DETAIL: {0}" -f $iss.Detail))
  [void]$sb.AppendLine("")
}

# Critical parse codes that block boot
$critical = @("END_TRAILING_COMMENT","UPPERCASE_END","BARE_SCALE","INVALID_BUILDCOMPLETION","INVALID_BRACE","MISSING_FINAL_END","EMPTY_FILE","READ_ERROR","INVALID_OBJECT_HEADER")
$critCount = @($issues | Where-Object { $critical -contains $_.Code }).Count
[void]$sb.AppendLine("CRITICAL_PARSE_ISSUES: $critCount")
[void]$sb.AppendLine(("VERDICT: " + $(if ($critCount -eq 0) { "PASS" } else { "FAIL" })))

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ("Report: " + $ReportPath)
Write-Host ("Issues: " + $issues.Count + "  Critical: " + $critCount)

# Return critical count via exit code for BAT
if ($critCount -gt 0) { exit 2 } else { exit 0 }
