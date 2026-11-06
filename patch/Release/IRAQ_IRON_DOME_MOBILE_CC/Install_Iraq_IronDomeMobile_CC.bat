@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Install Iraq Command Center Iron Dome Mobile

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)
set "PATCH_DIR=%~dp0"

REM ss1 originals — replace only these hashes, or this pack's hashes.
set "HASH_SS1_DATA=7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343"
set "HASH_NEW_DATA=f456aaa65d1d1e1b0bfb749fafd54a2ae96014d4faf3fd53026bb732f25f350c"
set "HASH_SS1_ART=81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf"
set "HASH_NEW_ART=c9a723443c321b689870d116a7b3c0d941516850d1db16c0254ed70218960787"
set "HASH_SS1_CS=f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
set "HASH_NEW_CS=ca435e520ac23c4e294395557b3a7e6866d7707844b82f4bcd9af7cfbb092206"

echo.
echo ============================================================
echo  Iraq Command Center  -  Iron Dome Mobile slot 3
echo ============================================================
echo.

if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo ERROR: Missing installer _SPEC_DATA_ONE.big
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
  echo ERROR: Missing installer _SPEC_ART_TWO.big
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%CommandSet.ini" (
  echo ERROR: Missing installer CommandSet.ini
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

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo ERROR: Game _SPEC_DATA_ONE.big not found.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_TWO.big" (
  echo ERROR: Game _SPEC_ART_TWO.big not found.
  pause
  exit /b 1
)

echo Game folder:
echo   %GAME_ROOT%
echo.

set "BACKUP=%GAME_ROOT%SpecterBackup_IraqIronDomeMobile_CC\"
set "BACKUP_DONE=%BACKUP%BACKUP_COMPLETE.txt"
set "SRC_LAUNCHER=%GAME_ROOT%CommandSet.ini"
set "SRC_DATAINI=%GAME_ROOT%Data\INI\CommandSet.ini"

if not exist "%BACKUP%" mkdir "%BACKUP%"

echo [1/4] Backup ^(must finish before any file is replaced^)
echo   Folder:
echo     %BACKUP%
echo.

set "SKIP_BACKUP="
if exist "%BACKUP_DONE%" if exist "%BACKUP%_SPEC_DATA_ONE.big" if exist "%BACKUP%_SPEC_ART_TWO.big" set "SKIP_BACKUP=1"
if exist "%BACKUP_DONE%" if not defined SKIP_BACKUP (
  echo   BACKUP_COMPLETE.txt found but a required BIG backup is missing.
  echo   Incomplete marker removed. Backup will be taken from the current game files.
  del /F /Q "%BACKUP_DONE%" >nul 2>&1
)

if defined SKIP_BACKUP (
  echo   Existing verified backup kept. It is not overwritten on re-install.
  echo.
) else (
  call :backup_file "%GAME_ROOT%_SPEC_DATA_ONE.big" "%BACKUP%_SPEC_DATA_ONE.big" "_SPEC_DATA_ONE.big"
  if errorlevel 1 goto FAIL_BACKUP
  if exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
    call :backup_file "%GAME_ROOT%_SPEC_ART_ONE.big" "%BACKUP%_SPEC_ART_ONE.big" "_SPEC_ART_ONE.big"
    if errorlevel 1 goto FAIL_BACKUP
  ) else (
    echo   _SPEC_ART_ONE.big not present. Skipped.
  )
  call :backup_file "%GAME_ROOT%_SPEC_ART_TWO.big" "%BACKUP%_SPEC_ART_TWO.big" "_SPEC_ART_TWO.big"
  if errorlevel 1 goto FAIL_BACKUP
  if exist "%SRC_LAUNCHER%" (
    call :backup_file "%SRC_LAUNCHER%" "%BACKUP%launcher_CommandSet.ini" "launcher CommandSet.ini"
    if errorlevel 1 goto FAIL_BACKUP
  ) else (
    echo   No CommandSet.ini next to the launcher. Not created.
  )
  if exist "%SRC_DATAINI%" (
    if not exist "%BACKUP%Data\INI" mkdir "%BACKUP%Data\INI"
    call :backup_file "%SRC_DATAINI%" "%BACKUP%Data\INI\CommandSet.ini" "Data\INI\CommandSet.ini"
    if errorlevel 1 goto FAIL_BACKUP
  ) else (
    echo   No Data\INI\CommandSet.ini yet.
  )
  echo Backup finished before any replace.> "%BACKUP_DONE%"
  echo   Backup complete. Game files not replaced yet.
  echo.
)

