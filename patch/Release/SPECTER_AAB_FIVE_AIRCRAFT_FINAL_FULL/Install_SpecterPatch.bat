@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter AAB Five-Aircraft FINAL FULL BIG Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER AAB FIVE-AIRCRAFT - FINAL FULL RELEASE
echo ============================================================
echo  Full replacement (NOT a small overlay):
echo    _SPEC_DATA_ONE.big
echo    _SPEC_ART_ONE.big
echo.
echo  Advanced Air Base builds ONLY:
echo    B-2, B-21, B-52, E-3 AWACS, AN-225
echo.

set "SRC=%~dp0"
set "GAMEROOT=%~1"
if not defined GAMEROOT (
  echo Enter Specter GameRoot path ^(folder with generals.exe / _SPEC_*.big^).
  set /p "GAMEROOT=GameRoot: "
)
if not defined GAMEROOT (
  echo ERROR: GameRoot required.
  echo Usage: Install_SpecterPatch.bat "D:\Games\Specter"
  pause
  exit /b 1
)
set "GAMEROOT=%GAMEROOT:"=%"

if not exist "!GAMEROOT!\generals.exe" if not exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
  echo ERROR: "!GAMEROOT!" is not a Specter GameRoot.
  pause
  exit /b 1
)
if not exist "!SRC!_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big missing next to installer.
  pause
  exit /b 1
)
if not exist "!SRC!_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big missing next to installer.
  pause
  exit /b 1
)

set "BAK=!GAMEROOT!\SpecterPatch_Backup_AAB_Five_Final_Full"
mkdir "!BAK!" 2>nul
if exist "!GAMEROOT!\_SPEC_DATA_ONE.big" copy /Y "!GAMEROOT!\_SPEC_DATA_ONE.big" "!BAK!\" >nul
if exist "!GAMEROOT!\_SPEC_ART_ONE.big"  copy /Y "!GAMEROOT!\_SPEC_ART_ONE.big"  "!BAK!\" >nul

echo Copying _SPEC_DATA_ONE.big ...
copy /Y "!SRC!_SPEC_DATA_ONE.big" "!GAMEROOT!\_SPEC_DATA_ONE.big" >nul || goto :fail
echo Copying _SPEC_ART_ONE.big ...
copy /Y "!SRC!_SPEC_ART_ONE.big" "!GAMEROOT!\_SPEC_ART_ONE.big" >nul || goto :fail

echo.
echo INSTALLATION COMPLETED SUCCESSFULLY
echo Backup saved to: !BAK!
echo Launch Specter normally.
pause
exit /b 0
:fail
echo ERROR: copy failed. Check permissions / disk space.
pause
exit /b 1
