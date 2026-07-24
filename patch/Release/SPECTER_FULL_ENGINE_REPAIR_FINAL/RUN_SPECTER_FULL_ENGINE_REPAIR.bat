@echo off
setlocal EnableExtensions
title Specter FULL ENGINE INI REPAIR
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter FULL ENGINE INI REPAIR
echo  Scan ALL Object\Specter INIs + auto-repair + verify
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" (
  echo [ERROR] SCAN_ALL_SPECTER_INI.ps1 missing.
  pause & exit /b 1
)
if not exist "%SCRIPTDIR%\AUTO_REPAIR_SPECTER_INI.ps1" (
  echo [ERROR] AUTO_REPAIR_SPECTER_INI.ps1 missing.
  pause & exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/5] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; $s=Join-Path $x 'Data\INI\Object\Specter'; return (Test-Path -LiteralPath $s) }; if(T $p){ $p; exit 0 }; $c=$p; 1..5 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (must contain Data\INI\Object\Specter)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" (
  echo [ERROR] Cancelled.
  pause & exit /b 1
)
if /I "%GAMEROOT%"=="INVALID" (
  echo [ERROR] Folder missing Data\INI\Object\Specter\
  pause & exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  pause & exit /b 1
)

echo        GameRoot: "%GAMEROOT%"
echo.

echo [2/5] Creating backup + scanning ALL Specter INI files...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\FULL_INI_SCAN_REPORT.txt"
set "SCANERR=%ERRORLEVEL%"
echo        Scan report: FULL_INI_SCAN_REPORT.txt
echo.

echo [3/5] Automatic repair of broken INI files...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\AUTO_REPAIR_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\FINAL_REPAIR_REPORT.txt" -FixedOutDir "%SCRIPTDIR%\Fixed"
set "REPERR=%ERRORLEVEL%"
echo.

echo [4/5] Verifying installation / re-scan...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\SCAN_ALL_SPECTER_INI.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\FULL_INI_SCAN_REPORT_AFTER.txt"
set "AFTERERR=%ERRORLEVEL%"
echo.

echo [5/5] Writing final status...
if not "%AFTERERR%"=="0" (
  echo.
  echo [ERROR] Critical INI parse issues remain. See FULL_INI_SCAN_REPORT_AFTER.txt
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo INSTALL SUCCESSFUL
echo Specter FULL ENGINE INI REPAIR complete.
echo ============================================================
echo.
echo Reports:
echo   FULL_INI_SCAN_REPORT.txt
echo   FULL_INI_SCAN_REPORT_AFTER.txt
echo   FINAL_REPAIR_REPORT.txt
echo Backup under: Specter_EngineRepair_Backup\
echo.
echo You can now launch Generals Zero Hour / Specter.
echo Optional: run TEST_SPECTER_LOAD.bat
echo.
pause
endlocal
exit /b 0
