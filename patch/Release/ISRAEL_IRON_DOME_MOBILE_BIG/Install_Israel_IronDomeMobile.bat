@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Install Israel Iron Dome Mobile (BIG)

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)
set "PATCH_DIR=%~dp0"

REM ss1 Data\INI\CommandSet.ini — delete only if SHA-256 matches this value.
set "HASH_SS1_COMMANDSET=f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
REM v2 leftover CommandSet.ini — not the ss1 original; cleaned only on exact v2 hash.
set "HASH_V2_COMMANDSET=dee09bd21cf8f398ffdf8e79f7b07a0f3c3e3563d538eb8ae14dfe4fe8d4a7f4"

echo.
echo ============================================================
echo  Israel Iron Dome Mobile  -  BIG install
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
if not defined GAME_ROOT (
  for %%I in ("%PATCH_DIR%..") do (
    if exist "%%~fI\generals.exe" set "GAME_ROOT=%%~fI\"
  )
)
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found in this folder or the parent folder.
  echo Put this pack inside SPECTER FINAL ^(the folder with generals.exe^) and run it again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%generals.exe" (
  echo ERROR: generals.exe missing at:
  echo   %GAME_ROOT%generals.exe
  pause
  exit /b 1
)

echo Game folder:
echo   %GAME_ROOT%
echo.

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

set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile\"
set "CS_BACKUP=%BACKUP%Data\INI\CommandSet.ini"
set "CS_BACKUP_LEGACY=%BACKUP%Data_INI_CommandSet.ini"
set "CS_LIVE=%GAME_ROOT%Data\INI\CommandSet.ini"
set "BACKUP_DONE=%BACKUP%BACKUP_COMPLETE.txt"

if not exist "%BACKUP%" mkdir "%BACKUP%"

echo [1/4] Backup ^(must finish before any BIG is replaced^)
echo   Folder:
echo     %BACKUP%
echo   CommandSet.ini backup path:
echo     %CS_BACKUP%
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
    echo   _SPEC_ART_ONE.big not present in the game folder. Skipped.
  )
  call :backup_file "%GAME_ROOT%_SPEC_ART_TWO.big" "%BACKUP%_SPEC_ART_TWO.big" "_SPEC_ART_TWO.big"
  if errorlevel 1 goto FAIL_BACKUP

  if not exist "%BACKUP%_SPEC_DATA_ONE.big" goto FAIL_BACKUP
  if not exist "%BACKUP%_SPEC_ART_TWO.big" goto FAIL_BACKUP

  call :backup_ss1_commandset
  if errorlevel 1 goto FAIL_BACKUP

  echo Backup finished before any BIG replace.> "%BACKUP_DONE%"
  echo   Backup complete. Game files not replaced yet.
  echo.
)

echo [2/4] Installing patched BIGs...
copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big. Backup is intact. Run Restore.
  pause
  exit /b 1
)
copy /Y "%PATCH_DIR%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_ART_TWO.big. Backup is intact. Run Restore.
  pause
  exit /b 1
)
echo   Installed _SPEC_DATA_ONE.big
echo   Installed _SPEC_ART_TWO.big
echo   _SPEC_ART_ONE.big was not replaced.
echo.

echo [3/4] CommandSet.ini ^(SHA-256, not size^)
call :handle_live_commandset
echo.

echo [4/4] Removing Iron Dome Mobile v2 loose files ^(exact SHA-256 only^)
call :del_if_hash "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini" d46708f22538a5c010025f958be87c3c375e057374c8ddab250ec7409d3bcbe1
call :del_if_hash "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" 6ce652ec590fc4865e5899f1d0c3f20011ba94ce0b72c283d94c67899cfefdde
call :del_if_hash "%GAME_ROOT%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" a9ab0802996424f8698a583c7a2482277d69ab735cac720d0e0c247d2567b5fe
call :del_if_hash "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" fd9e7dabbb4161b070df2881fa7c76fce1ba8db5752dbd9b5de5f41f3f852553
call :del_if_hash "%GAME_ROOT%Data\English\generals.csf" fea7f9a69ba97d12106bddf746ed5456da83da02a68037a6d1c74c74d715bb23
call :del_if_hash "%GAME_ROOT%Art\W3D\BONDKS.W3D" 32d85b6aef50ef1a10eb95613d98ecb3bde2859b6aa6d9ab94f30416933d3dc4
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D01.tga" 949cdee2c8f08554cd63fb032e891b34237039bff02bb2f5e5083f9308a32fa7
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D02.tga" 8d7a88931bfeb30ee2d4aba81c062bfd8f3cc5b9553685aa52aa40f6674b64a8
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D03.tga" e3bcd558aae7ff3f5f8f75ed6141f71cc737a30fb953f5024532f7f743156b29
call :del_if_hash "%GAME_ROOT%Art\Textures\concrete_wall_02_D.tga" 82abd77b603d308569dcc33472892c30f1eb04e763b575356e36290e1ee30609
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0006.tga" ed671df6f064d9b35467185fc9b785abd67b5320eb80f2ed4ef71aef1f9543a1
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0007.tga" abc1853a4f67c8cb10fd3ae915ca37c75fc72291f306ea6b0990d03363b1e937
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0008.tga" c57c265d99e7d4b7e447bd1288cafa122d7d3253864e9c1a7f0f14739c96f2ef
echo.

