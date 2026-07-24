@echo off
setlocal EnableExtensions
title Specter ENGINE REPAIR
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter FULL ENGINE INI REPAIR
echo  Copy into game folder -^> Run this file -^> Wait -^> Done
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\AUTO_REPAIR_ENGINE.ps1" (
  echo [ERROR] AUTO_REPAIR_ENGINE.ps1 is missing.
  echo         Keep this BAT next to AUTO_REPAIR_ENGINE.ps1.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [STEP 1] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled. No folder selected.
  echo.
  pause
  exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] That folder does not contain Data\INI\Object\Specter\
  echo         Put this package inside your game folder and try again.
  echo.
  pause
  exit /b 1
)
if /I "%GAMEROOT%"=="NEED_FOLDER" (
  echo [ERROR] Could not open folder picker.
  echo         Copy this entire folder into your game root and run again.
  echo         Game root must contain: Data\INI\Object\Specter\
  echo.
  pause
  exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  echo         Copy this package into the folder that contains Data\
  echo.
  pause
  exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo.

echo [STEP 2] Running automatic scan + backup + repair + verify...
echo         This may take a minute. Please wait.
echo.
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\AUTO_REPAIR_ENGINE.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\REPAIR_REPORT.txt"
set "RC=%ERRORLEVEL%"
echo.

echo [STEP 3] Done. Report: REPAIR_REPORT.txt
echo         Backup folder (if anything was changed):
echo         Specter_ENGINE_REPAIR_BACKUP\date_time\
echo.

if not "%RC%"=="0" (
  echo ============================================================
  echo  REPAIR FINISHED WITH WARNINGS / ERRORS
  echo  Open REPAIR_REPORT.txt for details.
  echo ============================================================
  echo.
  pause
  exit /b %RC%
)

echo ============================================================
echo  SUCCESS — Specter ENGINE REPAIR complete
echo  You can now launch Generals Zero Hour / Specter.
echo ============================================================
echo.
pause
endlocal
exit /b 0
