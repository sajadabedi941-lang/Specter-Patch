@echo off
setlocal EnableExtensions
title SPECTER GAME BOOT FIX - VERIFY
cd /d "%~dp0"
chcp 65001 >nul 2>&1
set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo SPECTER GAME BOOT FIX ? VERIFY
echo.

if not exist "%SCRIPTDIR%\VERIFY_SPECTER_GAME_BOOT_FIX.ps1" (
  echo [ERROR] VERIFY_SPECTER_GAME_BOOT_FIX.ps1 missing.
  pause & exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

set "GAMEROOT="
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; return (Test-Path -LiteralPath (Join-Path $x 'Data\INI\Object\Specter')) }; if(T $p){ $p; exit 0 }; $c=$p; 1..6 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; try { Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select game folder'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' } } catch { 'NEED_FOLDER' }"`) do set "GAMEROOT=%%I"

if not defined GAMEROOT ( echo VERIFY FAILED & pause & exit /b 1 )
if /I "%GAMEROOT%"=="CANCEL" ( pause & exit /b 1 )
if /I "%GAMEROOT%"=="INVALID" ( echo VERIFY FAILED & pause & exit /b 1 )
if /I "%GAMEROOT%"=="NEED_FOLDER" ( echo VERIFY FAILED & pause & exit /b 1 )

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\VERIFY_SPECTER_GAME_BOOT_FIX.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%" -ReportPath "%SCRIPTDIR%\VERIFY_REPORT.txt"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo VERIFY PASS
) else (
  echo VERIFY FAIL ? see VERIFY_REPORT.txt
)
pause
endlocal
exit /b %RC%
