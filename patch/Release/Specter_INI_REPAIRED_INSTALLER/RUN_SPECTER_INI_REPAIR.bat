@echo off
setlocal EnableExtensions
title Specter INI Repair - Installer
cd /d "%~dp0"

REM ============================================================
REM  Auto-detect game root, backup, install repaired INIs into
REM  Data\INI\Object\Specter\<Faction>\...  (never flat Data\INI)
REM ============================================================

chcp 65001 >nul 2>&1

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

echo.
echo ============================================================
echo  Specter INI Repair Installer
echo ============================================================
echo.

if not exist "%SCRIPTDIR%\Specter_INI_REPAIRED\" (
  echo [ERROR] Specter_INI_REPAIRED folder not found next to this BAT.
  echo Extract the full Specter_INI_REPAIRED_INSTALLER.zip first.
  echo.
  pause
  exit /b 1
)
if not exist "%SCRIPTDIR%\PlacementMap.txt" (
  echo [ERROR] PlacementMap.txt missing next to this BAT.
  echo.
  pause
  exit /b 1
)
if not exist "%SCRIPTDIR%\Install_Specter_INI_Repair.ps1" (
  echo [ERROR] Install_Specter_INI_Repair.ps1 missing.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\Install_Specter_INI_Repair.ps1" -ScriptDir "%SCRIPTDIR%"
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
  echo [ERROR] Installation failed.
  echo.
  pause
  exit /b %ERR%
)

echo ============================================================
echo INSTALL SUCCESSFUL
echo Repaired INI files installed.
echo ============================================================
echo.
echo Backup folder: Specter_INI_Backup\
echo To rollback, run UNINSTALL_SPECTER_INI_REPAIR.bat
echo.
pause
endlocal
exit /b 0
