@echo off
setlocal EnableExtensions
title SPECTER ENGINE REPAIR FINAL - INSTALL
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  SPECTER FULL ENGINE REPAIR FINAL
echo  INSTALL — scan + apply Fixed\ + auto-repair + verify
echo ============================================================
echo.
echo  Close the game before continuing.
echo.

if not exist "%SCRIPTDIR%\AUTO_REPAIR_ENGINE.ps1" (
  echo [ERROR] AUTO_REPAIR_ENGINE.ps1 missing from this folder.
  pause & exit /b 1
)
if not exist "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" (
  echo [ERROR] SCAN_ALL_SPECTER_INI.ps1 missing from this folder.
  pause & exit /b 1
)
if not exist "%SCRIPTDIR%\Fixed" (
  echo [ERROR] Fixed\ folder missing from this package.
  pause & exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/5] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] Folder missing Data\INI\Object\Specter\
  echo         Copy SPECTER_ENGINE_REPAIR_FINAL next to your game Data\ folder.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="NEED_FOLDER" (
  echo [ERROR] Could not open folder picker.
  echo         Copy this folder into the game root and run again.
  pause & exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo.

echo [2/5] Pre-scan (before repair)...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\SCAN_REPORT_BEFORE.txt"
echo         Wrote SCAN_REPORT_BEFORE.txt
echo.

echo [3/5] Applying Fixed\ files + auto-repairing remaining broken INIs...
echo         Backups go to: Specter_ENGINE_REPAIR_BACKUP\date_time\
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\AUTO_REPAIR_ENGINE.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\Repair_Report.txt" -FixedOutDir "%SCRIPTDIR%\Fixed" -ApplyFixedPayload
set "REPERR=%ERRORLEVEL%"
echo.

echo [4/5] Post-scan (after repair)...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\SCAN_REPORT_AFTER.txt"
set "AFTERERR=%ERRORLEVEL%"
echo         Wrote SCAN_REPORT_AFTER.txt
echo.

echo [5/5] Result
echo ------------------------------------------------------------
if not "%AFTERERR%"=="0" (
  echo  FAILURE — critical INI issues remain.
  echo  See: Repair_Report.txt
  echo       SCAN_REPORT_AFTER.txt
  echo ------------------------------------------------------------
  echo.
  pause
  exit /b 1
)

if not "%REPERR%"=="0" (
  echo  WARNING — repair step reported issues, but final scan PASS.
  echo  See: Repair_Report.txt
  echo ------------------------------------------------------------
  echo.
  pause
  exit /b 0
)

echo  SUCCESS — Specter ENGINE REPAIR installed.
echo  Broken INI files were replaced in:
echo    Data\INI\Object\Specter\
echo  Report: Repair_Report.txt
echo  Backup: Specter_ENGINE_REPAIR_BACKUP\
echo  Undo:   UNINSTALL_SPECTER_REPAIR.bat
echo ------------------------------------------------------------
echo.
echo  You can now launch Generals Zero Hour / Specter.
echo.
pause
endlocal
exit /b 0