echo Done. Re-running this installer does not overwrite an existing backup.
echo Restore: Restore_Israel_IronDomeMobile.bat
echo Buy button: AirF Command Center slot 11
echo.
pause
exit /b 0

:FAIL_BACKUP
echo.
echo ERROR: Backup did not finish. No game BIG was replaced.
echo Existing game files were left as they were.
pause
exit /b 1

:backup_file
REM %1 source  %2 dest  %3 label
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

:backup_ss1_commandset
if not exist "%CS_LIVE%" (
  echo   Data\INI\CommandSet.ini not present. Nothing to back up.
  exit /b 0
)
call :sha256 "%CS_LIVE%"
if errorlevel 1 (
  echo ERROR: Could not hash Data\INI\CommandSet.ini
  exit /b 1
)
if /I not "!HASH256!"=="%HASH_SS1_COMMANDSET%" (
  echo   Data\INI\CommandSet.ini SHA-256 is not the ss1 original.
  echo   SHA-256: !HASH256!
  echo   Not backed up as the ss1 original. Not deleted in this step.
  exit /b 0
)
if not exist "%BACKUP%Data\INI" mkdir "%BACKUP%Data\INI"
if exist "%CS_BACKUP%" (
  fc /b "%CS_LIVE%" "%CS_BACKUP%" >nul
  if errorlevel 1 (
    echo ERROR: Existing backup CommandSet.ini does not match the live ss1 file.
    echo   Live:   %CS_LIVE%
    echo   Backup: %CS_BACKUP%
    echo   Live file was not deleted.
    exit /b 1
  )
  echo   Existing CommandSet.ini backup already matches the live ss1 file.
  echo     %CS_BACKUP%
  exit /b 0
)
copy /Y "%CS_LIVE%" "%CS_BACKUP%" >nul
if errorlevel 1 (
  echo ERROR: Could not write CommandSet.ini backup.
  exit /b 1
)
fc /b "%CS_LIVE%" "%CS_BACKUP%" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini backup is not identical to the original. Backup file removed.
  del /F /Q "%CS_BACKUP%" >nul 2>&1
  exit /b 1
)
echo   Backed up ss1 Data\INI\CommandSet.ini
echo     from %CS_LIVE%
echo     to   %CS_BACKUP%
echo   Backup verified byte-for-byte.
exit /b 0

:handle_live_commandset
if not exist "%CS_LIVE%" (
  echo   Data\INI\CommandSet.ini already absent. Patched BIG will be used.
  exit /b 0
)
call :sha256 "%CS_LIVE%"
if errorlevel 1 (
  echo   WARNING: Could not hash Data\INI\CommandSet.ini. Left in place.
  exit /b 0
)
if /I "!HASH256!"=="%HASH_SS1_COMMANDSET%" (
  if not exist "%CS_BACKUP%" (
    echo   ERROR: ss1 CommandSet.ini is present but backup is missing. Not deleted.
    exit /b 0
  )
  fc /b "%CS_LIVE%" "%CS_BACKUP%" >nul
  if errorlevel 1 (
    echo   ERROR: Backup does not match live ss1 CommandSet.ini. Not deleted.
    echo     Live:   %CS_LIVE%
    echo     Backup: %CS_BACKUP%
    exit /b 0
  )
  del /F /Q "%CS_LIVE%"
  if exist "%CS_LIVE%" (
    echo   ERROR: Could not remove Data\INI\CommandSet.ini
    exit /b 0
  )
  echo   Removed ss1 Data\INI\CommandSet.ini after verified backup.
  echo     Backup kept at %CS_BACKUP%
  exit /b 0
)
if /I "!HASH256!"=="%HASH_V2_COMMANDSET%" (
  echo   Data\INI\CommandSet.ini matches Iron Dome Mobile v2. Not the ss1 original.
  echo   Removing v2 leftover so the patched BIG is used.
  del /F /Q "%CS_LIVE%"
  exit /b 0
)
echo   Data\INI\CommandSet.ini SHA-256 is not ss1 and not v2.
echo   SHA-256: !HASH256!
echo   Left in place. Other game files were not changed.
echo   Slot 11 may not appear if this file wins over the BIG.
exit /b 0

:del_if_hash
if not exist "%~1" exit /b 0
call :sha256 "%~1"
if errorlevel 1 (
  echo   Left in place ^(could not hash^): %~1
  exit /b 0
)
if /I "!HASH256!"=="%~2" (
  del /F /Q "%~1"
  echo   Removed v2 leftover: %~1
) else (
  echo   Left in place ^(hash is not v2^): %~1
)
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
