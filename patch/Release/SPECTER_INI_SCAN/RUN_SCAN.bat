@echo off
setlocal EnableExtensions
title Specter INI SCAN
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter INI SCAN
echo  Read-only check of Data\INI\Object\Specter\*.ini
echo  Does NOT delete or modify game files
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\SCAN_SPECTER_INI.ps1" (
  echo [ERROR] SCAN_SPECTER_INI.ps1 is missing.
  echo         Keep RUN_SCAN.bat next to SCAN_SPECTER_INI.ps1.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/2] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] That folder does not contain Data\INI\Object\Specter\
  echo         Copy this folder next to your game Data\ folder and try again.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="NEED_FOLDER" (
  echo [ERROR] Could not open folder picker.
  echo         Copy this folder into the game root and double-click RUN_SCAN.bat again.
  pause & exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo.

echo [2/2] Scanning all Specter INI files...
echo.
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\SCAN_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\INI_ERROR_REPORT.txt"
set "RC=%ERRORLEVEL%"
echo.

echo ------------------------------------------------------------
if "%RC%"=="0" (
  echo  SCAN COMPLETE — no errors found.
) else (
  echo  SCAN COMPLETE — errors found. See INI_ERROR_REPORT.txt
)
echo  Report: INI_ERROR_REPORT.txt
echo  Backup copies of broken files ^(if any^):
echo    Specter_INI_SCAN_BACKUP\date_time\
echo  Game files were NOT modified or deleted.
echo ------------------------------------------------------------
echo.
pause
endlocal
exit /b %RC%
