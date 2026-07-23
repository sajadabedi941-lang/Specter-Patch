@echo off
setlocal EnableExtensions
title Specter FULL INI Repair - Uninstall / Rollback
cd /d "%~dp0"

REM ============================================================
REM  Rollback using backup created by RUN_SPECTER_FULL_REPAIR.bat
REM  GameRoot = this BAT's folder (%~dp0). No prompts for path.
REM ============================================================

chcp 65001 >nul 2>&1

set "GAMEROOT=%~dp0"
if "%GAMEROOT:~-1%"=="\" set "GAMEROOT=%GAMEROOT:~0,-1%"
set "SCRIPTDIR=%GAMEROOT%"

echo.
echo ============================================================
echo  Specter FULL INI Repair - UNINSTALL
echo ============================================================
echo.
echo Detected game path:
echo "%GAMEROOT%"
echo.

if not exist "%GAMEROOT%\Data\" (
  echo [ERROR] Data folder not found.
  echo Place this BAT inside the main game folder.
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPTDIR%\Uninstall_Specter_Full_Repair.ps1" (
  echo [ERROR] Uninstall_Specter_Full_Repair.ps1 missing next to this BAT.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo Restoring backup / removing installed repair files...
echo.

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\Uninstall_Specter_Full_Repair.ps1" -GameRoot "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo [ERROR] Uninstall failed.
  echo.
  pause
  exit /b %ERR%
)

echo.
echo ============================================================
echo UNINSTALL SUCCESSFUL
echo Specter FULL INI Repair rolled back.
echo ============================================================
echo.
echo Game path: "%GAMEROOT%"
echo.
pause
endlocal
exit /b 0
