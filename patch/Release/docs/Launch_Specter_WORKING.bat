@echo off
setlocal EnableExtensions
title Specter Ultimate Expansion Launcher

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Could not open launcher folder.
  pause
  exit /b 1
)

set "PATCHDIR=%~dp0"
if "%PATCHDIR:~-1%"=="\" set "PATCHDIR=%PATCHDIR:~0,-1%"

REM Game root is the parent of this patch folder
for %%I in ("%PATCHDIR%\..") do set "GAMEROOT=%%~fI"

set "EXE="
if exist "%GAMEROOT%\generals.exe" set "EXE=%GAMEROOT%\generals.exe"
if not defined EXE if exist "%GAMEROOT%\Generals.exe" set "EXE=%GAMEROOT%\Generals.exe"

if not defined EXE (
  echo ERROR: generals.exe not found.
  echo.
  echo Expected game folder:
  echo   %GAMEROOT%
  echo.
  echo Place this patch folder inside your Generals Zero Hour
  echo / Specter game directory and try again.
  echo.
  pause
  exit /b 1
)

echo Starting Specter...
echo   %EXE%
echo.
pushd "%GAMEROOT%"
start "" "%EXE%"
popd
exit /b 0
