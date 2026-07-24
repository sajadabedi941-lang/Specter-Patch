<#
.SYNOPSIS
  Install Specter GAME BOOT FIX — deploy Fixed\ INIs into Data\INI\Object\Specter
  Creates backup first. Does not touch .big archives.
#>
param(
  [Parameter(Mandatory = $false)]
  [string]$GameRoot,
  [Parameter(Mandatory = $false)]
  [string]$ScriptDir,
  [Parameter(Mandatory = $false)]
  [string]$ReportPath
)

$ErrorActionPreference = "Stop"

function Ensure-Directory([string]$p) {
  if ($p) { [void][IO.Directory]::CreateDirectory($p) }
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
  foreach ($c in $cands) { if (Test-SpecterRoot $c) { return $c.TrimEnd('\', '/') } }
  return $null
}

if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.TrimEnd('\', '/')
if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found (need Data\INI\Object\Specter)."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
$Fixed = Join-Path $ScriptDir "Fixed"
if (-not (Test-Path -LiteralPath $Fixed)) { throw "Fixed\ folder missing from package." }
if (-not $ReportPath) { $ReportPath = Join-Path $ScriptDir "FINAL_CRASH_FIX_REPORT.txt" }

$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Backup = Join-Path $GameRoot ("Specter_GAME_BOOT_FIX_BACKUP\" + $ts)
Ensure-Directory $Backup

Write-Host ("GameRoot : " + $GameRoot)
Write-Host ("Specter  : " + $Specter)
Write-Host ("Backup   : " + $Backup)
Write-Host ("Fixed    : " + $Fixed)

$files = @(Get-ChildItem -LiteralPath $Fixed -Recurse -Filter *.ini -File)
$n = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($Fixed.Length).TrimStart('\', '/')
  $dest = Join-Path $Specter $rel
  Ensure-Directory (Split-Path -Parent $dest)
  if (Test-Path -LiteralPath $dest) {
    $bak = Join-Path $Backup $rel
    Ensure-Directory (Split-Path -Parent $bak)
    Copy-Item -LiteralPath $dest -Destination $bak -Force
  }
  Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
  $n++
  Write-Host ("  REPLACED: " + $rel)
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("SPECTER GAME BOOT FIX — INSTALL LOG")
[void]$sb.AppendLine("===================================")
[void]$sb.AppendLine(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine(("GameRoot     : " + $GameRoot))
[void]$sb.AppendLine(("Backup       : " + $Backup))
[void]$sb.AppendLine(("FilesDeployed: " + $n))
[void]$sb.AppendLine("STATUS       : INSTALL COMPLETE — launch Specter on Windows to confirm main menu / Skirmish")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("See also: FINAL_CRASH_FIX_REPORT.txt, RUNTIME_CRASH_ITERATIONS.txt, NEW_FOLDER_FILE_VALIDATION.txt")
[System.IO.File]::WriteAllText((Join-Path $ScriptDir "INSTALL_LOG.txt"), $sb.ToString(), [Text.UTF8Encoding]::new($false))

# Append install note to final report without wiping static analysis
$append = @("", "---- INSTALL RUN ----", ("Utc: " + (Get-Date).ToUniversalTime().ToString("o")), ("GameRoot: " + $GameRoot), ("Deployed: " + $n), ("Backup: " + $Backup))
Add-Content -LiteralPath $ReportPath -Value ($append -join [Environment]::NewLine) -Encoding UTF8

Write-Host ("Deployed $n files.")
if ($n -le 0) { exit 2 }
exit 0
