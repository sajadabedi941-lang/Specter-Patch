<#
.SYNOPSIS
  Read-only Specter crash diagnosis from ReleaseCrashInfo.txt.
  Finds failing INI / Object, checks references, writes CRASH_REFERENCE_REPORT.txt.
  Does NOT modify, delete, or modify any game files.
#>
param(
  [Parameter(Mandatory = $false)]
  [Alias("LiteralPath", "Path")]
  [string]$GameRoot,

  [Parameter(Mandatory = $false)]
  [string]$ScriptDir,

  [Parameter(Mandatory = $false)]
  [string]$CrashInfoPath,

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

function Find-CrashInfo([string]$gameRoot, [string]$scriptDir) {
  $names = @("ReleaseCrashInfo.txt", "CrashInfo.txt", "releasecrashinfo.txt")
  $dirs = New-Object System.Collections.Generic.List[string]
  if ($gameRoot) { $dirs.Add($gameRoot) | Out-Null }
  if ($scriptDir) { $dirs.Add($scriptDir) | Out-Null }
  if ($gameRoot) {
    $dirs.Add((Join-Path $gameRoot "Data")) | Out-Null
    $dirs.Add((Join-Path $gameRoot "Logs")) | Out-Null
  }
  foreach ($d in $dirs) {
    if (-not $d -or -not (Test-Path -LiteralPath $d)) { continue }
    foreach ($n in $names) {
      $p = Join-Path $d $n
      if (Test-Path -LiteralPath $p) { return $p }
    }
  }
  # Newest ReleaseCrashInfo*.txt under game root
  if ($gameRoot -and (Test-Path -LiteralPath $gameRoot)) {
    $hits = @(Get-ChildItem -LiteralPath $gameRoot -Filter "ReleaseCrashInfo*.txt" -File -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending)
    if ($hits.Count -gt 0) { return $hits[0].FullName }
  }
  return $null
}

function Parse-CrashInfo([string]$text) {
  $result = [pscustomobject]@{
    RawText     = $text
    IniRelPath  = $null
    IniHint     = $null
    ObjectName  = $null
    MissingKind = $null
    MissingName = $null
    ParseNotes  = New-Object System.Collections.Generic.List[string]
  }

  # Error parsing INI file '...' / "..."
  if ($text -match '(?i)Error parsing INI file\s+[''"]([^''"]+\.ini)[''"]') {
    $result.IniHint = $Matches[1]
    $result.ParseNotes.Add("Matched: Error parsing INI file") | Out-Null
  }
  elseif ($text -match '(?i)(?:INI file|File|Loading)\s*[:=]\s*[''"]?([^\r\n''"]+?\.ini)[''"]?') {
    $result.IniHint = $Matches[1].Trim()
    $result.ParseNotes.Add("Matched: File/INI path line") | Out-Null
  }
  elseif ($text -match '(?i)(Data[\\/]INI[\\/]Object[\\/]Specter[\\/][^\r\n''"]+\.ini)') {
    $result.IniHint = $Matches[1]
    $result.ParseNotes.Add("Matched: Specter INI path in crash text") | Out-Null
  }

  # Object name
  if ($text -match '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+Object(?:\s+named)?\s+[''"]?([A-Za-z0-9_\-]+)[''"]?') {
    $result.ObjectName = $Matches[1].Trim('"', "'")
    $result.MissingKind = "Object"
    $result.MissingName = $result.ObjectName
    $result.ParseNotes.Add("Matched: missing Object") | Out-Null
  }
  elseif ($text -match '(?i)\bObject\s*[:=]\s*[''"]?([A-Za-z0-9_\-]+)[''"]?') {
    $result.ObjectName = $Matches[1].Trim('"', "'")
    $result.ParseNotes.Add("Matched: Object = name") | Out-Null
  }
  elseif ($text -match '(?im)^\s*Object\s+([A-Za-z0-9_\-]+)\s*$') {
    $result.ObjectName = $Matches[1]
    $result.ParseNotes.Add("Matched: Object header style line in crash dump") | Out-Null
  }

  # Named missing template kinds
  $kinds = @(
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+Weapon(?:\s+named|\s+template)?\s+(\S+)'; Kind = 'Weapon' },
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+Armor(?:\s+named)?\s+(\S+)'; Kind = 'Armor' },
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+CommandSet(?:\s+named)?\s+(\S+)'; Kind = 'CommandSet' },
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+CommandButton(?:\s+named)?\s+(\S+)'; Kind = 'CommandButton' },
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+Locomotor(?:\s+named)?\s+(\S+)'; Kind = 'Locomotor' },
    @{ Re = '(?i)(?:Could not find|Unable to find|Missing|Unknown)\s+Model(?:\s+named)?\s+(\S+)'; Kind = 'Model' }
  )
  foreach ($k in $kinds) {
    if ($text -match $k.Re) {
      $result.MissingKind = $k.Kind
      $result.MissingName = $Matches[1].Trim().Trim('"', "'")
      if (-not $result.ObjectName -and $k.Kind -eq 'Object') { $result.ObjectName = $result.MissingName }
      $result.ParseNotes.Add("Matched: missing " + $k.Kind) | Out-Null
      break
    }
  }

  if ($result.IniHint) {
    $h = $result.IniHint -replace '/', '\'
    if ($h -match '(?i)Object\\Specter\\(.+)$') {
      $result.IniRelPath = $Matches[1]
    } elseif ($h -match '(?i)Specter\\(.+)$') {
      $result.IniRelPath = $Matches[1]
    } else {
      $result.IniRelPath = [IO.Path]::GetFileName($h)
    }
  }

  return $result
}

function Get-FixSuggestion([string]$kind, [string]$name, [string]$status) {
  switch ($kind) {
    "Weapon" {
      return "Add or restore 'Weapon $name' in Data\INI\Weapon_*.ini (or the faction weapon INI), and ensure that file loads."
    }
    "Armor" {
      return "Add or restore 'Armor $name' in an Armor INI under Data\INI\, or retarget Armor = to an existing armor set."
    }
    "CommandSet" {
      return "Add or restore 'CommandSet $name' in Data\INI\CommandSet_*.ini, or change CommandSet = on the Object to an existing set."
    }
    "CommandButton" {
      return "Add or restore 'CommandButton $name' in Data\INI\CommandButton_*.ini, or remove/replace the button slot in the CommandSet."
    }
    "Locomotor" {
      return "Add or restore 'Locomotor $name' in a Locomotor INI under Data\INI\, or retarget Locomotor = to an existing locomotor."
    }
    "Object" {
      return "Add or restore 'Object $name' under Data\INI\Object\Specter\ (correct faction folder), or fix the Prerequisite/Weapon ProjectileObject reference."
    }
    "Model" {
      return "Ensure the W3D/model asset for '$name' exists in the game Art folders, or change Model = to a model that ships with Specter/stock ZH."
    }
    "Draw" {
      return "Draw module type must be a valid engine draw (e.g. W3DModelDraw). Fix the Draw = line syntax / ModuleTag."
    }
    "Prerequisite" {
      return "Ensure prerequisite Object '$name' exists under Specter (or base game), or remove/replace that Prerequisites Object = line."
    }
    default {
      return "Locate the definition for '$name' ($kind) in Specter/Data\INI or retarget the reference."
    }
  }
}

# Built-in / ignore tokens
$IgnoreNames = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
@(
  "NONE","None","Default","NULL","Null","Yes","No","True","False",
  "PRIMARY","SECONDARY","TERTIARY","PRIMARY_WEAPON","SECONDARY_WEAPON",
  "SET_NORMAL","SET_TAXIING","SET_LANDING","SET_TAKEOFF","SET_ULTRA_ACCURATE",
  "W3DModelDraw","W3DTruckDraw","W3DTankDraw","W3DDependencyModelDraw","W3DScienceModelDraw",
  "ActiveBody","HighlanderBody","UndeadBody","StructureBody","TankDraw","SupplyTruckDraw"
) | ForEach-Object { [void]$IgnoreNames.Add($_) }

$WeaponSlots = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
@("PRIMARY","SECONDARY","TERTIARY","QUATERNARY","QUINARY") | ForEach-Object { [void]$WeaponSlots.Add($_) }

function Add-Def([hashtable]$map, [string]$name, [string]$file, [int]$line) {
  if (-not $name -or $IgnoreNames.Contains($name)) { return }
  if (-not $map.ContainsKey($name)) {
    $map[$name] = New-Object System.Collections.Generic.List[string]
  }
  $map[$name].Add(("{0} : L{1}" -f $file, $line)) | Out-Null
}

function Build-DefinitionIndex([string]$specterRoot, [string]$iniRoot) {
  $idx = @{
    Object        = @{}
    Weapon        = @{}
    Armor         = @{}
    CommandSet    = @{}
    CommandButton = @{}
    Locomotor     = @{}
  }

  Write-Host "  Indexing Specter Object INIs..."
  $specterFiles = @(Get-ChildItem -LiteralPath $specterRoot -Recurse -Filter *.ini -File -ErrorAction Stop)
  $i = 0
  foreach ($f in $specterFiles) {
    $i++
    if (($i % 300) -eq 0) { Write-Host ("    Specter index: $i / $($specterFiles.Count)") }
    $rel = "Object\Specter\" + $f.FullName.Substring($specterRoot.Length).TrimStart('\', '/')
    $lines = [System.IO.File]::ReadAllLines($f.FullName)
    for ($n = 0; $n -lt $lines.Count; $n++) {
      $s = $lines[$n].Trim()
      if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }
      if ($s -match '^(?i)Object\s+(\S+)\s*$') { Add-Def $idx.Object $Matches[1] $rel ($n + 1) }
      if ($s -match '^(?i)Weapon\s+(\S+)\s*$') { Add-Def $idx.Weapon $Matches[1] $rel ($n + 1) }
      if ($s -match '^(?i)Armor\s+(\S+)\s*$') { Add-Def $idx.Armor $Matches[1] $rel ($n + 1) }
      if ($s -match '^(?i)CommandSet\s+(\S+)\s*$') { Add-Def $idx.CommandSet $Matches[1] $rel ($n + 1) }
      if ($s -match '^(?i)CommandButton\s+(\S+)\s*$') { Add-Def $idx.CommandButton $Matches[1] $rel ($n + 1) }
      if ($s -match '^(?i)Locomotor\s+(\S+)\s*$') { Add-Def $idx.Locomotor $Matches[1] $rel ($n + 1) }
    }
  }

  Write-Host "  Indexing Data\INI definitions (Weapon/Armor/CommandSet/...)..."
  if (Test-Path -LiteralPath $iniRoot) {
    $iniFiles = @(Get-ChildItem -LiteralPath $iniRoot -Recurse -Filter *.ini -File -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -notmatch '[\\/]Object[\\/]Specter[\\/]' })
    $j = 0
    foreach ($f in $iniFiles) {
      $j++
      if (($j % 200) -eq 0) { Write-Host ("    Data\INI index: $j / $($iniFiles.Count)") }
      $rel = $f.FullName.Substring($iniRoot.Length).TrimStart('\', '/')
      $rel = "INI\" + $rel
      try { $lines = [System.IO.File]::ReadAllLines($f.FullName) } catch { continue }
      for ($n = 0; $n -lt $lines.Count; $n++) {
        $s = $lines[$n].Trim()
        if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }
        if ($s -match '^(?i)Object\s+(\S+)\s*$') { Add-Def $idx.Object $Matches[1] $rel ($n + 1) }
        if ($s -match '^(?i)Weapon\s+(\S+)\s*$') { Add-Def $idx.Weapon $Matches[1] $rel ($n + 1) }
        if ($s -match '^(?i)Armor\s+(\S+)\s*$') { Add-Def $idx.Armor $Matches[1] $rel ($n + 1) }
        if ($s -match '^(?i)CommandSet\s+(\S+)\s*$') { Add-Def $idx.CommandSet $Matches[1] $rel ($n + 1) }
        if ($s -match '^(?i)CommandButton\s+(\S+)\s*$') { Add-Def $idx.CommandButton $Matches[1] $rel ($n + 1) }
        if ($s -match '^(?i)Locomotor\s+(\S+)\s*$') { Add-Def $idx.Locomotor $Matches[1] $rel ($n + 1) }
      }
    }
  }

  return @{ Index = $idx; SpecterFileCount = $specterFiles.Count }
}

