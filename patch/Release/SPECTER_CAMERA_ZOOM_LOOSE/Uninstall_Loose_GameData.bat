@echo off
setlocal EnableExtensions
title SPECTER Camera Zoom - Uninstall Loose GameData.ini

REM Removes only the loose override this installer recorded.
REM action=created: delete Data\INI\GameData.ini so the archive copy is used again.
REM action=replaced: restore Data\INI\GameData.ini.specter-zoom-backup.
REM No marker: leave any loose GameData.ini in place.

cd /d "%~dp0"
set "PKG=%~dp0"
if not "%PKG:~-1%"=="\" set "PKG=%PKG%\"

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
  echo Pass the same runtime folder you used for installation:
  echo   Uninstall_Loose_GameData.bat "D:\Path\To\The\Folder\With\generals.exe"
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

set "DEST=%GAME_ROOT%Data\INI\GameData.ini"
set "MARKER=%GAME_ROOT%Data\INI\SPECTER_CameraZoom_install.txt"
set "BACKUP=%GAME_ROOT%Data\INI\GameData.ini.specter-zoom-backup"

if not exist "%MARKER%" (
  echo.
  echo No SPECTER camera-zoom install record was found in:
  echo   %GAME_ROOT%
  echo Data\INI\GameData.ini was not deleted.
  echo If you copied the INI by hand, remove or restore that file yourself.
  echo.
  pause
  exit /b 1
)

findstr /b /c:"action=created" "%MARKER%" >nul
if not errorlevel 1 goto created
findstr /b /c:"action=replaced" "%MARKER%" >nul
if not errorlevel 1 goto replaced

echo.
echo The install record is not recognized. Nothing was deleted:
echo   %MARKER%
echo.
pause
exit /b 1

:created
if exist "%DEST%" del /f "%DEST%"
if exist "%DEST%" (
  echo.
  echo ERROR: Could not remove Data\INI\GameData.ini
  echo.
  pause
  exit /b 1
)
del /f "%MARKER%"
echo.
echo Removed the loose Data\INI\GameData.ini installed by this package.
echo The game will read GameData.ini from the archives again.
echo.
pause
exit /b 0

:replaced
if not exist "%BACKUP%" (
  echo.
  echo ERROR: The backup is missing:
  echo   %BACKUP%
  echo Data\INI\GameData.ini was left unchanged.
  echo.
  pause
  exit /b 1
)
copy /Y /B "%BACKUP%" "%DEST%" >nul
if errorlevel 1 (
  echo.
  echo ERROR: Could not restore the backup.
  echo.
  pause
  exit /b 1
)
del /f "%BACKUP%"
del /f "%MARKER%"
echo.
echo Restored the previous loose Data\INI\GameData.ini from the backup.
echo.
pause
exit /b 0
