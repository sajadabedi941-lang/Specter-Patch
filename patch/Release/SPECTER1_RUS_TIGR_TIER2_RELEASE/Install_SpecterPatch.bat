@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER1 RUS TIGR TIER2 RELEASE installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER1_RUS_TIGR_TIER2_RELEASE
echo ============================================================
echo  Copies _SPEC_DATA_ONE.big into the Zero Hour GameRoot.
echo  Does NOT replace ART.
echo  NOT WINDOWS GAMEPLAY VALIDATED
echo.

set "SRC=%~dp0"
set "GAMEROOT=%~1"
if not defined GAMEROOT (
  echo Enter Specter / Zero Hour GameRoot (folder with generals.exe).
  set /p "GAMEROOT=GameRoot: "
)
if not defined GAMEROOT (
  echo ERROR: GameRoot required.
  echo Usage: Install_SpecterPatch.bat "D:\Games\Generals Zero Hour"
  pause
  exit /b 1
)
set "GAMEROOT=%GAMEROOT:"=%"

if not exist "!GAMEROOT!\generals.exe" if not exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
  echo ERROR: "!GAMEROOT!" is not a Specter / Zero Hour GameRoot.
  pause
  exit /b 1
)
if not exist "!SRC!_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big missing next to installer.
  pause
  exit /b 1
)

set "BAK=!GAMEROOT!\SpecterPatch_Backup_RUS_TIGR_TIER2"
mkdir "!BAK!" 2>nul
if exist "!GAMEROOT!\_SPEC_DATA_ONE.big" copy /Y "!GAMEROOT!\_SPEC_DATA_ONE.big" "!BAK!\" >nul

echo Copying _SPEC_DATA_ONE.big ...
copy /Y "!SRC!_SPEC_DATA_ONE.big" "!GAMEROOT!\_SPEC_DATA_ONE.big" >nul || goto :fail

echo.
echo INSTALLATION COMPLETED SUCCESSFULLY
echo Backup saved to: !BAK!
echo ART was not changed.
echo NOT WINDOWS GAMEPLAY VALIDATED
pause
exit /b 0
:fail
echo ERROR: copy failed. Check permissions / disk space.
pause
exit /b 1
