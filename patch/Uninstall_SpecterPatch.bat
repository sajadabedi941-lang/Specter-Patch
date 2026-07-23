@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Ultimate Warfare Expansion - Rollback / Uninstall
cd /d "%~dp0"

echo.
echo ============================================================
echo  Specter Ultimate Warfare Expansion - Rollback / Uninstall
echo ============================================================
echo.
echo  This will:
echo   - Restore backed-up original files
echo   - Remove overlay files added by the patch installer
echo   - NEVER delete .big / Data.zip / _SPEC_* archives
echo.

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

if exist "%~dp0Uninstall_SpecterPatch.ps1" (
  "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall_SpecterPatch.ps1" %*
  set "ERR=!ERRORLEVEL!"
) else (
  echo PowerShell uninstall script missing.
  echo Manual rollback: restore files from SpecterPatch_Backup\<timestamp>\
  set "ERR=1"
)

echo.
if "!ERR!"=="0" (
  echo UNINSTALL / ROLLBACK COMPLETED.
) else (
  echo UNINSTALL FAILED  ^(exit code !ERR!^).
)
echo.
pause
exit /b !ERR!
