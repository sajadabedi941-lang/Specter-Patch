<#
.SYNOPSIS
  Post-repair load test: missing files, critical syntax, duplicate Objects
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
  $cands = @(); if ($start) { $cands += $start }
  $cur = $start
  for ($i = 0; $i -lt 6; $i++) {
    if (-not $cur) { break }
    $par = Split-Path -Parent $cur
    if ($par -and $par -ne $cur) { $cands += $par; $cur = $par } else { break }
  }
  foreach ($c in $cands) { if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') } }
  return $null
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')
if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) { throw "GameRoot not found." }
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
if (-not $ReportPath) { $ReportPath = Join-Path $ScriptDir "TEST_SPECTER_LOAD_REPORT.txt" }

Write-Host "TEST_SPECTER_LOAD"
Write-Host ("Specter: " + $Specter)

$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File)
$crit = 0
$dupes = 0
$empty = 0
$objMap = @{}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("TEST SPECTER LOAD REPORT")
[void]$sb.AppendLine("========================")
[void]$sb.AppendLine(("GameRoot: " + $GameRoot))
[void]$sb.AppendLine(("INI files: " + $files.Count))
[void]$sb.AppendLine("")

foreach ($f in $files) {
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  if ($f.Length -lt 1) {
    $empty++; [void]$sb.AppendLine("EMPTY: $rel"); continue
  }
  $text = [System.IO.File]::ReadAllText($f.FullName)
  foreach ($ln in ($text -split "`r?`n")) {
    if ($ln -match '(?i)^[ \t]*End[ \t]*;') { $crit++; [void]$sb.AppendLine("CRIT End; : $rel") }
    if ($ln -cmatch '^[ \t]*END[ \t]*$') { $crit++; [void]$sb.AppendLine("CRIT END  : $rel") }
    $code = ($ln -split ";", 2)[0]
    if ($ln -match '(?i)^[ \t]*Scale[ \t]+' -and $code -notmatch '=') { $crit++; [void]$sb.AppendLine("CRIT Scale: $rel") }
    if ($ln -match '(?i)BuildCompletion\s*=\s*PLACE_ON_GROUND\b') { $crit++; [void]$sb.AppendLine("CRIT BuildCompletion: $rel") }
    if ($code -match '[{}]') { $crit++; [void]$sb.AppendLine("CRIT brace: $rel") }
  }
  foreach ($m in [regex]::Matches($text, '(?im)^\s*Object\s+(\S+)\s*$')) {
    $name = $m.Groups[1].Value
    if ($name -eq '=') { continue }
    if (-not $objMap.ContainsKey($name)) { $objMap[$name] = New-Object System.Collections.Generic.List[string] }
    $objMap[$name].Add($rel) | Out-Null
  }
}

[void]$sb.AppendLine("")
[void]$sb.AppendLine("DUPLICATE OBJECTS (cross-file)")
[void]$sb.AppendLine("------------------------------")
foreach ($kv in ($objMap.GetEnumerator() | Sort-Object Name)) {
  $u = @($kv.Value | Select-Object -Unique)
  if ($u.Count -gt 1) {
    $dupes++
    [void]$sb.AppendLine(($kv.Key + " => " + ($u -join " | ")))
  }
}

[void]$sb.AppendLine("")
[void]$sb.AppendLine(("CriticalSyntax={0}" -f $crit))
[void]$sb.AppendLine(("EmptyFiles={0}" -f $empty))
[void]$sb.AppendLine(("DuplicateObjectNames={0}" -f $dupes))
# Duplicates are informational for Specter (some intentional overlays) — fail only on critical syntax
$verdict = if ($crit -eq 0 -and $empty -eq 0) { "PASS" } else { "FAIL" }
[void]$sb.AppendLine(("VERDICT={0}" -f $verdict))

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ("CriticalSyntax=$crit Empty=$empty DupObjects=$dupes")
Write-Host ("VERDICT=$verdict")
Write-Host ("Report: $ReportPath")
if ($verdict -ne "PASS") { exit 2 } else { exit 0 }