echo [2/4] Hash-check then install BIGs ^(ss1 or this pack only^)
call :install_hashed "%GAME_ROOT%_SPEC_DATA_ONE.big" "%PATCH_DIR%_SPEC_DATA_ONE.big" "_SPEC_DATA_ONE.big" "%HASH_SS1_DATA%" "%HASH_NEW_DATA%"
if errorlevel 1 goto FAIL
call :install_hashed "%GAME_ROOT%_SPEC_ART_TWO.big" "%PATCH_DIR%_SPEC_ART_TWO.big" "_SPEC_ART_TWO.big" "%HASH_SS1_ART%" "%HASH_NEW_ART%"
if errorlevel 1 goto FAIL
echo   _SPEC_ART_ONE.big was not replaced.
echo.

echo [3/4] Hash-check then install live CommandSet.ini
call :install_hashed "%SRC_LAUNCHER%" "%PATCH_DIR%CommandSet.ini" "launcher CommandSet.ini" "%HASH_SS1_CS%" "%HASH_NEW_CS%"
if errorlevel 1 goto FAIL
if exist "%SRC_DATAINI%" (
  call :install_hashed "%SRC_DATAINI%" "%PATCH_DIR%CommandSet.ini" "Data\INI\CommandSet.ini" "%HASH_SS1_CS%" "%HASH_NEW_CS%"
  if errorlevel 1 goto FAIL
) else (
  if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
  copy /Y "%PATCH_DIR%CommandSet.ini" "%SRC_DATAINI%" >nul
  if errorlevel 1 (
    echo ERROR: Could not write missing Data\INI\CommandSet.ini
    goto FAIL
  )
  call :sha256 "%SRC_DATAINI%"
  if /I not "!HASH256!"=="%HASH_NEW_CS%" (
    echo ERROR: Written Data\INI\CommandSet.ini hash mismatch.
    goto FAIL
  )
  echo   Installed missing ControlBar file: Data\INI\CommandSet.ini
)
echo.

echo [4/4] Simulate Launch_Specter.bat: copy launcher CommandSet.ini onto Data\INI
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
  echo   After launcher-style copy, both CommandSet.ini files are identical.
) else if exist "%SRC_DATAINI%" (
  echo   No launcher-side CommandSet.ini. Data\INI file was patched in place.
  echo   If you later add CommandSet.ini next to Launch_Specter.bat, copy this
  echo   patched file there or the launcher will overwrite Data\INI.
)
echo.
echo Done. Restore: Restore_Iraq_IronDomeMobile_CC.bat
echo This installer does not write new loose Object/CommandButton/CSF/art files.
echo Israel Command Center CommandSets were not changed.
pause
exit /b 0

:FAIL_BACKUP
echo.
echo ERROR: Backup did not finish. No game file was replaced.
echo Existing game files were left as they were.
pause
exit /b 1

:FAIL
echo.
echo ERROR: Install stopped. Backups are in:
echo   %BACKUP%
pause
exit /b 1

:backup_file
if not exist "%~1" (
  echo ERROR: Missing %~3
  exit /b 1
)
if exist "%BACKUP_DONE%" if exist "%~2" (
  echo   Keep existing backup of %~3
  exit /b 0
)
echo   Copying %~3 ...
copy /Y "%~1" "%~2" >nul
if errorlevel 1 (
  echo ERROR: Could not copy %~3 to backup.
  exit /b 1
)
fc /b "%~1" "%~2" >nul
if errorlevel 1 (
  echo ERROR: Backup of %~3 is not identical to the original. Backup file removed.
  del /F /Q "%~2" >nul 2>&1
  exit /b 1
)
echo   Verified byte-for-byte: %~3
exit /b 0

:install_hashed
REM %1 dest  %2 src  %3 label  %4 allowed-original  %5 allowed-patched
if not exist "%~1" (
  echo   Skip missing %~3
  exit /b 0
)
call :sha256 "%~1"
if errorlevel 1 (
  echo ERROR: Could not hash %~3
  exit /b 1
)
if /I "!HASH256!"=="%~5" (
  echo   Already this pack: %~3
  exit /b 0
)
if /I not "!HASH256!"=="%~4" (
  echo ERROR: %~3 is not the ss1 original and not this pack. Not replaced.
  echo   SHA-256: !HASH256!
  echo   Expected ss1: %~4
  echo   Expected pack: %~5
  exit /b 1
)
copy /Y "%~2" "%~1" >nul
if errorlevel 1 (
  echo ERROR: Could not write %~3
  exit /b 1
)
call :sha256 "%~1"
if /I not "!HASH256!"=="%~5" (
  echo ERROR: Written %~3 hash mismatch.
  echo   SHA-256: !HASH256!
  echo   Expected: %~5
  exit /b 1
)
echo   Installed: %~3
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
