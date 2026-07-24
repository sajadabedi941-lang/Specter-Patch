@echo off
setlocal EnableExtensions
title SPECTER GAME BOOT FIX - INSTALL
cd /d "%~dp0"
chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  SPECTER GAME BOOT FIX FINAL
echo  Deploys Fixed\ INIs into Data\INI\Object\Specter
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\INSTALL_SPECTER_GAME_BOOT_FIX.ps1" (
  echo [ERROR] INSTALL_SPECTER_GAME_BOOT_FIX.ps1 missing.
  echo INSTALL FAILED
  pause & exit /b 1
)
if not exist "%SCRIPTDIR%\Fixed" (
  echo [ERROR] Fixed\ folder missing.
  echo INSTALL FAILED
  pause & exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo [1/3] Detecting game folder...
set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if /I "%GAMEROOT%"=="CANCEL" ( echo INSTALL FAILED & pause & exit /b 1 )
if /I "%GAMEROOT%"=="INVALID" ( echo [ERROR] Missing Data\INI\Object\Specter\ & echo INSTALL FAILED & pause & exit /b 1 )
if /I "%GAMEROOT%"=="NEED_FOLDER" ( echo [ERROR] Copy this folder into the game root. & echo INSTALL FAILED & pause & exit /b 1 )
if not defined GAMEROOT ( echo INSTALL FAILED & pause & exit /b 1 )
echo         GameRoot: "%GAMEROOT%"
echo.

echo [2/3] Backing up + deploying Fixed\ files...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\INSTALL_SPECTER_GAME_BOOT_FIX.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo INSTALL FAILED
  pause
  exit /b %RC%
)
echo.

echo [3/3] Verifying boot-critical INI rules...
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\VERIFY_SPECTER_GAME_BOOT_FIX.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%"
set "VR=%ERRORLEVEL%"
echo.

if not "%VR%"=="0" (
  echo ============================================================
  echo INSTALL FAILED ? verification found remaining parse defects
  echo See VERIFY_REPORT.txt
  echo ============================================================
  pause
  exit /b 1
)

echo ============================================================
echo INSTALL SUCCESSFUL
echo Fixed Specter INIs deployed. Backup under:
echo   Specter_GAME_BOOT_FIX_BACKUP\date_time\
echo Launch Specter now and confirm main menu / Skirmish.
echo ============================================================
pause
endlocal
exit /b 0
