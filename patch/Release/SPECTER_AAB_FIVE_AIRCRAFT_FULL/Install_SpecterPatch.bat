@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter AAB Five-Aircraft Full BIG Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER - AAB FIVE-AIRCRAFT FULL RELEASE INSTALLER
echo ============================================================
echo.
echo  Replaces GameRoot BIG archives:
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
  echo ERROR: GameRoot was not provided.
  echo Usage: Install_SpecterPatch.bat "D:\Games\Specter"
  pause
  exit /b 1
)

set "GAMEROOT=%GAMEROOT:"=%"

if not exist "!GAMEROOT!\generals.exe" (
  if not exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
    echo ERROR: "!GAMEROOT!" does not look like a Specter GameRoot.
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

set "BAK=!GAMEROOT!\SpecterPatch_Backup_AAB_Five"
echo.
echo Creating backup folder: !BAK!
mkdir "!BAK!" 2>nul
if exist "!GAMEROOT!\_SPEC_DATA_ONE.big" copy /Y "!GAMEROOT!\_SPEC_DATA_ONE.big" "!BAK!\_SPEC_DATA_ONE.big" >nul
if exist "!GAMEROOT!\_SPEC_ART_ONE.big"  copy /Y "!GAMEROOT!\_SPEC_ART_ONE.big"  "!BAK!\_SPEC_ART_ONE.big" >nul

echo Copying _SPEC_DATA_ONE.big ...
copy /Y "!SRC!_SPEC_DATA_ONE.big" "!GAMEROOT!\_SPEC_DATA_ONE.big" >nul || goto :fail
echo Copying _SPEC_ART_ONE.big ...
copy /Y "!SRC!_SPEC_ART_ONE.big" "!GAMEROOT!\_SPEC_ART_ONE.big" >nul || goto :fail

echo.
echo INSTALLATION COMPLETED SUCCESSFULLY
echo Backup saved under: !BAK!
echo Launch Specter normally.
echo.
pause
exit /b 0

:fail
echo.
echo ERROR: Copy failed. Check permissions / disk space.
pause
exit /b 1
