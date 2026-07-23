@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter FULL INI REPAIR PASS
cd /d "%~dp0"

echo.
echo  Specter FULL INI REPAIR PASS
echo  Full New-folder audit + path repair + flat purge
echo.

set "GAMEROOT=%~1"
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

if not exist "%~dp0Install_Runtime_Fix.ps1" (
  echo [ERROR] Install_Runtime_Fix.ps1 missing.
  if not defined SPECTER_LAUNCHER pause
  exit /b 1
)

if defined GAMEROOT (
  "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Runtime_Fix.ps1" -GameRoot "%GAMEROOT%"
) else (
  "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Runtime_Fix.ps1"
)
set "ERR=!ERRORLEVEL!"

echo.
if not defined SPECTER_LAUNCHER pause
exit /b !ERR!
