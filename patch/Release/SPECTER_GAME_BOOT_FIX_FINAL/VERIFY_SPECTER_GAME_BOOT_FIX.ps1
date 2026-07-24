<#
.SYNOPSIS
  Verify boot-critical INI parse defects under Data\INI\Object\Specter after install.
#>
param(
  [Parameter(Mandatory = $false)][string]$GameRoot,
  [Parameter(Mandatory = $false)][string]$ScriptDir,
  [Parameter(Mandatory = $false)][string]$ReportPath
)
$ErrorActionPreference = "Stop"
function Test-SpecterRoot([string]$root) {
  if (-not $root) { return $false }
  return (Test-Path -LiteralPath (Join-Path $root "Data\INI\Object\Specter"))
}
function Find-GameRoot([string]$start) {
  $cands = @(); if ($start) { $cands += $start }
  $cur = $start
  for ($i = 0; $i -lt 8; $i++) {
    if (-not $cur) { break }
    $par = Split-Path -Parent $cur
    if ($par -and $par -ne $cur) { $cands += $par; $cur = $par } else { break }
  }
  foreach ($c in $cands) { if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') } }
  return $null
}
if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot } else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.TrimEnd('\', '/')
if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) { throw "GameRoot not found." }
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
if (-not $ReportPath) { $ReportPath = Join-Path $ScriptDir "VERIFY_REPORT.txt" }

$files = @(Get-ChildItem -LiteralPath $Specter -Recurse -Filter *.ini -File)
$issues = New-Object System.Collections.Generic.List[object]
$idx = 0
foreach ($f in $files) {
  $idx++
  if (($idx % 200) -eq 0) { Write-Host ("  Verify $idx / $($files.Count)") }
  $rel = $f.FullName.Substring($Specter.Length).TrimStart('\', '/')
  $lines = [IO.File]::ReadAllLines($f.FullName)
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $s = $lines[$i].Trim()
    $n = $i + 1
    if ($s -match '(?i)^End[ \t]*;') { $issues.Add("$rel L$n END_SEMI") | Out-Null }
    if ($s -cmatch '^END\s*$') { $issues.Add("$rel L$n UPPER_END") | Out-Null }
    if ($s -match '(?i)^BuildCompletion\s*=\s*PLACE_ON_GROUND\b') { $issues.Add("$rel L$n PLACE_ON_GROUND") | Out-Null }
    if ($s -match '(?i)^CommandSet\s*=\s*$' -or $s -match '(?i)^CommandSet\s*=\s*;') { $issues.Add("$rel L$n EMPTY_COMMANDSET") | Out-Null }
    $code = ($s -split ';', 2)[0]
    if ($code -match '[{}]') { $issues.Add("$rel L$n BRACE") | Out-Null }
  }
}

# Known targets
$known = @(
  "British Armed Forces\Airforce\Britain_F35B.ini",
  "British Armed Forces\Drones\Britain_CombatDrone.ini",
  "Turkey Armed Forces\Turkey_WeaponObjects.ini",
  "Israel Defense Forces\Buildings\Israel_CommandCenter.ini",
  "Israel Defense Forces\Buildings\Israel_MilitaryHQ.ini"
)

$sb = New-Object Text.StringBuilder
[void]$sb.AppendLine("VERIFY REPORT — SPECTER GAME BOOT FIX")
[void]$sb.AppendLine("=====================================")
[void]$sb.AppendLine(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine(("GameRoot     : " + $GameRoot))
[void]$sb.AppendLine(("Scanned      : " + $files.Count))
[void]$sb.AppendLine(("BootCritical : " + $issues.Count))
[void]$sb.AppendLine("")
[void]$sb.AppendLine("KNOWN TARGETS")
foreach ($k in $known) {
  $p = Join-Path $Specter $k
  $st = if (-not (Test-Path -LiteralPath $p)) { "NOT FOUND" } else {
    $hit = @($issues | Where-Object { $_ -like ($k.Replace('\','/') + '*') -or $_ -like ($k + '*') })
    if ($hit.Count) { "FAIL" } else { "OK" }
  }
  [void]$sb.AppendLine("  $st  $k")
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("ISSUES")
if ($issues.Count -eq 0) { [void]$sb.AppendLine("  (none)") }
else { foreach ($x in $issues) { [void]$sb.AppendLine("  $x") } }
$verdict = if ($issues.Count -eq 0) { "PASS" } else { "FAIL" }
[void]$sb.AppendLine("")
[void]$sb.AppendLine("FINAL VERDICT: $verdict")
[void]$sb.AppendLine("NOTE: This verifies boot-critical parse defects only. Launch the game on Windows for menu/Skirmish proof.")
[IO.File]::WriteAllText($ReportPath, $sb.ToString(), [Text.UTF8Encoding]::new($false))
Write-Host ("Boot-critical issues: $($issues.Count)  VERDICT: $verdict")
Write-Host ("Report: $ReportPath")
if ($issues.Count -gt 0) { exit 2 } else { exit 0 }
