@echo off
setlocal EnableExtensions
title Specter INI Repair - Uninstall / Restore Backup
cd /d "%~dp0"

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter INI Repair - UNINSTALL
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\Uninstall_Specter_INI_Repair.ps1" (
  echo [ERROR] Uninstall_Specter_INI_Repair.ps1 missing.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\Uninstall_Specter_INI_Repair.ps1" -ScriptDir "%SCRIPTDIR%"
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
  echo [ERROR] Uninstall failed.
  echo.
  pause
  exit /b %ERR%
)

echo ============================================================
echo UNINSTALL SUCCESSFUL
echo Backup restored.
echo ============================================================
echo.
pause
endlocal
exit /b 0
