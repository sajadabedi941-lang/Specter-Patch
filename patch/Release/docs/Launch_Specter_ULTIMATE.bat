@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Ultimate Expansion Launcher
cd /d "%~dp0"

set "ROOTFILE=%~dp0SpecterGameRoot.path"
set "APPDATAFILE=%LOCALAPPDATA%\SpecterUltimateExpansion\SpecterGameRoot.path"
set "GAMEROOT="

if exist "%ROOTFILE%" (
  set /p GAMEROOT=<"%ROOTFILE%"
)
if not defined GAMEROOT if exist "%APPDATAFILE%" (
  set /p GAMEROOT=<"%APPDATAFILE%"
)

if defined GAMEROOT (
  set "GAMEROOT=!GAMEROOT:"=!"
)

if not defined GAMEROOT (
  rem Try parent / this folder
  if exist "%~dp0generals.exe" set "GAMEROOT=%~dp0"
  if exist "%~dp0Generals.exe" set "GAMEROOT=%~dp0"
)

if not defined GAMEROOT (
  echo.
  echo Specter GameRoot not found.
  echo Run Install_SpecterPatch.exe first, or enter the game folder path.
  echo.
  set /p "GAMEROOT=GameRoot: "
  set "GAMEROOT=!GAMEROOT:"=!"
)

if not exist "!GAMEROOT!\generals.exe" if not exist "!GAMEROOT!\Generals.exe" (
  echo.
  echo ERROR: generals.exe not found in:
  echo   !GAMEROOT!
  echo.
  pause
  exit /b 1
)

set "EXE=!GAMEROOT!\generals.exe"
if not exist "!EXE!" set "EXE=!GAMEROOT!\Generals.exe"

echo Launching Specter from:
echo   !EXE!
echo.
pushd "!GAMEROOT!"
start "" "!EXE!"
popd
exit /b 0
