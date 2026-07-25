@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Ultimate Expansion - Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER ULTIMATE EXPANSION INSTALLER
echo ============================================================
echo.
echo  This installer only replaces:
echo    _SPEC_DATA_ONE.big
echo    _SPEC_ART_ONE.big
echo  No other game folders are modified.
echo.

set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

set "DATA_SRC=%SRC%\_SPEC_DATA_ONE.big"
set "ART_SRC=%SRC%\_SPEC_ART_ONE.big"

echo [1/5] Checking installer package files...
if not exist "%DATA_SRC%" (
  echo.
  echo ERROR: _SPEC_DATA_ONE.big not found in:
  echo   %SRC%
  echo.
  pause
  exit /b 1
)
if not exist "%ART_SRC%" (
  echo.
  echo ERROR: _SPEC_ART_ONE.big not found in:
  echo   %SRC%
  echo.
  pause
  exit /b 1
)
echo   Found _SPEC_DATA_ONE.big
echo   Found _SPEC_ART_ONE.big
echo.

echo [2/5] Detecting Specter GameRoot...
set "GAMEROOT="

rem A) This folder is GameRoot (ZIP extracted flat into SPECTER FINAL)
call :IsGameRoot "%SRC%"
if not errorlevel 1 (
  set "GAMEROOT=%SRC%"
  echo   Detected GameRoot = installer folder
  goto RootReady
)

rem B) Parent folder is GameRoot (ZIP folder extracted into SPECTER FINAL)
for %%I in ("%SRC%\..") do set "PARENT=%%~fI"
call :IsGameRoot "!PARENT!"
if not errorlevel 1 (
  set "GAMEROOT=!PARENT!"
  echo   Detected GameRoot = parent folder
  goto RootReady
)

rem C) Walk up a few levels
set "CURSOR=%SRC%"
for /L %%N in (1,1,4) do (
  for %%I in ("!CURSOR!\..") do set "CURSOR=%%~fI"
  call :IsGameRoot "!CURSOR!"
  if not errorlevel 1 (
    set "GAMEROOT=!CURSOR!"
    echo   Detected GameRoot = !CURSOR!
    goto RootReady
  )
)

rem D) Ask user
echo   Automatic detection failed.
echo.
echo Enter the full path to your Specter GameRoot
echo ^(folder that contains generals.exe^).
echo Example: D:\Games\SPECTER FINAL ^(GeneralsMode.com^)
echo.
set /p "GAMEROOT=GameRoot: "
set "GAMEROOT=!GAMEROOT:"=!"

call :IsGameRoot "!GAMEROOT!"
if errorlevel 1 (
  echo.
  echo ERROR: Not a valid Specter GameRoot:
  echo   !GAMEROOT!
  echo It must contain generals.exe or Generals.exe.
  echo.
  pause
  exit /b 1
)

:RootReady
echo   GameRoot: !GAMEROOT!
echo.

set "DATA_DST=!GAMEROOT!\_SPEC_DATA_ONE.big"
set "ART_DST=!GAMEROOT!\_SPEC_ART_ONE.big"

echo [3/5] Creating backup folder...
set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=!STAMP: =0!"
set "STAMP=!STAMP:/=!"
set "STAMP=!STAMP:\=!"
set "STAMP=!STAMP::=!"
set "BACKUP=!GAMEROOT!\BACKUP_SPECTER_!STAMP!"
mkdir "!BACKUP!" >nul 2>&1
if not exist "!BACKUP!\" (
  echo ERROR: Could not create backup folder:
  echo   !BACKUP!
  pause
  exit /b 1
)

if exist "!DATA_DST!" (
  echo   Backing up existing _SPEC_DATA_ONE.big ...
  copy /Y "!DATA_DST!" "!BACKUP!\_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_DATA_ONE.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing _SPEC_DATA_ONE.big to backup
)

if exist "!ART_DST!" (
  echo   Backing up existing _SPEC_ART_ONE.big ...
  copy /Y "!ART_DST!" "!BACKUP!\_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo ERROR: Failed to backup _SPEC_ART_ONE.big
    pause
    exit /b 1
  )
  echo   OK
) else (
  echo   No existing _SPEC_ART_ONE.big to backup
)
echo   Backup folder: !BACKUP!
echo.

echo [4/5] Installing new BIG files into GameRoot...

rem If installer was extracted flat into GameRoot, source and dest are the same path.
rem In that case files are already in place after unzip; still verify and finish cleanly.
if /I "%DATA_SRC%"=="!DATA_DST!" (
  echo   Source and GameRoot are the same folder.
  echo   BIG files are already in GameRoot from extraction.
) else (
  echo   Copying _SPEC_DATA_ONE.big ...
  copy /Y "%DATA_SRC%" "!DATA_DST!" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy _SPEC_DATA_ONE.big
    echo Your backup is in:
    echo   !BACKUP!
    pause
    exit /b 1
  )
  echo   OK

  echo   Copying _SPEC_ART_ONE.big ...
  copy /Y "%ART_SRC%" "!ART_DST!" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy _SPEC_ART_ONE.big
    echo Your backup is in:
    echo   !BACKUP!
    pause
    exit /b 1
  )
  echo   OK
)

if not exist "!DATA_DST!" (
  echo ERROR: _SPEC_DATA_ONE.big missing after install.
  pause
  exit /b 1
)
if not exist "!ART_DST!" (
  echo ERROR: _SPEC_ART_ONE.big missing after install.
  pause
  exit /b 1
)
echo.

echo [5/5] Writing install marker...
(
  echo Specter Ultimate Expansion installed.
  echo InstalledAt=%DATE% %TIME%
  echo GameRoot=!GAMEROOT!
  echo Backup=!BACKUP!
) > "!GAMEROOT!\SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt"
echo   Wrote SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt
echo.

echo ============================================================
echo  INSTALLATION COMPLETED SUCCESSFULLY
echo ============================================================
echo.
echo  Installed:
echo    !DATA_DST!
echo    !ART_DST!
echo.
echo  Backup:
echo    !BACKUP!
echo.
echo  You can now launch Specter with Launch_Specter.bat
echo  or generals.exe in the GameRoot.
echo.
pause
exit /b 0

:IsGameRoot
set "TESTROOT=%~1"
if not defined TESTROOT exit /b 1
if not exist "%TESTROOT%\" exit /b 1
if exist "%TESTROOT%\generals.exe" exit /b 0
if exist "%TESTROOT%\Generals.exe" exit /b 0
if exist "%TESTROOT%\GeneralsZH.exe" exit /b 0
if exist "%TESTROOT%\generalszh.exe" exit /b 0
rem Specter roots always have the BIG pair even if exe casing differs
if exist "%TESTROOT%\_SPEC_DATA_ONE.big" if exist "%TESTROOT%\_SPEC_ART_ONE.big" (
  rem Prefer requiring an exe; allow BIG-only only when also Data folder exists
  if exist "%TESTROOT%\Data\" exit /b 0
)
exit /b 1
