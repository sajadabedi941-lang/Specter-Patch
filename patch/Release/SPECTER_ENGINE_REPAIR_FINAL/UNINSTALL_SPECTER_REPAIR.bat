@echo off
setlocal EnableExtensions
title SPECTER ENGINE REPAIR FINAL - UNINSTALL
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  SPECTER ENGINE REPAIR — UNINSTALL / RESTORE BACKUP
echo ============================================================
echo.
echo  This restores INI files from the newest backup under:
echo    Specter_ENGINE_REPAIR_BACKUP\
echo.

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/3] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] Folder missing Data\INI\Object\Specter\
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="NEED_FOLDER" (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo.

echo [2/3] Restoring newest backup...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $root='%GAMEROOT%'.TrimEnd('\'); $specter=Join-Path $root 'Data\INI\Object\Specter'; $bakRoot=Join-Path $root 'Specter_ENGINE_REPAIR_BACKUP'; if(-not (Test-Path -LiteralPath $bakRoot)){ Write-Host 'No Specter_ENGINE_REPAIR_BACKUP folder found.'; exit 2 }; $dirs=@(Get-ChildItem -LiteralPath $bakRoot -Directory | Sort-Object Name -Descending); if($dirs.Count -eq 0){ Write-Host 'Backup folder is empty.'; exit 2 }; $latest=$dirs[0].FullName; Write-Host ('Using backup: ' + $latest); $files=@(Get-ChildItem -LiteralPath $latest -Recurse -Filter *.ini -File); $n=0; foreach($f in $files){ $rel=$f.FullName.Substring($latest.Length).TrimStart('\','/'); $dest=Join-Path $specter $rel; $destDir=Split-Path -Parent $dest; [void][IO.Directory]::CreateDirectory($destDir); Copy-Item -LiteralPath $f.FullName -Destination $dest -Force; $n++; Write-Host ('  RESTORED: ' + $rel) }; Write-Host ('Restored ' + $n + ' files.'); $log=Join-Path '%SCRIPTDIR%' 'Repair_Report.txt'; $msg=@('SPECTER ENGINE REPAIR — UNINSTALL','================================','RestoredFrom: ' + $latest,'Files: ' + $n,'GeneratedUtc: ' + (Get-Date).ToUniversalTime().ToString('o'),'VERDICT: RESTORED'); [IO.File]::WriteAllText($log, ($msg -join [Environment]::NewLine) + [Environment]::NewLine)"
set "RC=%ERRORLEVEL%"
echo.

echo [3/3] Done.
if not "%RC%"=="0" (
  echo [ERROR] Restore failed. Code=%RC%
  echo         Make sure you ran INSTALL first so a backup exists.
  echo.
  pause
  exit /b %RC%
)

echo ============================================================
echo  UNINSTALL SUCCESS — originals restored from backup.
echo ============================================================
echo.
pause
endlocal
exit /b 0
