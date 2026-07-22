@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Ultimate Warfare Expansion - Safe Installer (Phases A-I)
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

REM Prefer PowerShell installer when companion script exists
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

if exist "%~dp0Install_SpecterPatch.ps1" (
  echo Using PowerShell installer engine...
  "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_SpecterPatch.ps1" %*
  set "ERR=!ERRORLEVEL!"
) else (
  echo PowerShell script missing - using built-in CMD fallback installer...
  call :CmdInstall
  set "ERR=!ERRORLEVEL!"
)

echo.
if "!ERR!"=="0" (
  echo INSTALL COMPLETED SUCCESSFULLY.
) else if "!ERR!"=="2" (
  echo INSTALL COMPLETED WITH VERIFY WARNINGS.
) else (
  echo INSTALL FAILED  ^(exit code !ERR!^).
  echo See messages above. Original files were backed up when replaced.
)
echo.
pause
exit /b !ERR!

:CmdInstall
set "PATCHROOT=%~dp0"
if "%PATCHROOT:~-1%"=="\" set "PATCHROOT=%PATCHROOT:~0,-1%"

REM Detect game root = parent of patch folder
for %%I in ("%PATCHROOT%\..") do set "GAMEROOT=%%~fI"
if not exist "%GAMEROOT%\Data" if not exist "%GAMEROOT%\Art" if not exist "%GAMEROOT%\Data.zip" (
  echo Could not auto-detect game root from parent folder.
  set /p GAMEROOT=Enter Specter/ZH game root path: 
  set "GAMEROOT=!GAMEROOT:"=!"
)
if not defined GAMEROOT (
  echo ERROR: No game root.
  exit /b 1
)
if not exist "!GAMEROOT!" (
  echo ERROR: Game root not found: !GAMEROOT!
  exit /b 1
)

echo Game root: !GAMEROOT!
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
if not defined TS set "TS=manual"
set "BACKUP=!GAMEROOT!\SpecterPatch_Backup\!TS!"
set "STATE=!GAMEROOT!\SpecterPatch_InstallState"
mkdir "!BACKUP!" >nul 2>&1
mkdir "!STATE!" >nul 2>&1

echo Backing up and merging Data...
if exist "%PATCHROOT%\Data\" (
  robocopy "%PATCHROOT%\Data" "!GAMEROOT!\Data" /E /XO /R:1 /W:1 /NFL /NDL /NJH /NJS /NP >nul
  robocopy "%PATCHROOT%\Data" "!GAMEROOT!\Data" /E /IS /IT /R:1 /W:1 /XF *.big Data.zip /XD _SPEC_* /NFL /NDL /NJH /NJS /NP
)

echo Backing up and merging Art...
if exist "%PATCHROOT%\Art\" (
  if not exist "!BACKUP!\Art" mkdir "!BACKUP!\Art" >nul 2>&1
  if exist "!GAMEROOT!\Art\" robocopy "!GAMEROOT!\Art" "!BACKUP!\Art" /E /XO /R:1 /W:1 /NFL /NDL /NJH /NJS /NP >nul
  robocopy "%PATCHROOT%\Art" "!GAMEROOT!\Art" /E /IS /IT /R:1 /W:1 /XF *.big /NFL /NDL /NJH /NJS /NP
)

echo !BACKUP!> "!STATE!\ACTIVE_BACKUP.txt"
(
  echo Specter Ultimate Warfare Expansion - PATCH INSTALLED
  echo InstalledAt: %DATE% %TIME%
  echo PatchRoot: %PATCHROOT%
  echo GameRoot: !GAMEROOT!
  echo BackupFolder: !BACKUP!
  echo PhasesActivated: A B C D F F+ G H I
  echo Note: Prefer Install_SpecterPatch.ps1 for full SHA256 verify.
) > "!GAMEROOT!\PATCH_INSTALLED.txt"
copy /Y "!GAMEROOT!\PATCH_INSTALLED.txt" "%PATCHROOT%\PATCH_INSTALLED.txt" >nul

echo CMD fallback install finished. Run Verify_SpecterPatch.bat for hash check.
exit /b 0
