<#
.SYNOPSIS
  Scan ALL Data\INI\Object\Specter\*.ini for Generals ZH parse defects.
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
if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "SCAN_REPORT.txt"
}

Write-Host ("Scanning: " + $Specter)

$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File -ErrorAction Stop)
$issues = New-Object System.Collections.Generic.List[object]
$objectIndex = @{}

function Add-Issue([string]$rel, [int]$line, [string]$code, [string]$detail) {
  $issues.Add([pscustomobject]@{
    File = $rel; Line = $line; Code = $code; Detail = $detail
  }) | Out-Null
}

$idx = 0
foreach ($f in $files) {
  $idx++
  if (($idx % 200) -eq 0 -or $idx -eq $files.Count) {
    Write-Host ("  Progress: $idx / $($files.Count)")
  }
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

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    $n = $i + 1
    $s = $ln.Trim()
    if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }

    $codePart = ($s -split ";", 2)[0]
    if ($codePart -match '[{}]') { Add-Issue $rel $n "INVALID_BRACE" $s }

    $qCount = ([regex]::Matches($codePart, '"')).Count
    if (($qCount % 2) -ne 0) { Add-Issue $rel $n "INVALID_QUOTES" $s }

    if ($s -cmatch '^END\s*$') { Add-Issue $rel $n "UPPERCASE_END" "Use End not END" }
    if ($s -match '(?i)^End[ \t]*;') { Add-Issue $rel $n "END_TRAILING_COMMENT" $s }
    if ($s -match '(?i)^Scale[ \t]+' -and ($codePart -notmatch '=')) { Add-Issue $rel $n "BARE_SCALE" $s }
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') {
      Add-Issue $rel $n "INVALID_BUILDCOMPLETION" "PLACE_ON_GROUND is not valid; use PLACED_BY_PLAYER"
    }
    if ($s -match '(?i)^(Behavior|Draw|Body|ClientUpdate|AI)\s*=\s*$') {
      Add-Issue $rel $n "MALFORMED_MODULE" $s
    }
    if ($s -match '(?i)^Command(Button|Set)\s*$' -or $s -match '(?i)^Command(Button|Set)\s*=\s*$') {
      Add-Issue $rel $n "MALFORMED_COMMAND" $s
    }

    if ($s -match '(?i)^Object\s+(\S+)\s*$') {
      $hasObject = $true
      $oname = $Matches[1]
      if ($oname -eq '=' -or $oname -eq '' -or $oname -match '[,"]') {
        Add-Issue $rel $n "INVALID_OBJECT_HEADER" $s
      } else {
        if (-not $objectIndex.ContainsKey($oname)) {
          $objectIndex[$oname] = New-Object System.Collections.Generic.List[string]
        }
        $objectIndex[$oname].Add($rel) | Out-Null
      }
      foreach ($st in $stack) {
        Add-Issue $rel $n "UNCLOSED_BEFORE_OBJECT" ("Still open " + $st.Kind + " from L" + $st.Line)
      }
      $stack.Clear()
      $stack.Add(@{ Line = $n; Kind = "Object"; Name = $oname }) | Out-Null
      continue
    }
    if ($s -match '(?i)^Object\s*$') {
      Add-Issue $rel $n "INVALID_OBJECT_HEADER" "Object with no name"
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

  foreach ($st in $stack) {
    if ($st.Kind -eq "Object") {
      Add-Issue $rel $st.Line "MISSING_END" ("Object " + $st.Name + " missing final End")
    }
  }

  if ($hasObject) {
    $codeLines = @()
    foreach ($ln2 in $lines) {
      $t2 = $ln2.Trim()
      if ($t2 -and -not $t2.StartsWith(";") -and -not $t2.StartsWith("//")) { $codeLines += $t2 }
    }
    if ($codeLines.Count -gt 0 -and $codeLines[-1] -notmatch '(?i)^End\s*$') {
      Add-Issue $rel $lines.Count "MISSING_FINAL_END" ("Last code line: " + $codeLines[-1])
    }
  }
}

foreach ($kv in $objectIndex.GetEnumerator()) {
  $uniq = @($kv.Value | Select-Object -Unique)
  if ($uniq.Count -gt 1) {
    Add-Issue ($uniq -join " | ") 0 "DUPLICATE_OBJECT" ($kv.Key + " defined in " + $uniq.Count + " files")
  }
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("FULL INI SCAN REPORT")
[void]$sb.AppendLine("====================")
[void]$sb.AppendLine(("GameRoot: " + $GameRoot))
[void]$sb.AppendLine(("Specter : " + $Specter))
[void]$sb.AppendLine(("Scanned : " + $files.Count + " INI files"))
[void]$sb.AppendLine(("Issues  : " + $issues.Count))
[void]$sb.AppendLine(("GeneratedUtc: " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine("")

$known = @(
  "British Armed Forces\Airforce\Britain_F35B.ini",
  "Turkey Armed Forces\Turkey_WeaponObjects.ini",
  "Israel Defense Forces\Buildings\Israel_CommandCenter.ini",
  "Israel Defense Forces\Buildings\Israel_MilitaryHQ.ini"
)
[void]$sb.AppendLine("KNOWN TARGETS")
[void]$sb.AppendLine("-------------")
foreach ($k in $known) {
  $kp = Join-Path $Specter $k
  $status = if (-not (Test-Path -LiteralPath $kp)) { "NOT FOUND" } else {
    $ki = @($issues | Where-Object { ($_.File -replace '/', '\') -eq $k })
    if ($ki.Count -gt 0) { "HAS ISSUES (" + $ki.Count + ")" } else { "OK" }
  }
  [void]$sb.AppendLine(("  {0}  {1}" -f $status, $k))
}
[void]$sb.AppendLine("")

$byCode = $issues | Group-Object Code | Sort-Object Count -Descending
[void]$sb.AppendLine("SUMMARY BY CODE")
[void]$sb.AppendLine("---------------")
if ($byCode) {
  foreach ($g in $byCode) { [void]$sb.AppendLine(("  {0,-28} {1}" -f $g.Name, $g.Count)) }
} else {
  [void]$sb.AppendLine("  (none)")
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

$critical = @(
  "END_TRAILING_COMMENT","UPPERCASE_END","BARE_SCALE","INVALID_BUILDCOMPLETION",
  "INVALID_BRACE","MISSING_FINAL_END","MISSING_END","EMPTY_FILE","READ_ERROR",
  "INVALID_OBJECT_HEADER","INVALID_QUOTES","MALFORMED_MODULE","UNCLOSED_BEFORE_OBJECT"
)
$critCount = @($issues | Where-Object { $critical -contains $_.Code }).Count
[void]$sb.AppendLine("CRITICAL_PARSE_ISSUES: $critCount")
[void]$sb.AppendLine(("VERDICT: " + $(if ($critCount -eq 0) { "PASS" } else { "FAIL" })))

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ("Report: " + $ReportPath)
Write-Host ("Issues: " + $issues.Count + "  Critical: " + $critCount)

if ($critCount -gt 0) { exit 2 } else { exit 0 }
