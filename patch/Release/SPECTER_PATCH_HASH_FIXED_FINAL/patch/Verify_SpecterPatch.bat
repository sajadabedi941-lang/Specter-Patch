@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Patch - Verify SYNC_MANIFEST
cd /d "%~dp0"

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

if exist "%~dp0Verify_SpecterPatch.ps1" (
  "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Verify_SpecterPatch.ps1" %*
  set "ERR=!ERRORLEVEL!"
) else (
  echo Verify_SpecterPatch.ps1 missing. Cannot verify SYNC_MANIFEST.sha256
  set "ERR=1"
)

echo.
pause
exit /b !ERR!
