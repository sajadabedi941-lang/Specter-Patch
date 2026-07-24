@echo off
setlocal EnableExtensions
title Specter Load Test
cd /d "%~dp0"

chcp 65001 >nul 2>&1
set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo.
echo ============================================================
echo  TEST_SPECTER_LOAD
echo ============================================================
echo.

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\TEST_SPECTER_LOAD.ps1" -ScriptDir "%SCRIPTDIR%"
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
  echo TEST FAILED — see TEST_SPECTER_LOAD_REPORT.txt
) else (
  echo TEST PASSED — no critical INI parse defects detected.
)
echo.
pause
exit /b %ERR%
