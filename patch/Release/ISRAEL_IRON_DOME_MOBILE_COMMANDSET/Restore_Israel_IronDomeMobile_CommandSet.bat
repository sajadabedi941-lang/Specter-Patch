@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Restore CommandSet.ini (Iron Dome Mobile slot 3)

cd /d "%~dp0"
set "PATCH_DIR=%~dp0"

set "HASH_SS1=f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"

set "GAME_ROOT="
if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if exist "%PATCH_DIR%Launch_Specter.bat" if not defined GAME_ROOT set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT (
  for %%I in ("%PATCH_DIR%..") do (
    if exist "%%~fI\generals.exe" set "GAME_ROOT=%%~fI\"
    if not defined GAME_ROOT if exist "%%~fI\Launch_Specter.bat" set "GAME_ROOT=%%~fI\"
  )
)
if not defined GAME_ROOT (
  echo ERROR: Game folder not found.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile_CommandSet\"
set "PACK_ORIG=%PATCH_DIR%backup_original\CommandSet.ini"

echo Restoring CommandSet.ini to the ss1 original.
echo Game folder:
echo   %GAME_ROOT%
echo.

set "RESTORED=0"
if exist "%BACKUP%launcher_CommandSet.ini" (
  copy /Y "%BACKUP%launcher_CommandSet.ini" "%GAME_ROOT%CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Could not restore launcher CommandSet.ini
    pause
    exit /b 1
  )
  fc /b "%BACKUP%launcher_CommandSet.ini" "%GAME_ROOT%CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Restored launcher file does not match backup.
    pause
    exit /b 1
  )
  echo   Restored %GAME_ROOT%CommandSet.ini
  set "RESTORED=1"
)
if exist "%BACKUP%Data_INI_CommandSet.ini" (
  if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
  copy /Y "%BACKUP%Data_INI_CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Could not restore Data\INI\CommandSet.ini
    pause
    exit /b 1
  )
  fc /b "%BACKUP%Data_INI_CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Restored Data\INI file does not match backup.
    pause
    exit /b 1
  )
  echo   Restored %GAME_ROOT%Data\INI\CommandSet.ini
  set "RESTORED=1"
)

if "%RESTORED%"=="0" (
  if not exist "%PACK_ORIG%" (
    echo ERROR: No live backup and no pack original.
    pause
    exit /b 1
  )
  echo   No live backup folder. Restoring pack ss1 original.
  if exist "%GAME_ROOT%CommandSet.ini" copy /Y "%PACK_ORIG%" "%GAME_ROOT%CommandSet.ini" >nul
  if exist "%GAME_ROOT%Data\INI\CommandSet.ini" copy /Y "%PACK_ORIG%" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
)

echo.
echo Restore finished. Slot 3 Iron Dome Mobile is removed.
pause
exit /b 0
