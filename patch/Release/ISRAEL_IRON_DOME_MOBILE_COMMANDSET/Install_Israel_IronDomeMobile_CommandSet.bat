@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Install Iron Dome Mobile CommandSet slot 3

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)
set "PATCH_DIR=%~dp0"

set "HASH_SS1=f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
set "HASH_PATCHED=0a826f14e6d5253a9edd81ce3500a834edfc36cda37d1249d2d72011a742f3f8"

echo.
echo ============================================================
echo  Iron Dome Mobile  -  CommandSet.ini slot 3
echo ============================================================
echo.

if not exist "%PATCH_DIR%CommandSet.ini" (
  echo ERROR: Missing CommandSet.ini in the installer folder.
  pause
  exit /b 1
)

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
  echo ERROR: generals.exe or Launch_Specter.bat not found in this folder
  echo or the parent folder. Put this pack in SPECTER FINAL and run it again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo Game folder:
echo   %GAME_ROOT%
echo.

set "SRC_LAUNCHER=%GAME_ROOT%CommandSet.ini"
set "SRC_DATAINI=%GAME_ROOT%Data\INI\CommandSet.ini"
set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile_CommandSet\"
if not exist "%BACKUP%" mkdir "%BACKUP%"

echo [1/3] Independent backup of live CommandSet.ini files
if exist "%SRC_LAUNCHER%" (
  if not exist "%BACKUP%launcher_CommandSet.ini" copy /Y "%SRC_LAUNCHER%" "%BACKUP%launcher_CommandSet.ini" >nul
  fc /b "%SRC_LAUNCHER%" "%BACKUP%launcher_CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Backup of launcher CommandSet.ini is not identical.
    pause
    exit /b 1
  )
  echo   Backed up launcher source:
  echo     %SRC_LAUNCHER%
  echo     -^> %BACKUP%launcher_CommandSet.ini
) else (
  echo   No CommandSet.ini next to the launcher. Not created.
)
if exist "%SRC_DATAINI%" (
  if not exist "%BACKUP%Data_INI_CommandSet.ini" copy /Y "%SRC_DATAINI%" "%BACKUP%Data_INI_CommandSet.ini" >nul
  fc /b "%SRC_DATAINI%" "%BACKUP%Data_INI_CommandSet.ini" >nul
  if errorlevel 1 (
    echo ERROR: Backup of Data\INI\CommandSet.ini is not identical.
    pause
    exit /b 1
  )
  echo   Backed up ControlBar dest:
  echo     %SRC_DATAINI%
  echo     -^> %BACKUP%Data_INI_CommandSet.ini
) else (
  echo   No Data\INI\CommandSet.ini yet.
)
echo.

echo [2/3] Installing patched CommandSet.ini ^(ss1 or already-patched hash only^)
call :install_one "%SRC_LAUNCHER%" "launcher CommandSet.ini"
if errorlevel 1 goto FAIL
if exist "%GAME_ROOT%Data\INI" (
  call :install_one "%SRC_DATAINI%" "Data\INI\CommandSet.ini"
  if errorlevel 1 goto FAIL
) else (
  echo   Data\INI not present. Left uncreated.
)
echo.

echo [3/3] Simulate what Launch_Specter.bat does: copy launcher file onto Data\INI
if exist "%SRC_LAUNCHER%" (
  if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
  copy /Y "%SRC_LAUNCHER%" "%SRC_DATAINI%" >nul
  if errorlevel 1 (
    echo ERROR: Simulated launcher copy failed.
    pause
    exit /b 1
  )
  fc /b "%SRC_LAUNCHER%" "%SRC_DATAINI%" >nul
  if errorlevel 1 (
    echo ERROR: After copy, Data\INI\CommandSet.ini does not match launcher source.
    pause
    exit /b 1
  )
  echo   After launcher-style copy, both files are identical.
  echo     %SRC_LAUNCHER%
  echo     %SRC_DATAINI%
) else if exist "%SRC_DATAINI%" (
  echo   No launcher-side CommandSet.ini. Data\INI file was patched in place.
  echo   If you later add CommandSet.ini next to Launch_Specter.bat, copy this
  echo   patched file there or the launcher will overwrite Data\INI.
)
echo.
echo Done. Restore: Restore_Israel_IronDomeMobile_CommandSet.bat
echo This installer does not change BIGs, Object, CommandButton, or art.
pause
exit /b 0

:FAIL
echo.
echo ERROR: Install stopped. Backups are in:
echo   %BACKUP%
pause
exit /b 1

:install_one
if not exist "%~1" (
  echo   Skip missing %~2
  exit /b 0
)
call :sha256 "%~1"
if errorlevel 1 (
  echo ERROR: Could not hash %~2
  exit /b 1
)
if /I "!HASH256!"=="%HASH_PATCHED%" (
  echo   Already patched: %~2
  exit /b 0
)
if /I not "!HASH256!"=="%HASH_SS1%" (
  echo ERROR: %~2 is not the ss1 CommandSet.ini. Not replaced.
  echo   SHA-256: !HASH256!
  echo   Expected ss1: %HASH_SS1%
  exit /b 1
)
copy /Y "%PATCH_DIR%CommandSet.ini" "%~1" >nul
if errorlevel 1 (
  echo ERROR: Could not write %~2
  exit /b 1
)
call :sha256 "%~1"
if /I not "!HASH256!"=="%HASH_PATCHED%" (
  echo ERROR: Written %~2 hash mismatch.
  exit /b 1
)
echo   Installed: %~2
exit /b 0

:sha256
set "HASH256="
if not exist "%~1" exit /b 1
for /f "skip=1 delims=" %%A in ('certutil -hashfile "%~1" SHA256') do (
  set "HASH256=%%A"
  goto :sha256_done
)
:sha256_done
if not defined HASH256 exit /b 1
set "HASH256=!HASH256: =!"
exit /b 0
