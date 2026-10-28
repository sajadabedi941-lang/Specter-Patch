@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER Unified Install

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini 0_SPECTER_GlobalStoreCameos.big 0_SPECTER_MissileJLMNCameos.big"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script.
    pause
    exit /b 1
  )
)

rem Canonical Full Release ART. Do not install truncated substitutes.
set "ART1_NAME=_SPEC_ART_ONE.big"
set "ART2_NAME=_SPEC_ART_TWO.big"
set "ART1_SIZE=2145283309"
set "ART2_SIZE=307254782"
set "ART1_SHA=15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
set "ART2_SHA=a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af"
set "ART1_URL=https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big"
set "ART1_URL_ALT=https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/WORLD_WAR_III2027-Full-Release/_SPEC_ART_ONE.big"

set "GAME_ROOT="
set "PARENT="
for %%I in ("%~dp0..") do set "PARENT=%%~fI"

if exist "%~dp0generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%~dp0Generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"

if not defined GAME_ROOT (
  echo ERROR: generals.exe not found. Unzip this pack and run the installer from the game folder, or from a folder next to it.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%Data\INI\" mkdir "%GAME_ROOT%Data\INI"
if errorlevel 1 (
  echo ERROR: Cannot create Data\INI
  pause
  exit /b 1
)

call :find_art ART1_SRC "%ART1_NAME%" "%ART1_SIZE%"
call :find_art ART2_SRC "%ART2_NAME%" "%ART2_SIZE%"

if not defined ART1_SRC (
  echo.
  echo ERROR: Canonical %ART1_NAME% was not found.
  echo This ZIP is NOT a standalone complete install. GitHub's 2 GiB asset
  echo limit cannot hold ART ONE + ART TWO + DATA in one ZIP.
  echo.
  echo Place the original Full Release file next to this installer, next to
  echo generals.exe, or already in the game folder:
  echo   %ART1_NAME%
  echo   bytes    %ART1_SIZE%
  echo   SHA-256  %ART1_SHA%
  echo.
  echo Download:
  echo   %ART1_URL%
  echo   %ART1_URL_ALT%
  echo.
  echo Do NOT use the 447 MB construct-button ART, the repo split zip, or
  echo s-art-split-2gib. Those drop models.
  pause
  exit /b 1
)

if not defined ART2_SRC (
  echo.
  echo ERROR: Canonical %ART2_NAME% was not found.
  echo Expected %ART2_SIZE% bytes, SHA-256 %ART2_SHA%.
  echo Keep the copy shipped in this pack, or the Full Release original.
  pause
  exit /b 1
)

for /f "tokens=1-3 delims=/ " %%A in ("%DATE%") do set "D=%%C%%A%%B"
for /f "tokens=1-3 delims=:." %%A in ("%TIME%") do set "T=%%A%%B%%C"
set "T=%T: =0%"
set "BACKUP=%GAME_ROOT%Backup_SPECTER_UNIFIED_%D%_%T%"
mkdir "%BACKUP%" 2>nul
mkdir "%BACKUP%\Data\INI" 2>nul

echo Backing up existing files to:
echo   %BACKUP%
if exist "%GAME_ROOT%_SPEC_DATA_ONE.big" copy /Y "%GAME_ROOT%_SPEC_DATA_ONE.big" "%BACKUP%\_SPEC_DATA_ONE.big" >nul
if exist "%GAME_ROOT%Data\INI\CommandSet.ini" copy /Y "%GAME_ROOT%Data\INI\CommandSet.ini" "%BACKUP%\Data\INI\CommandSet.ini" >nul
if exist "%GAME_ROOT%Data\INI\CommandButton.ini" copy /Y "%GAME_ROOT%Data\INI\CommandButton.ini" "%BACKUP%\Data\INI\CommandButton.ini" >nul
if exist "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" copy /Y "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" "%BACKUP%\0_SPECTER_GlobalStoreCameos.big" >nul
if exist "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" copy /Y "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" "%BACKUP%\0_SPECTER_MissileJLMNCameos.big" >nul
copy /Y "%~dp0Restore_SpecterUnifiedBackup.bat" "%BACKUP%\Restore_SpecterUnifiedBackup.bat" >nul 2>nul
echo %BACKUP%> "%GAME_ROOT%Backup_SPECTER_UNIFIED_LAST.txt"

echo Installing DATA / INI / overlays...
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp00_SPECTER_GlobalStoreCameos.big" "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp00_SPECTER_MissileJLMNCameos.big" "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" >nul
if errorlevel 1 goto :copyfail

set "ART1_ACTION=kept existing canonical file"
set "ART2_ACTION=kept existing canonical file"

call :install_art "%ART1_SRC%" "%GAME_ROOT%%ART1_NAME%" "%BACKUP%\%ART1_NAME%" ART1_ACTION "%ART1_NAME%"
if errorlevel 1 goto :copyfail
call :install_art "%ART2_SRC%" "%GAME_ROOT%%ART2_NAME%" "%BACKUP%\%ART2_NAME%" ART2_ACTION "%ART2_NAME%"
if errorlevel 1 goto :copyfail

echo.
echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%0_SPECTER_GlobalStoreCameos.big
echo   %GAME_ROOT%0_SPECTER_MissileJLMNCameos.big
echo   %GAME_ROOT%%ART1_NAME%  !ART1_ACTION!
echo   %GAME_ROOT%%ART2_NAME%  !ART2_ACTION!
echo.
echo SHA-256:
echo   DATA  c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac
echo   CS    a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo   GS    1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc
echo   JLMN  618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae
echo   ART1  %ART1_SHA%
echo   ART2  %ART2_SHA%
echo.
echo Load order: 0_ overlays first-win Art\Textures over %ART1_NAME%.
echo Keep the 0_ prefix. Do not replace Full Release ART with a 447 MB pack.
echo To undo DATA/INI/overlays, run Restore_SpecterUnifiedBackup.bat from:
echo   %BACKUP%
echo ART is restored only if this installer had to replace a non-canonical file.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed. Restore from %BACKUP% if needed.
pause
exit /b 1

:find_art
rem %1 = out var, %2 = filename, %3 = expected bytes
set "%~1="
call :accept_art "%~1" "%~dp0%~2" "%~3"
if defined %~1 exit /b 0
if defined PARENT call :accept_art "%~1" "%PARENT%\%~2" "%~3"
if defined %~1 exit /b 0
call :accept_art "%~1" "%GAME_ROOT%%~2" "%~3"
exit /b 0

:accept_art
if defined %~1 exit /b 0
if not exist "%~2" exit /b 0
set "GOTSIZE="
for %%A in ("%~2") do set "GOTSIZE=%%~zA"
if not "!GOTSIZE!"=="%~3" (
  echo Skipping non-canonical %~2
  echo   size !GOTSIZE!  expected %~3
  exit /b 0
)
set "%~1=%~2"
echo Using canonical ART: %~2
exit /b 0

:install_art
rem %1 src, %2 dest, %3 backup, %4 action var, %5 display name
set "SRC=%~1"
set "DST=%~2"
if /I "%SRC%"=="%DST%" (
  set "%~4=already in game folder, preserved"
  exit /b 0
)
if exist "%DST%" (
  set "DSTSIZE="
  for %%A in ("%DST%") do set "DSTSIZE=%%~zA"
  set "SRCSIZE="
  for %%A in ("%SRC%") do set "SRCSIZE=%%~zA"
  if "!DSTSIZE!"=="!SRCSIZE!" (
    set "%~4=already installed, preserved"
    exit /b 0
  )
  echo Backing up non-canonical %~5
  copy /Y "%DST%" "%~3" >nul
)
echo Copying %~5 ...
copy /Y "%SRC%" "%DST%" >nul
if errorlevel 1 exit /b 1
set "%~4=installed from pack / sidecar"
exit /b 0
