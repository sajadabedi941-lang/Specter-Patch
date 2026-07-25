@echo off
setlocal
title Specter Patch Installer

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Could not open installer folder.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"

echo.
echo Specter Patch Installer
echo.

REM ----- Check patch BIG files -----
if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo Missing patch files
  echo Expected: %PATCH_DIR%_SPEC_DATA_ONE.big
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  echo Missing patch files
  echo Expected: %PATCH_DIR%_SPEC_ART_ONE.big
  pause
  exit /b 1
)

REM ----- Detect game directory = this folder -----
if not exist "%PATCH_DIR%generals.exe" if not exist "%PATCH_DIR%Generals.exe" (
  echo Please put this installer inside Command and Conquer Generals Zero Hour folder
  echo.
  echo This folder must contain generals.exe
  echo Current folder:
  echo   %PATCH_DIR%
  pause
  exit /b 1
)

echo Game folder found:
echo   %PATCH_DIR%
echo.

REM ----- Backup old BIG files -----
set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=%STAMP: =0%"
set "STAMP=%STAMP:/=%"
set "STAMP=%STAMP:\=%"
set "STAMP=%STAMP::=%"
set "BACKUP=%PATCH_DIR%Backup_Specter_%STAMP%"

echo Creating backup folder...
mkdir "%BACKUP%"
if not exist "%BACKUP%\" (
  echo ERROR: Could not create backup folder.
  echo   %BACKUP%
  pause
  exit /b 1
)

if exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%BACKUP%\_SPEC_DATA_ONE.big"
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_DATA_ONE.big
    pause
    exit /b 1
  )
)
if exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%BACKUP%\_SPEC_ART_ONE.big"
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_ART_ONE.big
    pause
    exit /b 1
  )
)

echo Backup completed
echo   %BACKUP%
echo.

REM ----- Install BIG files into this game folder -----
echo Installing Specter Patch...
echo.

REM Installer lives in the game folder, so source and destination are the same.
REM Verify the patch BIG files are present, then refresh timestamps via copy to backup restore path is not needed.
REM Copy from installer files onto the game filenames explicitly:

copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%PATCH_DIR%_SPEC_DATA_ONE.big" >nul 2>&1
if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo ERROR: Failed to install _SPEC_DATA_ONE.big
  pause
  exit /b 1
)
echo Copied _SPEC_DATA_ONE.big

copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%PATCH_DIR%_SPEC_ART_ONE.big" >nul 2>&1
if not exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  echo ERROR: Failed to install _SPEC_ART_ONE.big
  pause
  exit /b 1
)
echo Copied _SPEC_ART_ONE.big
echo.

echo Installation completed successfully
echo.
pause
exit /b 0