function Extract-References([string]$iniPath, [string]$objectFilter) {
  $refs = New-Object System.Collections.Generic.List[object]
  $lines = [System.IO.File]::ReadAllLines($iniPath)
  $currentObject = $null
  $inPrereq = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $n = $i + 1
    $raw = $lines[$i]
    $s = $raw.Trim()
    if (-not $s -or $s.StartsWith(";") -or $s.StartsWith("//")) { continue }

    if ($s -match '^(?i)Object\s+(\S+)\s*$') {
      $currentObject = $Matches[1]
      $inPrereq = $false
      continue
    }
    if ($objectFilter -and $currentObject -and ($currentObject -ne $objectFilter)) {
      # still track prereq/end for structure, but skip collecting refs for other objects
      if ($s -match '(?i)^Prerequisites\b') { $inPrereq = $true; continue }
      if ($s -match '(?i)^End\b') { if ($inPrereq) { $inPrereq = $false }; continue }
      continue
    }

    if ($s -match '(?i)^Prerequisites\b') { $inPrereq = $true; continue }
    if ($s -match '(?i)^End\b') {
      if ($inPrereq) { $inPrereq = $false }
      continue
    }

    # WeaponSet / Weapon =
    if ($s -match '(?i)^Weapon\s*=\s*(\S+)(?:\s+(\S+))?') {
      $a = $Matches[1]; $b = $Matches[2]
      $wname = if ($b -and $WeaponSlots.Contains($a)) { $b } else { $a }
      if ($wname -and -not $IgnoreNames.Contains($wname) -and -not $WeaponSlots.Contains($wname)) {
        $refs.Add([pscustomobject]@{ Kind = "Weapon"; Name = $wname; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }
    if ($s -match '(?i)^WeaponTemplate\s*=\s*(\S+)') {
      $wname = $Matches[1]
      if (-not $IgnoreNames.Contains($wname)) {
        $refs.Add([pscustomobject]@{ Kind = "Weapon"; Name = $wname; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # Armor
    if ($s -match '(?i)^Armor\s*=\s*(\S+)') {
      $an = $Matches[1]
      if (-not $IgnoreNames.Contains($an)) {
        $refs.Add([pscustomobject]@{ Kind = "Armor"; Name = $an; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # Draw (module type)
    if ($s -match '(?i)^Draw\s*=\s*(\S+)') {
      $dn = $Matches[1]
      $refs.Add([pscustomobject]@{ Kind = "Draw"; Name = $dn; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
    }

    # Model
    if ($s -match '(?i)^Model\s*=\s*(\S+)') {
      $mn = $Matches[1]
      if (-not $IgnoreNames.Contains($mn)) {
        $refs.Add([pscustomobject]@{ Kind = "Model"; Name = $mn; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # CommandSet
    if ($s -match '(?i)^CommandSet\s*=\s*(\S+)') {
      $cn = $Matches[1]
      if (-not $IgnoreNames.Contains($cn)) {
        $refs.Add([pscustomobject]@{ Kind = "CommandSet"; Name = $cn; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # CommandButton (rare on Object; also 1 = Command_Xxx inside sets handled later)
    if ($s -match '(?i)^CommandButton\s*=\s*(\S+)') {
      $bn = $Matches[1]
      if (-not $IgnoreNames.Contains($bn)) {
        $refs.Add([pscustomobject]@{ Kind = "CommandButton"; Name = $bn; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # Locomotor = SET_NORMAL Name
    if ($s -match '(?i)^Locomotor\s*=\s*(\S+)(?:\s+(\S+))?') {
      $a = $Matches[1]; $b = $Matches[2]
      $lname = if ($b) { $b } else { $a }
      if ($lname -and -not $IgnoreNames.Contains($lname)) {
        $refs.Add([pscustomobject]@{ Kind = "Locomotor"; Name = $lname; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # Prerequisite Object =
    if ($inPrereq -and $s -match '(?i)^Object\s*=\s*(\S+)') {
      $on = $Matches[1]
      if (-not $IgnoreNames.Contains($on)) {
        $refs.Add([pscustomobject]@{ Kind = "Prerequisite"; Name = $on; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }

    # ProjectileObject often causes object ref crashes
    if ($s -match '(?i)^ProjectileObject\s*=\s*(\S+)') {
      $on = $Matches[1]
      if (-not $IgnoreNames.Contains($on)) {
        $refs.Add([pscustomobject]@{ Kind = "Object"; Name = $on; Line = $n; Object = $currentObject; Context = $s }) | Out-Null
      }
    }
  }

  return $refs
}

function Resolve-CommandSetButtons([string]$iniRoot, [string]$commandSetName, [hashtable]$buttonIndex) {
  $found = New-Object System.Collections.Generic.List[object]
  if (-not $iniRoot -or -not (Test-Path -LiteralPath $iniRoot)) { return $found }
  $files = @(Get-ChildItem -LiteralPath $iniRoot -Recurse -Filter *.ini -File -ErrorAction SilentlyContinue)
  foreach ($f in $files) {
    $text = $null
    try { $text = [System.IO.File]::ReadAllText($f.FullName) } catch { continue }
    if ($text -notmatch ("(?im)^\s*CommandSet\s+" + [regex]::Escape($commandSetName) + "\s*$")) { continue }
    $lines = $text -split "`r?`n"
    $in = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
      $s = $lines[$i].Trim()
      if ($s -match ("(?i)^CommandSet\s+" + [regex]::Escape($commandSetName) + "\s*$")) { $in = $true; continue }
      if ($in -and $s -match '(?i)^CommandSet\s+') { break }
      if ($in -and $s -match '(?i)^End\s*$') { break }
      if ($in -and $s -match '^\d+\s*=\s*(\S+)') {
        $btn = $Matches[1]
        if ($IgnoreNames.Contains($btn)) { continue }
        $exists = $buttonIndex.ContainsKey($btn)
        $found.Add([pscustomobject]@{ Name = $btn; Line = ($i + 1); File = $f.FullName; Exists = $exists }) | Out-Null
      }
    }
  }
  return $found
}

function Find-ObjectIni([string]$specterRoot, [string]$objectName) {
  $hits = New-Object System.Collections.Generic.List[object]
  $files = @(Get-ChildItem -LiteralPath $specterRoot -Recurse -Filter *.ini -File)
  foreach ($f in $files) {
    $lines = [System.IO.File]::ReadAllLines($f.FullName)
    for ($i = 0; $i -lt $lines.Count; $i++) {
      $s = $lines[$i].Trim()
      if ($s -match ("(?i)^Object\s+" + [regex]::Escape($objectName) + "\s*$")) {
        $hits.Add([pscustomobject]@{
          FullPath = $f.FullName
          Rel = $f.FullName.Substring($specterRoot.Length).TrimStart('\', '/')
          Line = $i + 1
        }) | Out-Null
        break
      }
    }
  }
  return $hits
}

function Resolve-IniPath([string]$specterRoot, [string]$relOrName) {
  if (-not $relOrName) { return $null }
  $cand = Join-Path $specterRoot ($relOrName -replace '/', '\')
  if (Test-Path -LiteralPath $cand) { return (Get-Item -LiteralPath $cand).FullName }
  # search by filename
  $name = [IO.Path]::GetFileName($relOrName)
  $hits = @(Get-ChildItem -LiteralPath $specterRoot -Recurse -Filter $name -File -ErrorAction SilentlyContinue)
  if ($hits.Count -eq 1) { return $hits[0].FullName }
  if ($hits.Count -gt 1) { return $hits[0].FullName }
  return $null
}

function Test-ModelAsset([string]$gameRoot, [string]$modelName) {
  if (-not $gameRoot -or -not $modelName) { return $false }
  $patterns = @(
    (Join-Path $gameRoot ("Art\W3D\" + $modelName + ".w3d")),
    (Join-Path $gameRoot ("Art\W3D\" + $modelName + ".W3D")),
    (Join-Path $gameRoot ("Data\Art\W3D\" + $modelName + ".w3d")),
    (Join-Path $gameRoot ("Art\" + $modelName + ".w3d"))
  )
  foreach ($p in $patterns) {
    if (Test-Path -LiteralPath $p) { return $true }
  }
  # loose search (may be slow — limit)
  $art = Join-Path $gameRoot "Art"
  if (Test-Path -LiteralPath $art) {
    $hit = Get-ChildItem -LiteralPath $art -Recurse -Filter ($modelName + ".w3d") -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $true }
  }
  return $false
}

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if (-not $ScriptDir) {
  if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
  else { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
}
$ScriptDir = $ScriptDir.Trim().TrimEnd('\', '/')

Write-Host ""
Write-Host "============================================================"
Write-Host " Specter CRASH REFERENCE DIAGNOSIS (read-only)"
Write-Host "============================================================"
Write-Host ""

if (-not $GameRoot) { $GameRoot = Find-GameRoot $ScriptDir }
if (-not $GameRoot -or -not (Test-SpecterRoot $GameRoot)) {
  throw "GameRoot not found (need Data\INI\Object\Specter\)."
}
$GameRoot = $GameRoot.TrimEnd('\', '/')
$Specter = Join-Path $GameRoot "Data\INI\Object\Specter"
$IniRoot = Join-Path $GameRoot "Data\INI"

if (-not $ReportPath) {
  $ReportPath = Join-Path $ScriptDir "CRASH_REFERENCE_REPORT.txt"
}

if (-not $CrashInfoPath) {
  $CrashInfoPath = Find-CrashInfo $GameRoot $ScriptDir
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("SPECTER CRASH REFERENCE REPORT")
[void]$sb.AppendLine("==============================")
[void]$sb.AppendLine(("GeneratedUtc : " + (Get-Date).ToUniversalTime().ToString("o")))
[void]$sb.AppendLine(("GameRoot     : " + $GameRoot))
[void]$sb.AppendLine(("Specter      : " + $Specter))
[void]$sb.AppendLine("Mode         : READ-ONLY (no file modifications)")
[void]$sb.AppendLine("")

if (-not $CrashInfoPath -or -not (Test-Path -LiteralPath $CrashInfoPath)) {
  [void]$sb.AppendLine("CRASH INFO")
  [void]$sb.AppendLine("----------")
  [void]$sb.AppendLine("ReleaseCrashInfo.txt NOT FOUND.")
  [void]$sb.AppendLine("Place ReleaseCrashInfo.txt in the game folder (next to Generals.exe / Data\),")
  [void]$sb.AppendLine("or copy it next to this tool, then run again.")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("FINAL VERDICT: NO_CRASH_INFO")
  [System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
  Write-Host "ReleaseCrashInfo.txt not found."
  Write-Host ("Report: " + $ReportPath)
  exit 3
}

$crashText = [System.IO.File]::ReadAllText($CrashInfoPath)
$parsed = Parse-CrashInfo $crashText

Write-Host ("CrashInfo : " + $CrashInfoPath)
Write-Host ("INI hint  : " + $(if ($parsed.IniHint) { $parsed.IniHint } else { "(none)" }))
Write-Host ("Object    : " + $(if ($parsed.ObjectName) { $parsed.ObjectName } else { "(none)" }))
Write-Host ""

[void]$sb.AppendLine("CRASH INFO")
[void]$sb.AppendLine("----------")
[void]$sb.AppendLine(("File        : " + $CrashInfoPath))
[void]$sb.AppendLine(("INI hint    : " + $(if ($parsed.IniHint) { $parsed.IniHint } else { "(none parsed)" })))
[void]$sb.AppendLine(("Object name : " + $(if ($parsed.ObjectName) { $parsed.ObjectName } else { "(none parsed)" })))
[void]$sb.AppendLine(("Crash named missing : " + $(if ($parsed.MissingKind) { ($parsed.MissingKind + " " + $parsed.MissingName) } else { "(none)" })))
[void]$sb.AppendLine("Parse notes:")
foreach ($n in $parsed.ParseNotes) { [void]$sb.AppendLine("  - $n") }
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Crash text excerpt (first 40 lines):")
$excerpt = ($crashText -split "`r?`n" | Select-Object -First 40) -join [Environment]::NewLine
[void]$sb.AppendLine($excerpt)
[void]$sb.AppendLine("")

# Resolve broken INI file
$brokenFull = $null
$brokenRel = $null
if ($parsed.IniRelPath) {
  $brokenFull = Resolve-IniPath $Specter $parsed.IniRelPath
}
if (-not $brokenFull -and $parsed.IniHint) {
  $brokenFull = Resolve-IniPath $Specter ([IO.Path]::GetFileName($parsed.IniHint))
}
if (-not $brokenFull -and $parsed.ObjectName) {
  Write-Host ("Searching Specter for Object " + $parsed.ObjectName + "...")
  $hits = Find-ObjectIni $Specter $parsed.ObjectName
  if ($hits.Count -ge 1) {
    $brokenFull = $hits[0].FullPath
    $brokenRel = $hits[0].Rel
    if ($hits.Count -gt 1) {
      [void]$sb.AppendLine(("NOTE: Object '{0}' found in {1} files; using first: {2}" -f $parsed.ObjectName, $hits.Count, $brokenRel))
      [void]$sb.AppendLine("")
    }
  }
}
if ($brokenFull -and -not $brokenRel) {
  $brokenRel = $brokenFull.Substring($Specter.Length).TrimStart('\', '/')
}

[void]$sb.AppendLine("BROKEN / FAILING FILE")
[void]$sb.AppendLine("---------------------")
if (-not $brokenFull) {
  [void]$sb.AppendLine("Could not resolve a Specter INI from ReleaseCrashInfo.txt.")
  [void]$sb.AppendLine("Fix suggestion: Confirm the crash log contains a Data\INI\Object\Specter\...\.ini path")
  [void]$sb.AppendLine("               or an Object name that exists under Specter.")
  [void]$sb.AppendLine("")
  [void]$sb.AppendLine("FINAL VERDICT: UNRESOLVED_TARGET")
  [System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
  Write-Host "Could not resolve failing INI."
  exit 2
}
[void]$sb.AppendLine(("Full path : " + $brokenFull))
[void]$sb.AppendLine(("Relative  : " + $brokenRel))
[void]$sb.AppendLine("")

# If object name missing, take first Object in file
if (-not $parsed.ObjectName) {
  $m = [regex]::Match([System.IO.File]::ReadAllText($brokenFull), '(?im)^\s*Object\s+(\S+)\s*$')
  if ($m.Success) {
    $parsed.ObjectName = $m.Groups[1].Value
    [void]$sb.AppendLine(("Inferred Object name from INI: " + $parsed.ObjectName))
    [void]$sb.AppendLine("")
  }
}

Write-Host "Building definition indexes (Specter + Data\INI)..."
$built = Build-DefinitionIndex $Specter $IniRoot
$idx = $built.Index

Write-Host ("Extracting references from: " + $brokenRel)
$refs = Extract-References $brokenFull $parsed.ObjectName

# Expand CommandSet -> CommandButtons
$extraBtnMissing = New-Object System.Collections.Generic.List[object]
$commandSetNames = @($refs | Where-Object { $_.Kind -eq "CommandSet" } | ForEach-Object { $_.Name } | Select-Object -Unique)
foreach ($csName in $commandSetNames) {
  $btns = Resolve-CommandSetButtons $IniRoot $csName $idx.CommandButton
  foreach ($b in $btns) {
    if (-not $b.Exists) {
      $extraBtnMissing.Add([pscustomobject]@{
        Kind = "CommandButton"; Name = $b.Name; Line = $b.Line
        Object = $parsed.ObjectName; Context = ("via CommandSet " + $csName)
        CommandSetFile = $b.File
      }) | Out-Null
    }
  }
}

function Find-InIndex([hashtable]$map, [string]$name) {
  if (-not $name) { return $null }
  if ($map.ContainsKey($name)) { return $map[$name] }
  return $null
}

$missing = New-Object System.Collections.Generic.List[object]
$ok = New-Object System.Collections.Generic.List[object]

foreach ($r in $refs) {
  $kind = $r.Kind
  $name = $r.Name
  $status = "OK"
  $where = ""
  $inSpecter = $false

  switch ($kind) {
    "Weapon" {
      $hit = Find-InIndex $idx.Weapon $name
      if ($hit) {
        $where = ($hit -join " | ")
        $inSpecter = ($where -match '(?i)Object\\Specter\\')
      } else { $status = "MISSING" }
    }
    "Armor" {
      $hit = Find-InIndex $idx.Armor $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "CommandSet" {
      $hit = Find-InIndex $idx.CommandSet $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "CommandButton" {
      $hit = Find-InIndex $idx.CommandButton $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "Locomotor" {
      $hit = Find-InIndex $idx.Locomotor $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "Object" {
      $hit = Find-InIndex $idx.Object $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "Prerequisite" {
      $hit = Find-InIndex $idx.Object $name
      if ($hit) { $where = ($hit -join " | "); $inSpecter = ($where -match '(?i)Object\\Specter\\') }
      else { $status = "MISSING" }
    }
    "Draw" {
      if ($IgnoreNames.Contains($name) -or $name -match '(?i)^W3D') {
        $status = "OK"; $where = "engine draw module"
      } else {
        $status = "MISSING"; $where = ""
      }
    }
    "Model" {
      $asset = Test-ModelAsset $GameRoot $name
      # Also see if any Specter INI mentions same model (weak signal)
      if ($asset) {
        $status = "OK"; $where = "Art asset found under game folder"
      } else {
        $status = "MISSING_OR_IN_BIG"
        $where = "Not found as loose .w3d under Art\ (may still exist inside .big)"
      }
    }
    default { $status = "UNKNOWN_KIND" }
  }

  $item = [pscustomobject]@{
    Kind = $kind; Name = $name; Line = $r.Line; Object = $r.Object
    Context = $r.Context; Status = $status; Where = $where; InSpecter = $inSpecter
  }

  if ($status -eq "MISSING" -or $status -eq "MISSING_OR_IN_BIG") {
    $missing.Add($item) | Out-Null
  } else {
    $ok.Add($item) | Out-Null
  }
}

foreach ($b in $extraBtnMissing) {
  $missing.Add([pscustomobject]@{
    Kind = "CommandButton"; Name = $b.Name; Line = $b.Line; Object = $b.Object
    Context = $b.Context; Status = "MISSING"; Where = ""; InSpecter = $false
  }) | Out-Null
}

# If crash log named a specific missing item, ensure it appears
if ($parsed.MissingKind -and $parsed.MissingName) {
  $already = @($missing | Where-Object { $_.Kind -eq $parsed.MissingKind -and $_.Name -eq $parsed.MissingName }).Count -gt 0
  if (-not $already) {
    $map = switch ($parsed.MissingKind) {
      "Weapon" { $idx.Weapon }
      "Armor" { $idx.Armor }
      "CommandSet" { $idx.CommandSet }
      "CommandButton" { $idx.CommandButton }
      "Locomotor" { $idx.Locomotor }
      "Object" { $idx.Object }
      "Prerequisite" { $idx.Object }
      default { @{} }
    }
    $hit = Find-InIndex $map $parsed.MissingName
    if (-not $hit) {
      $missing.Add([pscustomobject]@{
        Kind = $parsed.MissingKind; Name = $parsed.MissingName; Line = 0
        Object = $parsed.ObjectName; Context = "named in ReleaseCrashInfo.txt"
        Status = "MISSING"; Where = ""; InSpecter = $false
      }) | Out-Null
    }
  }
}

[void]$sb.AppendLine("REFERENCE CHECK SUMMARY")
[void]$sb.AppendLine("-----------------------")
[void]$sb.AppendLine(("Object analyzed     : " + $(if ($parsed.ObjectName) { $parsed.ObjectName } else { "(file-wide)" })))
[void]$sb.AppendLine(("References checked  : " + $refs.Count))
[void]$sb.AppendLine(("OK / resolved       : " + $ok.Count))
[void]$sb.AppendLine(("Missing / suspicious: " + $missing.Count))
[void]$sb.AppendLine(("Specter INIs indexed: " + $built.SpecterFileCount))
[void]$sb.AppendLine(("Weapons indexed     : " + $idx.Weapon.Count))
[void]$sb.AppendLine(("Armors indexed      : " + $idx.Armor.Count))
[void]$sb.AppendLine(("CommandSets indexed : " + $idx.CommandSet.Count))
[void]$sb.AppendLine(("CommandButtons idx  : " + $idx.CommandButton.Count))
[void]$sb.AppendLine(("Locomotors indexed  : " + $idx.Locomotor.Count))
[void]$sb.AppendLine(("Objects indexed     : " + $idx.Object.Count))
[void]$sb.AppendLine("")

[void]$sb.AppendLine("MISSING REFERENCES")
[void]$sb.AppendLine("------------------")
if ($missing.Count -eq 0) {
  [void]$sb.AppendLine("(none — all checked references were found in Specter/Data\INI, or Model may live in .big)")
} else {
  foreach ($m in ($missing | Sort-Object Kind, Name, Line)) {
    [void]$sb.AppendLine(("BROKEN FILE       : {0}" -f $brokenFull))
    [void]$sb.AppendLine(("OBJECT            : {0}" -f $(if ($m.Object) { $m.Object } else { $parsed.ObjectName })))
    [void]$sb.AppendLine(("MISSING REFERENCE : {0} = {1}" -f $m.Kind, $m.Name))
    [void]$sb.AppendLine(("LINE NUMBER       : {0}" -f $m.Line))
    [void]$sb.AppendLine(("CONTEXT           : {0}" -f $m.Context))
    [void]$sb.AppendLine(("STATUS            : {0}" -f $m.Status))
    [void]$sb.AppendLine(("SPECTER SEARCH    : not found as a definition under Object\Specter (also checked Data\INI)"))
    [void]$sb.AppendLine(("FIX SUGGESTION    : {0}" -f (Get-FixSuggestion $m.Kind $m.Name $m.Status)))
    [void]$sb.AppendLine("")
  }
}

[void]$sb.AppendLine("RESOLVED REFERENCES (sample)")
[void]$sb.AppendLine("----------------------------")
$shown = 0
foreach ($o in ($ok | Sort-Object Kind, Name)) {
  if ($shown -ge 40) { [void]$sb.AppendLine("(... truncated ...)"); break }
  [void]$sb.AppendLine(("  OK  {0,-14} {1,-40} L{2}  [{3}]" -f $o.Kind, $o.Name, $o.Line, $o.Where))
  $shown++
}
if ($ok.Count -eq 0) { [void]$sb.AppendLine("  (none collected)") }
[void]$sb.AppendLine("")

$verdict = if ($missing.Count -eq 0) { "PASS_OR_NO_MISSING_INI_REFS" } else { "MISSING_REFERENCES_FOUND" }
[void]$sb.AppendLine("FINAL VERDICT: $verdict")
[void]$sb.AppendLine("NOTE: Definitions that exist only inside stock .big archives are not indexed.")
[void]$sb.AppendLine("      MISSING here means not found in loose Data\INI / Object\Specter files.")

[System.IO.File]::WriteAllText($ReportPath, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
Write-Host ""
Write-Host ("Missing refs: " + $missing.Count)
Write-Host ("Report: " + $ReportPath)
Write-Host ("VERDICT: " + $verdict)
Write-Host ""

if ($missing.Count -gt 0) { exit 2 } else { exit 0 }
