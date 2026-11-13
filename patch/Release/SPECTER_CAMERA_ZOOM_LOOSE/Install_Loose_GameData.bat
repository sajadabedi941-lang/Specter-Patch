@echo off
setlocal EnableExtensions
title SPECTER Camera Zoom - Install Loose GameData.ini

REM Installs Data\INI\GameData.ini next to the generals.exe that SPECTER starts.
REM The file stays loose. It is not packed into a BIG archive.
REM A pre-existing loose GameData.ini is copied to
REM Data\INI\GameData.ini.specter-zoom-backup before it is replaced.
REM Re-running this installer refreshes the override and keeps that backup.

cd /d "%~dp0"
set "PKG=%~dp0"
if not "%PKG:~-1%"=="\" set "PKG=%PKG%\"
set "SRC=%PKG%Data\INI\GameData.ini"

if not exist "%SRC%" (
  echo.
  echo ERROR: This folder does not contain Data\INI\GameData.ini
  echo Extract the package, then run Install_Loose_GameData.bat from that folder.
  echo.
  pause
  exit /b 1
)

set "GAME_ROOT="
set "ARG1=%~1"
if not "%ARG1%"=="" set "GAME_ROOT=%ARG1%"
if not defined GAME_ROOT if exist "%PKG%generals.exe" set "GAME_ROOT=%PKG%"
if not defined GAME_ROOT if exist "%PKG%Generals.exe" set "GAME_ROOT=%PKG%"
for %%I in ("%PKG%..") do set "PARENT=%%~fI"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%"

if not defined GAME_ROOT (
  echo.
  echo ERROR: generals.exe was not found.
  echo.
  echo Run this installer from the extracted package, or pass the runtime folder:
  echo   Install_Loose_GameData.bat "D:\Path\To\The\Folder\With\generals.exe"
  echo.
  echo The runtime folder is the folder Launch_Specter.bat prints as Game folder.
  echo That is the working directory of the generals.exe it starts.
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%generals.exe" if not exist "%GAME_ROOT%Generals.exe" (
  echo.
  echo ERROR: generals.exe is missing in:
  echo   %GAME_ROOT%
  echo.
  pause
  exit /b 1
)

echo.
echo SPECTER loose camera zoom installer
echo Package:  %PKG%
echo Runtime:  %GAME_ROOT%
echo.

if exist "%GAME_ROOT%INIZH.big" (
  echo INIZH.big is in the runtime folder.
) else (
  echo WARNING: INIZH.big was not found in the runtime folder.
  echo This snapshot keeps INIZH.big next to generals.exe.
  echo If your archives load from the Generals registry InstallPath,
  echo the loose INI still belongs in the folder above, because
  echo Data\INI\GameData.ini is opened from the working directory.
  echo.
)

if not exist "%GAME_ROOT%Data" mkdir "%GAME_ROOT%Data"
if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"

set "DEST=%GAME_ROOT%Data\INI\GameData.ini"
set "MARKER=%GAME_ROOT%Data\INI\SPECTER_CameraZoom_install.txt"
set "BACKUP=%GAME_ROOT%Data\INI\GameData.ini.specter-zoom-backup"

if exist "%DEST%" goto dest_exists
copy /Y /B "%SRC%" "%DEST%" >nul
if errorlevel 1 goto copy_failed
if exist "%MARKER%" goto verify
> "%MARKER%" echo SPECTER_CAMERA_ZOOM_LOOSE
>> "%MARKER%" echo action=created
goto verify

:dest_exists
if exist "%MARKER%" goto refresh
fc /b "%DEST%" "%SRC%" >nul
if errorlevel 1 goto backup_user
> "%MARKER%" echo SPECTER_CAMERA_ZOOM_LOOSE
>> "%MARKER%" echo action=created
goto refresh

:backup_user
copy /Y /B "%DEST%" "%BACKUP%" >nul
if errorlevel 1 (
  echo.
  echo ERROR: Could not back up the existing Data\INI\GameData.ini
  echo The existing file was left unchanged.
  echo.
  pause
  exit /b 1
)
> "%MARKER%" echo SPECTER_CAMERA_ZOOM_LOOSE
>> "%MARKER%" echo action=replaced
echo Backed up the existing loose file to:
echo   %BACKUP%

:refresh
copy /Y /B "%SRC%" "%DEST%" >nul
if errorlevel 1 goto copy_failed

:verify
fc /b "%DEST%" "%SRC%" >nul
if errorlevel 1 (
  echo.
  echo ERROR: Installed file does not match the package.
  echo.
  pause
  exit /b 1
)

echo.
echo Installed:
echo   %DEST%
echo.
echo MaxCameraHeight in this file is 620.0.
echo Remove z_SPECTER_CameraZoom.big from the runtime folder before you
echo judge this test, then start the game with Launch_Specter.bat.
echo.
echo Uninstall with Uninstall_Loose_GameData.bat from this same package.
echo.
pause
exit /b 0

:copy_failed
echo.
echo ERROR: Could not write Data\INI\GameData.ini
echo.
pause
exit /b 1
