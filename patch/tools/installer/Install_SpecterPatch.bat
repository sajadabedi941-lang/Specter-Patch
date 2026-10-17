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
if not exist "%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big" (
  echo.
  echo ERROR: Missing patch file 0_SPECTER_NatoSpainDisplay.big
  echo Put 0_SPECTER_NatoSpainDisplay.big next to Install_SpecterPatch.bat
  echo.
  pause
  exit /b 1
)
echo   Found _SPEC_DATA_ONE.big
echo   Found _SPEC_ART_ONE.big
echo   Found 0_SPECTER_NatoSpainDisplay.big
if exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
  echo   Found _SPEC_ART_TWO.big
) else (
  echo   _SPEC_ART_TWO.big is not next to this installer.
  echo   It must already sit beside generals.exe, or install will stop.
)
echo.

REM Official SPEC byte sizes from SPECTER_SPEC_ART_DATA.SHA256.txt
REM and inspected archives. Catches truncated copies. Size is not a hash.
set "SZ_DATA="
set "SZ_ART1="
set "SZ_ART2="
set "SZ_SPAIN="
for %%A in ("%PATCH_DIR%_SPEC_DATA_ONE.big") do set "SZ_DATA=%%~zA"
for %%A in ("%PATCH_DIR%_SPEC_ART_ONE.big") do set "SZ_ART1=%%~zA"
for %%A in ("%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big") do set "SZ_SPAIN=%%~zA"
if exist "%PATCH_DIR%_SPEC_ART_TWO.big" for %%A in ("%PATCH_DIR%_SPEC_ART_TWO.big") do set "SZ_ART2=%%~zA"
if not "%SZ_DATA%"=="373898957" (
  echo.
  echo ERROR: _SPEC_DATA_ONE.big is %SZ_DATA% bytes, expected 373898957.
  echo The file is incomplete. Use the official SPEC archive.
  echo.
  pause
  exit /b 1
)
if not "%SZ_ART1%"=="2144972013" (
  echo.
  echo ERROR: _SPEC_ART_ONE.big is %SZ_ART1% bytes, expected 2144972013.
  echo A truncated ART_ONE copy leaves buildings black or magenta.
  echo.
  pause
  exit /b 1
)
if not "%SZ_SPAIN%"=="1608985" (
  echo.
  echo ERROR: 0_SPECTER_NatoSpainDisplay.big is %SZ_SPAIN% bytes, expected 1608985.
  echo The overlay is incomplete. Do not install this copy.
  echo.
  pause
  exit /b 1
)
if defined SZ_ART2 goto CHECK_ART2_SIZE
goto AFTER_ART2_SIZE
:CHECK_ART2_SIZE
if not "%SZ_ART2%"=="307254782" (
  echo.
  echo ERROR: _SPEC_ART_TWO.big is %SZ_ART2% bytes, expected 307254782.
  echo The file is incomplete. US_Command.W3D lives only in this archive.
  echo.
  pause
  exit /b 1
)
:AFTER_ART2_SIZE
echo   Source byte sizes match for the files found here.
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

  if exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
    echo   Copying _SPEC_ART_TWO.big ...
    copy /Y "%PATCH_DIR%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
    if errorlevel 1 (
      echo ERROR: Failed to copy _SPEC_ART_TWO.big
      echo Backup is in: %BACKUP%
      pause
      exit /b 1
    )
    echo   OK
  )

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
if not exist "%GAME_ROOT%_SPEC_ART_TWO.big" (
  echo.
  echo ERROR: _SPEC_ART_TWO.big is not in the game folder.
  echo NATO Command Center uses Art\W3D\US_Command.W3D from this archive.
  echo Put _SPEC_ART_TWO.big next to Install_SpecterPatch.bat, or copy it
  echo beside generals.exe. Official SPEC size 307254782 bytes,
  echo SHA-256 a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af
  echo ^(SPECTER_SPEC_ART_DATA.SHA256.txt^).
  echo.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" (
  echo ERROR: 0_SPECTER_NatoSpainDisplay.big missing after install.
  pause
  exit /b 1
)

REM Revalidate destination sizes so a truncated copy or leftover
REM game-folder ART_TWO cannot print SUCCESS.
set "DST_DATA="
set "DST_ART1="
set "DST_ART2="
set "DST_SPAIN="
for %%A in ("%GAME_ROOT%_SPEC_DATA_ONE.big") do set "DST_DATA=%%~zA"
for %%A in ("%GAME_ROOT%_SPEC_ART_ONE.big") do set "DST_ART1=%%~zA"
for %%A in ("%GAME_ROOT%_SPEC_ART_TWO.big") do set "DST_ART2=%%~zA"
for %%A in ("%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big") do set "DST_SPAIN=%%~zA"
if not "%DST_DATA%"=="373898957" (
  echo ERROR: installed _SPEC_DATA_ONE.big is %DST_DATA% bytes, expected 373898957.
  pause
  exit /b 1
)
if not "%DST_ART1%"=="2144972013" (
  echo ERROR: installed _SPEC_ART_ONE.big is %DST_ART1% bytes, expected 2144972013.
  pause
  exit /b 1
)
if not "%DST_ART2%"=="307254782" (
  echo ERROR: installed _SPEC_ART_TWO.big is %DST_ART2% bytes, expected 307254782.
  pause
  exit /b 1
)
if not "%DST_SPAIN%"=="1608985" (
  echo ERROR: installed 0_SPECTER_NatoSpainDisplay.big is %DST_SPAIN% bytes, expected 1608985.
  pause
  exit /b 1
)
echo   Destination byte sizes match for all four required archives.
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
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%_SPEC_ART_ONE.big
echo   %GAME_ROOT%_SPEC_ART_TWO.big
echo.
echo You can start the game with Launch_Specter.bat
echo.
pause
endlocal
