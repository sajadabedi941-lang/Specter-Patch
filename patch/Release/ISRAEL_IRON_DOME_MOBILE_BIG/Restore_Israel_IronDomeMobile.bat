@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Restore SPECTER BIGs (Iron Dome Mobile)

cd /d "%~dp0"
set "PATCH_DIR=%~dp0"

set "HASH_SS1_COMMANDSET=f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
set "HASH_V2_COMMANDSET=dee09bd21cf8f398ffdf8e79f7b07a0f3c3e3563d538eb8ae14dfe4fe8d4a7f4"
set "HASH_V2_CSF=fea7f9a69ba97d12106bddf746ed5456da83da02a68037a6d1c74c74d715bb23"

set "GAME_ROOT="
if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT (
  for %%I in ("%PATCH_DIR%..") do (
    if exist "%%~fI\generals.exe" set "GAME_ROOT=%%~fI\"
  )
)
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found in this folder or the parent folder.
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

set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile\"
set "CS_BACKUP=%BACKUP%Data\INI\CommandSet.ini"
set "CS_BACKUP_LEGACY=%BACKUP%Data_INI_CommandSet.ini"
set "CS_LIVE=%GAME_ROOT%Data\INI\CommandSet.ini"

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

echo [1/3] Restoring BIGs
copy /Y "%BACKUP%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Could not restore _SPEC_DATA_ONE.big
  pause
  exit /b 1
)
if exist "%BACKUP%_SPEC_ART_ONE.big" (
  copy /Y "%BACKUP%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Could not restore _SPEC_ART_ONE.big
    pause
    exit /b 1
  )
  echo   Restored _SPEC_ART_ONE.big
) else (
  echo   No _SPEC_ART_ONE.big in backup. Left the game file unchanged.
)
copy /Y "%BACKUP%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
if errorlevel 1 (
  echo ERROR: Could not restore _SPEC_ART_TWO.big
  pause
  exit /b 1
)
echo   Restored _SPEC_DATA_ONE.big
echo   Restored _SPEC_ART_TWO.big
echo.

echo [2/3] Restoring Data\INI\CommandSet.ini
set "CS_SRC="
if exist "%CS_BACKUP%" set "CS_SRC=%CS_BACKUP%"
if not defined CS_SRC if exist "%CS_BACKUP_LEGACY%" set "CS_SRC=%CS_BACKUP_LEGACY%"
if not defined CS_SRC (
  echo   No CommandSet.ini backup. Loose file not created.
  echo   After BIG restore the archive copy is used.
) else (
  call :sha256 "!CS_SRC!"
  if errorlevel 1 (
    echo   ERROR: Could not hash CommandSet.ini backup. Not copied onto the game.
  ) else if /I not "!HASH256!"=="%HASH_SS1_COMMANDSET%" (
    echo   Backup CommandSet.ini is not the ss1 original. Not copied onto the game.
    echo   SHA-256: !HASH256!
    echo   Path: !CS_SRC!
  ) else (
    if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
    copy /Y "!CS_SRC!" "%CS_LIVE%" >nul
    if errorlevel 1 (
      echo   ERROR: Could not restore Data\INI\CommandSet.ini
    ) else (
      fc /b "!CS_SRC!" "%CS_LIVE%" >nul
      if errorlevel 1 (
        echo   ERROR: Restored CommandSet.ini does not match the backup.
      ) else (
        echo   Restored Data\INI\CommandSet.ini from:
        echo     !CS_SRC!
        echo   Verified byte-for-byte against the backup.
      )
    )
  )
)
echo.

echo [3/3] Removing Iron Dome Mobile v2 loose files ^(exact SHA-256 only^)
if exist "%CS_LIVE%" (
  call :sha256 "%CS_LIVE%"
  if errorlevel 1 (
    echo   Left Data\INI\CommandSet.ini in place ^(could not hash^).
  ) else if /I "!HASH256!"=="%HASH_V2_COMMANDSET%" (
    echo   Removing v2 CommandSet.ini leftover.
    del /F /Q "%CS_LIVE%"
  )
)
call :del_if_hash "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini" d46708f22538a5c010025f958be87c3c375e057374c8ddab250ec7409d3bcbe1
call :del_if_hash "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" 6ce652ec590fc4865e5899f1d0c3f20011ba94ce0b72c283d94c67899cfefdde
call :del_if_hash "%GAME_ROOT%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" a9ab0802996424f8698a583c7a2482277d69ab735cac720d0e0c247d2567b5fe
call :del_if_hash "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" fd9e7dabbb4161b070df2881fa7c76fce1ba8db5752dbd9b5de5f41f3f852553
call :del_if_hash "%GAME_ROOT%Data\English\generals.csf" %HASH_V2_CSF%
call :del_if_hash "%GAME_ROOT%Art\W3D\BONDKS.W3D" 32d85b6aef50ef1a10eb95613d98ecb3bde2859b6aa6d9ab94f30416933d3dc4
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D01.tga" 949cdee2c8f08554cd63fb032e891b34237039bff02bb2f5e5083f9308a32fa7
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D02.tga" 8d7a88931bfeb30ee2d4aba81c062bfd8f3cc5b9553685aa52aa40f6674b64a8
call :del_if_hash "%GAME_ROOT%Art\Textures\T_M978_D03.tga" e3bcd558aae7ff3f5f8f75ed6141f71cc737a30fb953f5024532f7f743156b29
call :del_if_hash "%GAME_ROOT%Art\Textures\concrete_wall_02_D.tga" 82abd77b603d308569dcc33472892c30f1eb04e763b575356e36290e1ee30609
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0006.tga" ed671df6f064d9b35467185fc9b785abd67b5320eb80f2ed4ef71aef1f9543a1
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0007.tga" abc1853a4f67c8cb10fd3ae915ca37c75fc72291f306ea6b0990d03363b1e937
call :del_if_hash "%GAME_ROOT%Art\Textures\texture_0008.tga" c57c265d99e7d4b7e447bd1288cafa122d7d3253864e9c1a7f0f14739c96f2ef
echo.

echo Restore finished.
pause
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
