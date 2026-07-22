@echo off
setlocal EnableExtensions
title Specter Ultimate Warfare Expansion ? Safe Installer (Phases A-I)
cd /d "%~dp0"

echo.
echo ============================================================
echo  Specter Ultimate Warfare Expansion - Safe Patch Installer
echo  Phases A-I  ^|  Backup + Merge + Verify + Report
echo ============================================================
echo.
echo  Rules:
echo   - Never permanently overwrites without backup
echo   - Never modifies .big / Data.zip / _SPEC_* archives
echo   - Merges patch\Data -^> game\Data
echo   - Merges patch\Art  -^> game\Art
echo   - Verifies with SYNC_MANIFEST.sha256
echo.

REM Prefer Windows PowerShell 5.1 (ships with Windows). Fall back to pwsh if present.
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_SpecterPatch.ps1" %*
set "ERR=%ERRORLEVEL%"

echo.
if "%ERR%"=="0" (
  echo INSTALL COMPLETED SUCCESSFULLY.
) else (
  echo INSTALL FAILED  ^(exit code %ERR%^).
  echo See messages above. Original files were backed up when replaced.
)
echo.
pause
exit /b %ERR%
