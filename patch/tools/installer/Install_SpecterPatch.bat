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
echo.
echo ============================================================
echo  SPECTER PATCH INSTALLER
echo ============================================================
echo.
echo Installer folder:
echo   %PATCH_DIR%
echo.

echo [1/5] Checking patch files...
if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo.
  echo ERROR: Missing patch file _SPEC_DATA_ONE.big
  echo Put _SPEC_DATA_ONE.big next to Install_SpecterPatch.bat
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  echo.
  echo ERROR: Missing patch file _SPEC_ART_ONE.big
  echo Put _SPEC_ART_ONE.big next to Install_SpecterPatch.bat
  echo.
  pause
  exit /b 1
)
echo   Found _SPEC_DATA_ONE.big
echo   Found _SPEC_ART_ONE.big
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
echo   Backup folder:
echo   %BACKUP%
echo.

echo [4/5] Installing new BIG files...
echo.

set "SAME=0"
if /I "%PATCH_DIR%"=="%GAME_ROOT%" set "SAME=1"

if "%SAME%"=="1" (
  echo   Installer is already inside the game folder.
  echo   BIG files are already in place.
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
)

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big missing after install.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big missing after install.
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
echo You can start the game with Launch_Specter.bat
echo.
pause
endlocal
