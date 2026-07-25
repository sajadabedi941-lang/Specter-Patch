@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter - Multi-Unit INI Playable BIG Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER PLAYABLE BIG INSTALLER
echo  Multi-unit INI repair package
echo ============================================================
echo.
echo  Copies rebuilt BIG archives into Specter GameRoot:
echo    - _SPEC_DATA_ONE.big
echo    - _SPEC_ART_ONE.big
echo.

set "SRC=%~dp0"
set "GAMEROOT=%~1"

if not defined GAMEROOT (
  echo Enter the full path to your Specter GameRoot
  echo ^(folder that contains generals.exe and the current BIG files^).
  echo.
  set /p "GAMEROOT=GameRoot: "
)

if not defined GAMEROOT (
  echo.
  echo ERROR: GameRoot was not provided.
  echo Usage: Install_SpecterPatch.bat "D:\Games\Specter"
  echo.
  pause
  exit /b 1
)

set "GAMEROOT=%GAMEROOT:"=%"

if not exist "!GAMEROOT!\generals.exe" (
  if not exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
    echo.
    echo ERROR: "!GAMEROOT!" does not look like a Specter GameRoot.
    echo.
    pause
    exit /b 1
  )
)

if not exist "!SRC!_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big not found next to this installer.
  pause
  exit /b 1
)
if not exist "!SRC!_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big not found next to this installer.
  pause
  exit /b 1
)

echo.
echo GameRoot: !GAMEROOT!
echo Source:   !SRC!
echo.

set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=!STAMP: =0!"
set "BACKUP=!GAMEROOT!\SpecterBIG_Backup_!STAMP!"

echo [1/3] Backing up existing BIG files ^(if present^)...
mkdir "!BACKUP!" >nul 2>&1
if exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
  copy /Y "!GAMEROOT!\_SPEC_DATA_ONE.big" "!BACKUP!\_SPEC_DATA_ONE.big" >nul
  echo   Backed up _SPEC_DATA_ONE.big
)
if exist "!GAMEROOT!\_SPEC_ART_ONE.big" (
  copy /Y "!GAMEROOT!\_SPEC_ART_ONE.big" "!BACKUP!\_SPEC_ART_ONE.big" >nul
  echo   Backed up _SPEC_ART_ONE.big
)
echo   Backup folder: !BACKUP!
echo.

echo [2/3] Installing new BIG files...
copy /Y "!SRC!_SPEC_DATA_ONE.big" "!GAMEROOT!\_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big
  pause
  exit /b 1
)
echo   Installed _SPEC_DATA_ONE.big

copy /Y "!SRC!_SPEC_ART_ONE.big" "!GAMEROOT!\_SPEC_ART_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_ART_ONE.big
  pause
  exit /b 1
)
echo   Installed _SPEC_ART_ONE.big
echo.

echo [3/3] Writing install marker...
(
  echo Specter Multi-Unit INI Playable Build installed.
  echo InstalledAt=!DATE! !TIME!
  echo GameRoot=!GAMEROOT!
  echo Backup=!BACKUP!
) > "!GAMEROOT!\SPECTER_MULTI_UNIT_INI_PLAYABLE_INSTALLED.txt"

echo.
echo ============================================================
echo  INSTALLATION COMPLETED SUCCESSFULLY
echo ============================================================
echo.
echo  New BIG files are now in:
echo    !GAMEROOT!\_SPEC_DATA_ONE.big
echo    !GAMEROOT!\_SPEC_ART_ONE.big
echo.
echo  Backup saved to:
echo    !BACKUP!
echo.
echo  Launch Command ^& Conquer Generals Zero Hour Specter.
echo.
pause
exit /b 0
