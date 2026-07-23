@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter RUNTIME CRASH FIX V2
cd /d "%~dp0"
echo.
echo  Specter RUNTIME CRASH FIX V2
echo  Removes flat Data\INI duplicates that crash initialization
echo  Automatic backup | No SHA256 verification
echo.
set "GAMEROOT=%~1"
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Runtime_Fix.ps1" %*
set "ERR=!ERRORLEVEL!"
echo.
if not "!ERR!"=="0" (
  echo FIX FINISHED WITH ERRORS ^(code !ERR!^).
) else (
  echo FIX COMPLETED.
)
echo.
pause
exit /b !ERR!
