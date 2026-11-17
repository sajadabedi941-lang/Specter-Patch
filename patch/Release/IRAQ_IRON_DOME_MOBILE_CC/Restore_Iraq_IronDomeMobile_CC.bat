@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Restore SPECTER files (Iraq Iron Dome Mobile CC)

cd /d "%~dp0"
set "PATCH_DIR=%~dp0"

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

set "BACKUP=%GAME_ROOT%SpecterBackup_IraqIronDomeMobile_CC\"
set "SRC_LAUNCHER=%GAME_ROOT%CommandSet.ini"
set "SRC_DATAINI=%GAME_ROOT%Data\INI\CommandSet.ini"

if not exist "%BACKUP%_SPEC_DATA_ONE.big" (
  echo ERROR: Backup _SPEC_DATA_ONE.big not found:
  echo   %BACKUP%
  echo Run the installer first so a backup exists.
  pause
  exit /b 1
)
if not exist "%BACKUP%_SPEC_ART_TWO.big" (
  echo ERROR: Backup _SPEC_ART_TWO.big not found:
  echo   %BACKUP%
  pause
  exit /b 1
)

echo Game folder:
echo   %GAME_ROOT%
echo Restoring from:
echo   %BACKUP%
echo.
echo This Restore copies the installer backup back. It does not
echo delete CommandSet.ini, CSF, or unknown game files.
echo.

echo [1/3] Restoring BIGs from this pack's backup
call :restore_file "%BACKUP%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" "_SPEC_DATA_ONE.big"
if errorlevel 1 goto FAIL
if exist "%BACKUP%_SPEC_ART_ONE.big" (
  call :restore_file "%BACKUP%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" "_SPEC_ART_ONE.big"
  if errorlevel 1 goto FAIL
) else (
  echo   No _SPEC_ART_ONE.big in backup. Left the game file unchanged.
)
call :restore_file "%BACKUP%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" "_SPEC_ART_TWO.big"
if errorlevel 1 goto FAIL
echo.

echo [2/3] Restoring launcher CommandSet.ini
if exist "%BACKUP%launcher_CommandSet.ini" (
  call :restore_file "%BACKUP%launcher_CommandSet.ini" "%SRC_LAUNCHER%" "launcher CommandSet.ini"
  if errorlevel 1 goto FAIL
) else (
  echo   No launcher CommandSet.ini in backup. Not created.
)
echo.

echo [3/3] Restoring Data\INI\CommandSet.ini
if exist "%BACKUP%Data\INI\CommandSet.ini" (
  if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
  call :restore_file "%BACKUP%Data\INI\CommandSet.ini" "%SRC_DATAINI%" "Data\INI\CommandSet.ini"
  if errorlevel 1 goto FAIL
) else (
  echo   No Data\INI\CommandSet.ini in backup. Loose file not created.
)
echo.

echo Restore finished.
pause
exit /b 0

:FAIL
echo.
echo ERROR: Restore stopped. Game files that already copied may be mixed.
echo Re-run Restore after fixing disk/permissions, or copy from:
echo   %BACKUP%
pause
exit /b 1

:restore_file
if not exist "%~1" (
  echo ERROR: Missing backup %~3
  exit /b 1
)
copy /Y "%~1" "%~2" >nul
if errorlevel 1 (
  echo ERROR: Could not restore %~3
  exit /b 1
)
fc /b "%~1" "%~2" >nul
if errorlevel 1 (
  echo ERROR: Restored %~3 does not match the backup.
  exit /b 1
)
echo   Restored %~3
exit /b 0
