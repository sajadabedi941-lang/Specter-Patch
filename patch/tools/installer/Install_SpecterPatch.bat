@echo off
setlocal EnableExtensions
title Specter Ultimate Expansion Installer

REM ============================================================
REM  Specter Ultimate Expansion - Clean Installer
REM  Place this folder inside your Generals Zero Hour / Specter
REM  game directory, then run this file as Administrator.
REM ============================================================

REM Always start in the folder where this BAT lives
cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Could not open installer folder.
  pause
  exit /b 1
)

set "PATCHDIR=%~dp0"
if "%PATCHDIR:~-1%"=="\" set "PATCHDIR=%PATCHDIR:~0,-1%"

echo.
echo ============================================================
echo  SPECTER ULTIMATE EXPANSION INSTALLER
echo ============================================================
echo.
echo Installer folder:
echo   %PATCHDIR%
echo.

REM ----- Request Administrator rights -----
net session >nul 2>&1
if errorlevel 1 (
  echo Requesting Administrator permission...
  echo.
  echo If a Windows security prompt appears, click Yes.
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  if errorlevel 1 (
    echo.
    echo ERROR: Administrator permission was not granted.
    echo Right-click Install_SpecterPatch.bat and choose:
    echo   Run as administrator
    echo.
    pause
    exit /b 1
  )
  exit /b 0
)

echo Running with Administrator permission.
echo.

REM ----- Check BIG files in installer folder -----
if not exist "%PATCHDIR%\_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big is missing from the installer folder.
  echo Expected:
  echo   %PATCHDIR%\_SPEC_DATA_ONE.big
  echo.
  pause
  exit /b 1
)
if not exist "%PATCHDIR%\_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big is missing from the installer folder.
  echo Expected:
  echo   %PATCHDIR%\_SPEC_ART_ONE.big
  echo.
  pause
  exit /b 1
)

REM ----- Detect game root = parent of this patch folder -----
for %%I in ("%PATCHDIR%\..") do set "GAMEROOT=%%~fI"

echo Checking game folder:
echo   %GAMEROOT%
echo.

if not exist "%GAMEROOT%\generals.exe" if not exist "%GAMEROOT%\Generals.exe" (
  echo ERROR: Wrong game folder.
  echo.
  echo Place the installer folder INSIDE your Command ^& Conquer
  echo Generals Zero Hour / Specter game directory, then run again.
  echo.
  echo The game folder must contain generals.exe
  echo Current detected folder:
  echo   %GAMEROOT%
  echo.
  pause
  exit /b 1
)

echo Game folder OK.
echo.

REM ----- Backup -----
set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=%STAMP: =0%"
set "STAMP=%STAMP:/=%"
set "STAMP=%STAMP:\=%"
set "STAMP=%STAMP::=%"
set "BACKUP=%GAMEROOT%\BACKUP_SPECTER_%STAMP%"

echo Creating backup folder...
mkdir "%BACKUP%" >nul 2>&1
if not exist "%BACKUP%\" (
  echo ERROR: Could not create backup folder:
  echo   %BACKUP%
  echo.
  pause
  exit /b 1
)

if exist "%GAMEROOT%\_SPEC_DATA_ONE.big" (
  copy /Y "%GAMEROOT%\_SPEC_DATA_ONE.big" "%BACKUP%\_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_DATA_ONE.big
    pause
    exit /b 1
  )
)
if exist "%GAMEROOT%\_SPEC_ART_ONE.big" (
  copy /Y "%GAMEROOT%\_SPEC_ART_ONE.big" "%BACKUP%\_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_ART_ONE.big
    pause
    exit /b 1
  )
)

echo Backup completed
echo   %BACKUP%
echo.

REM ----- Install -----
echo Installing Specter Patch...
echo.

copy /Y "%PATCHDIR%\_SPEC_DATA_ONE.big" "%GAMEROOT%\_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big
  echo Backup is still available in:
  echo   %BACKUP%
  echo.
  pause
  exit /b 1
)
echo   Copied _SPEC_DATA_ONE.big

copy /Y "%PATCHDIR%\_SPEC_ART_ONE.big" "%GAMEROOT%\_SPEC_ART_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_ART_ONE.big
  echo Backup is still available in:
  echo   %BACKUP%
  echo.
  pause
  exit /b 1
)
echo   Copied _SPEC_ART_ONE.big
echo.

if not exist "%GAMEROOT%\_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big not found in game folder after copy.
  pause
  exit /b 1
)
if not exist "%GAMEROOT%\_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big not found in game folder after copy.
  pause
  exit /b 1
)

echo Installation completed successfully
echo.
echo Game folder:
echo   %GAMEROOT%
echo Backup folder:
echo   %BACKUP%
echo.
echo You can now start the game with Launch_Specter.bat
echo or generals.exe
echo.
pause
exit /b 0
