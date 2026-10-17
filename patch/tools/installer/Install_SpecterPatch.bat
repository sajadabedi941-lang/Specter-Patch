@echo off
setlocal EnableExtensions
title Specter Patch Installer

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  echo.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"
set "VERIFY=%~dp0Verify_SpecterArchives.bat"
echo.
echo ============================================================
echo  SPECTER PATCH INSTALLER
echo ============================================================
echo.
echo Installer folder:
echo   %PATCH_DIR%
echo.

if not exist "%VERIFY%" (
  echo ERROR: Missing Verify_SpecterArchives.bat
  echo Put it next to Install_SpecterPatch.bat
  echo.
  pause
  exit /b 1
)

echo [1/5] Checking source archives + SHA-256...
echo.
echo   All four official files must sit next to this installer.
echo   A leftover _SPEC_ART_TWO.big beside generals.exe is not enough.
echo.
call "%VERIFY%" "%PATCH_DIR%"
if errorlevel 1 (
  echo.
  echo ERROR: Source archive check failed.
  echo Official SPEC hashes are in SPECTER_SPEC_ART_DATA.SHA256.txt
  echo Overlay SHA-256 a2558dd5ccea23b55189d96698a42a4ac91b82455db27b0d7511a366ea4b129d
  echo.
  pause
  exit /b 1
)
echo.

echo [2/5] Detecting game folder with generals.exe...
set "GAME_ROOT="
set "PARENT="

REM Resolve parent path first (outside IF blocks to avoid percent-expansion bugs)
for %%I in ("%PATCH_DIR%..") do set "PARENT=%%~fI"

REM A) This folder is the game root
if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PATCH_DIR%Generals.exe" set "GAME_ROOT=%PATCH_DIR%"

REM B) Parent folder is the game root (normal ZIP extract into game folder)
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"

if not defined GAME_ROOT (
  echo.
  echo ERROR: generals.exe was not found.
  echo.
  echo Put the SPECTER_ULTIMATE_FIXED_INSTALLER folder INSIDE your
  echo Command and Conquer Generals Zero Hour / Specter folder
  echo ^(the folder that already contains generals.exe^), then run
  echo Install_SpecterPatch.bat again.
  echo.
  echo Checked:
  echo   %PATCH_DIR%
  echo   %PARENT%
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo   Game folder:
echo   %GAME_ROOT%
echo.

echo [3/5] Creating backup folder Backup_SpecterPatch...
set "BACKUP=%GAME_ROOT%Backup_SpecterPatch"
if not exist "%BACKUP%\" mkdir "%BACKUP%"
if not exist "%BACKUP%\" (
  echo.
  echo ERROR: Could not create backup folder:
  echo   %BACKUP%
  echo.
  pause
  exit /b 1
)

if exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo   Backing up old _SPEC_DATA_ONE.big ...
  copy /Y "%GAME_ROOT%_SPEC_DATA_ONE.big" "%BACKUP%\_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Backup failed for _SPEC_DATA_ONE.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing _SPEC_DATA_ONE.big to backup
)

if exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo   Backing up old _SPEC_ART_ONE.big ...
  copy /Y "%GAME_ROOT%_SPEC_ART_ONE.big" "%BACKUP%\_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Backup failed for _SPEC_ART_ONE.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing _SPEC_ART_ONE.big to backup
)

if exist "%GAME_ROOT%_SPEC_ART_TWO.big" (
  echo   Backing up old _SPEC_ART_TWO.big ...
  copy /Y "%GAME_ROOT%_SPEC_ART_TWO.big" "%BACKUP%\_SPEC_ART_TWO.big" >nul
  if errorlevel 1 (
    echo ERROR: Backup failed for _SPEC_ART_TWO.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing _SPEC_ART_TWO.big to backup
)

if exist "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" (
  echo   Backing up old 0_SPECTER_NatoSpainDisplay.big ...
  copy /Y "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" "%BACKUP%\0_SPECTER_NatoSpainDisplay.big" >nul
  if errorlevel 1 (
    echo ERROR: Backup failed for 0_SPECTER_NatoSpainDisplay.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing 0_SPECTER_NatoSpainDisplay.big to backup
)
echo   Backup folder:
echo   %BACKUP%
echo.

echo [4/5] Installing new BIG files...
echo.

set "SAME=0"
if /I "%PATCH_DIR%"=="%GAME_ROOT%" set "SAME=1"

if "%SAME%"=="1" (
  echo   Installer is already inside the game folder.
  echo   Source files are the destination files. No copy.
) else (
  echo   Copying _SPEC_DATA_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy _SPEC_DATA_ONE.big
    echo Backup is in: %BACKUP%
    pause
    exit /b 1
  )
  echo   OK

  echo   Copying _SPEC_ART_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy _SPEC_ART_ONE.big
    echo Backup is in: %BACKUP%
    pause
    exit /b 1
  )
  echo   OK

  echo   Copying _SPEC_ART_TWO.big ...
  copy /Y "%PATCH_DIR%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy _SPEC_ART_TWO.big
    echo Backup is in: %BACKUP%
    pause
    exit /b 1
  )
  echo   OK

  echo   Copying 0_SPECTER_NatoSpainDisplay.big ...
  copy /Y "%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big" "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy 0_SPECTER_NatoSpainDisplay.big
    echo Backup is in: %BACKUP%
    pause
    exit /b 1
  )
  echo   OK
)

echo.
echo   Re-checking destination archives + SHA-256...
call "%VERIFY%" "%GAME_ROOT%"
if errorlevel 1 (
  echo.
  echo ERROR: Destination archive check failed.
  echo Installation is NOT complete. No success.
  echo Backup is in: %BACKUP%
  echo.
  pause
  exit /b 1
)
echo.

echo [5/5] Done.
echo.
echo ============================================================
echo  SPECTER PATCH INSTALLATION COMPLETED SUCCESSFULLY
echo ============================================================
echo.
echo Installed to:
echo   %GAME_ROOT%
echo Backup:
echo   %BACKUP%
echo.
echo Active BIGs beside generals.exe:
echo   %GAME_ROOT%0_SPECTER_NatoSpainDisplay.big
echo   %GAME_ROOT%_SPEC_ART_ONE.big
echo   %GAME_ROOT%_SPEC_ART_TWO.big
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo.
echo Load order ^(first-wins named files, _stricmp archive names^):
echo   0_SPECTER_NatoSpainDisplay.big, _SPEC_ART_ONE.big,
echo   _SPEC_ART_TWO.big, _SPEC_DATA_ONE.big
echo.
echo You can start the game with Launch_Specter.bat
echo.
pause
endlocal
exit /b 0
