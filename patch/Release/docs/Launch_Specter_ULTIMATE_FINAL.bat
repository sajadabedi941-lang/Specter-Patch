@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Ultimate Expansion Launcher
cd /d "%~dp0"

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

set "GAMEROOT="

rem Prefer GameRoot detection: this folder, then parent
if exist "%HERE%\generals.exe" set "GAMEROOT=%HERE%"
if exist "%HERE%\Generals.exe" set "GAMEROOT=%HERE%"
if not defined GAMEROOT (
  for %%I in ("%HERE%\..") do set "PARENT=%%~fI"
  if exist "!PARENT!\generals.exe" set "GAMEROOT=!PARENT!"
  if exist "!PARENT!\Generals.exe" set "GAMEROOT=!PARENT!"
)

if not defined GAMEROOT if exist "%HERE%\SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt" (
  for /f "usebackq tokens=1,* delims==" %%A in ("%HERE%\SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt") do (
    if /I "%%A"=="GameRoot" set "GAMEROOT=%%B"
  )
)
if not defined GAMEROOT (
  for %%I in ("%HERE%\..") do set "PARENT=%%~fI"
  if exist "!PARENT!\SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt" (
    for /f "usebackq tokens=1,* delims==" %%A in ("!PARENT!\SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt") do (
      if /I "%%A"=="GameRoot" set "GAMEROOT=%%B"
    )
  )
)

if not defined GAMEROOT (
  echo.
  echo Could not find Specter GameRoot automatically.
  echo Enter the folder that contains generals.exe.
  echo.
  set /p "GAMEROOT=GameRoot: "
  set "GAMEROOT=!GAMEROOT:"=!"
)

set "EXE="
if exist "!GAMEROOT!\generals.exe" set "EXE=!GAMEROOT!\generals.exe"
if not defined EXE if exist "!GAMEROOT!\Generals.exe" set "EXE=!GAMEROOT!\Generals.exe"
if not defined EXE if exist "!GAMEROOT!\GeneralsZH.exe" set "EXE=!GAMEROOT!\GeneralsZH.exe"

if not defined EXE (
  echo.
  echo ERROR: generals.exe not found in:
  echo   !GAMEROOT!
  echo.
  pause
  exit /b 1
)

echo Launching Specter...
echo   !EXE!
echo.
pushd "!GAMEROOT!"
start "" "!EXE!"
popd
exit /b 0
