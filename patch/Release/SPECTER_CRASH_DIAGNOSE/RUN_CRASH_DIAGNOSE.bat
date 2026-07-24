@echo off
setlocal EnableExtensions
title Specter CRASH REFERENCE DIAGNOSIS
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter CRASH REFERENCE DIAGNOSIS
echo  Reads ReleaseCrashInfo.txt — reports missing INI references
echo  Does NOT modify or modify any game files
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\DIAGNOSE_CRASH_REFERENCES.ps1" (
  echo [ERROR] DIAGNOSE_CRASH_REFERENCES.ps1 is missing.
  echo         Keep RUN_CRASH_DIAGNOSE.bat next to that script.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/3] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] Folder missing Data\INI\Object\Specter\
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="NEED_FOLDER" (
  echo [ERROR] Could not open folder picker. Copy this folder into the game root.
  pause & exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo.

echo [2/3] Looking for ReleaseCrashInfo.txt...
if exist "%GAMEROOT%\ReleaseCrashInfo.txt" (
  echo         Found: "%GAMEROOT%\ReleaseCrashInfo.txt"
) else if exist "%SCRIPTDIR%\ReleaseCrashInfo.txt" (
  echo         Found: "%SCRIPTDIR%\ReleaseCrashInfo.txt"
) else (
  echo         [WARN] Not found yet — the script will search and report.
)
echo.

echo [3/3] Diagnosing crash references (read-only)...
echo.
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\DIAGNOSE_CRASH_REFERENCES.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\CRASH_REFERENCE_REPORT.txt"
set "RC=%ERRORLEVEL%"
echo.

echo ------------------------------------------------------------
if "%RC%"=="0" (
  echo  DIAGNOSIS COMPLETE — no missing loose-INI references reported.
) else if "%RC%"=="3" (
  echo  NO ReleaseCrashInfo.txt FOUND
  echo  Copy it into the game folder or next to this tool, then re-run.
) else (
  echo  DIAGNOSIS COMPLETE — see missing references in the report.
)
echo  Report: CRASH_REFERENCE_REPORT.txt
echo  Game files were NOT modified.
echo ------------------------------------------------------------
echo.
pause
endlocal
exit /b %RC%
