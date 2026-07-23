param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$PatchDir
)
$ErrorActionPreference = "Stop"

function Test-GameRoot([string]$path) {
  if (-not $path) { return $false }
  if (-not (Test-Path -LiteralPath $path)) { return $false }
  $data = Join-Path $path "Data"
  if (-not (Test-Path -LiteralPath $data)) { return $false }
  $exes = @(
    (Join-Path $path "generals.exe"),
    (Join-Path $path "Generals.exe"),
    (Join-Path $path "GeneralsZH.exe"),
    (Join-Path $path "generalszh.exe")
  )
  foreach ($e in $exes) {
    if (Test-Path -LiteralPath $e) { return $true }
  }
  return $false
}

$PatchDir = $PatchDir.Trim().Trim('"')
if (-not (Test-Path -LiteralPath $PatchDir)) {
  Write-Output "INVALID"
  exit 0
}

# 1) Patch folder itself is the game root (extracted into GameRoot)
if (Test-GameRoot $PatchDir) {
  Write-Output $PatchDir
  exit 0
}

# 2) Parent of patch folder is the game root (patch subfolder inside GameRoot)
$parent = Split-Path -Parent $PatchDir
if ($parent -and (Test-GameRoot $parent)) {
  Write-Output $parent
  exit 0
}

# 3) Walk up a few levels (e.g. ...\GameRoot\patch\fix\)
$cursor = $PatchDir
for ($i = 0; $i -lt 4; $i++) {
  $cursor = Split-Path -Parent $cursor
  if (-not $cursor) { break }
  if (Test-GameRoot $cursor) {
    Write-Output $cursor
    exit 0
  }
}

# 4) Ask user to select folder (handles spaces; no typing)
try {
  Add-Type -AssemblyName System.Windows.Forms | Out-Null
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = "Select your Generals Zero Hour / Specter game folder (contains Data\ and generals.exe)"
  $dialog.ShowNewFolderButton = $false
  if ($parent -and (Test-Path -LiteralPath $parent)) {
    $dialog.SelectedPath = $parent
  } elseif (Test-Path -LiteralPath $PatchDir) {
    $dialog.SelectedPath = $PatchDir
  }
  $result = $dialog.ShowDialog()
  if ($result -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Output "CANCEL"
    exit 0
  }
  $chosen = $dialog.SelectedPath
  if (Test-GameRoot $chosen) {
    Write-Output $chosen
    exit 0
  }
  Write-Output "INVALID"
  exit 0
} catch {
  Write-Output "INVALID"
  exit 0
}
