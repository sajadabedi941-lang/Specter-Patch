@echo off
setlocal EnableExtensions
title Restore SPECTER BIGs (Iron Dome Mobile)

cd /d "%~dp0"
set "PATCH_DIR=%~dp0"

set "GAME_ROOT="
if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT (
  for %%I in ("%PATCH_DIR%..") do (
    if exist "%%~fI\generals.exe" set "GAME_ROOT=%%~fI\"
  )
)
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile\"
if not exist "%BACKUP%_SPEC_DATA_ONE.big" (
  echo ERROR: Backup not found:
  echo   %BACKUP%
  pause
  exit /b 1
)

echo Restoring BIGs from:
echo   %BACKUP%
copy /Y "%BACKUP%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if exist "%BACKUP%_SPEC_ART_ONE.big" copy /Y "%BACKUP%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
copy /Y "%BACKUP%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
if exist "%BACKUP%Data_INI_CommandSet.ini" (
  if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
  copy /Y "%BACKUP%Data_INI_CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
)
if exist "%BACKUP%Data_English_generals.csf" (
  if not exist "%GAME_ROOT%Data\English" mkdir "%GAME_ROOT%Data\English"
  copy /Y "%BACKUP%Data_English_generals.csf" "%GAME_ROOT%Data\English\generals.csf" >nul
)
echo Restored.
pause
exit /b 0
