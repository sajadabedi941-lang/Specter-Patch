@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Install America mobile Patriot (THAAD gameplay, New Donor art)

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)
set "PATCH_DIR=%~dp0"

REM ss1 originals, previous packs (v1 spawn / v2 crash-draw / v3 flags), or this pack.
set "HASH_SS1_DATA=7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343"
set "HASH_V1_DATA=1abaa9fa831ceb9b2278343d984fee92d4d454e31dbb3e405be09a58623aa990"
set "HASH_V2_DATA=51d5b0a51218accecc494bcc635bcc26872a6b11cca02791193d34a4facc3e02"
set "HASH_V3_DATA=6c97c63df1be3b0491bdb61e804f27f4dda80342edcb005e36f3f8da935c1389"
set "HASH_NEW_DATA=20fa43d9de8329c21baee2bdb6952ae08d725b248362eb18f5ad94a57553a486"
set "HASH_SS1_ART=81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf"
set "HASH_V1_ART=292dc82fdeaf34645e749d3eb9df09bf469a83549e238104d19514353f55af42"
set "HASH_NEW_ART=c4bb3c9837ee688c5cf8ff31529ca503f3d79b5b62e81474e349a967e63efe6d"

echo.
echo ============================================================
echo  America Command Center slot 6  -  mobile Patriot rebuild
echo  Object USAPAC3  (THAAD fire chain, New Donor art)
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
echo This installer does not write, delete, or replace any file under Data\
echo including Data\INI. America CC slot 6 already points at Object USAPAC3.
echo.

set "BACKUP=%GAME_ROOT%SpecterBackup_USA_PAC3_THAAD_DONOR\"
set "BACKUP_DONE=%BACKUP%BACKUP_COMPLETE.txt"

if not exist "%BACKUP%" mkdir "%BACKUP%"

echo [1/2] Backup ^(must finish before any file is replaced^)
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
  echo Backup finished before any replace.> "%BACKUP_DONE%"
  echo   Backup complete. Game files not replaced yet.
  echo.
)

echo [2/2] Hash-check then install BIGs ^(ss1, previous pack, or this pack^)
call :install_hashed "%GAME_ROOT%_SPEC_DATA_ONE.big" "%PATCH_DIR%_SPEC_DATA_ONE.big" "_SPEC_DATA_ONE.big" "%HASH_SS1_DATA%" "%HASH_NEW_DATA%" "%HASH_V2_DATA%"
if errorlevel 1 goto FAIL
call :install_hashed "%GAME_ROOT%_SPEC_ART_TWO.big" "%PATCH_DIR%_SPEC_ART_TWO.big" "_SPEC_ART_TWO.big" "%HASH_SS1_ART%" "%HASH_NEW_ART%" "%HASH_V1_ART%"
if errorlevel 1 goto FAIL
echo   _SPEC_ART_ONE.big was not replaced.
echo   Loose Data\INI was not touched.
echo.
echo Done. Restore: Restore_USA_PAC3_THAAD_DONOR.bat
echo This installer does not write new loose Object/CommandButton/CSF/art files.
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
REM %1 dest  %2 src  %3 label  %4 ss1  %5 this pack  %6 previous pack (optional)
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
set "ALLOW="
if /I "!HASH256!"=="%~4" set "ALLOW=1"
if not "%~6"=="" if /I "!HASH256!"=="%~6" set "ALLOW=1"
if /I "!HASH256!"=="%HASH_V1_DATA%" set "ALLOW=1"
if /I "!HASH256!"=="%HASH_V2_DATA%" set "ALLOW=1"
if /I "!HASH256!"=="%HASH_V3_DATA%" set "ALLOW=1"
if /I "!HASH256!"=="%HASH_V1_ART%" set "ALLOW=1"
if not defined ALLOW (
  echo ERROR: %~3 is not ss1, the previous pack, or this pack. Not replaced.
  echo   SHA-256: !HASH256!
  echo   Expected ss1: %~4
  echo   Expected previous pack: %~6
  echo   Expected this pack: %~5
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
