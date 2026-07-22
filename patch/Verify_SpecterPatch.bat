@echo off
setlocal EnableExtensions
title Specter Patch ? Verify SYNC_MANIFEST
cd /d "%~dp0"

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Verify_SpecterPatch.ps1" %*
set "ERR=%ERRORLEVEL%"
echo.
pause
exit /b %ERR%
