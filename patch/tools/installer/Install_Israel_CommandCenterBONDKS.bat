@echo off
setlocal EnableExtensions
title SPECTER - Israel Command Center BONDKS

REM Copies unique Israel CC + dozer CommandSet into Data\INI\ (loose, first-wins).
REM Does not overwrite CommandSet.ini or CommandButton.ini.

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open installer folder.
  echo.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"
echo.
echo ============================================================
echo  SPECTER Israel Command Center BONDKS
echo ============================================================
echo.
echo Installer folder:
echo   %PATCH_DIR%
echo.

if not exist "%PATCH_DIR%Data\INI\CommandSet_Israel_CommandCenterBONDKS.ini" (
  echo ERROR: Missing Data\INI\CommandSet_Israel_CommandCenterBONDKS.ini
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\CommandButton_Israel_CommandCenterBONDKS.ini" (
  echo ERROR: Missing Data\INI\CommandButton_Israel_CommandCenterBONDKS.ini
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\CommandButton_Israel_VehicleBONDKS.ini" (
  echo ERROR: Missing Data\INI\CommandButton_Israel_VehicleBONDKS.ini
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_CommandCenterBONDKS.ini" (
  echo ERROR: Missing Israel_CommandCenterBONDKS.ini
  echo.
  pause
  exit /b 1
)

set "GAME_ROOT="
set "PARENT="
for %%I in ("%PATCH_DIR%..") do set "PARENT=%%~fI"

if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PATCH_DIR%Generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"

if not defined GAME_ROOT (
  echo ERROR: generals.exe was not found.
  echo Extract this ZIP into the SPECTER / Zero Hour folder
  echo ^(the folder that already contains generals.exe^), then run
  echo Install_Israel_CommandCenterBONDKS.bat again.
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo Game folder:
echo   %GAME_ROOT%
echo.

if not exist "%GAME_ROOT%Data\INI\" mkdir "%GAME_ROOT%Data\INI"
if not exist "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Buildings\" mkdir "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Buildings"
if not exist "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\" mkdir "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled"
if not exist "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\AirDefense\" mkdir "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\AirDefense"
if not exist "%GAME_ROOT%Art\W3D\" mkdir "%GAME_ROOT%Art\W3D"
if not exist "%GAME_ROOT%Art\Textures\" mkdir "%GAME_ROOT%Art\Textures"

echo Copying unique INI files to Data\INI\ ...
copy /Y "%PATCH_DIR%Data\INI\CommandSet_Israel_CommandCenterBONDKS.ini" "%GAME_ROOT%Data\INI\CommandSet_Israel_CommandCenterBONDKS.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%PATCH_DIR%Data\INI\CommandButton_Israel_CommandCenterBONDKS.ini" "%GAME_ROOT%Data\INI\CommandButton_Israel_CommandCenterBONDKS.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%PATCH_DIR%Data\INI\CommandButton_Israel_VehicleBONDKS.ini" "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleBONDKS.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_CommandCenterBONDKS.ini" "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_CommandCenterBONDKS.ini" >nul
if errorlevel 1 goto :copyfail
if exist "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini" (
  copy /Y "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini" "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini" >nul
  if errorlevel 1 goto :copyfail
)
if exist "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\AirDefense\Israel_VehicleBONDKS.ini" (
  copy /Y "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\AirDefense\Israel_VehicleBONDKS.ini" "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\AirDefense\Israel_VehicleBONDKS.ini" >nul
  if errorlevel 1 goto :copyfail
)
echo   OK: unique Data\INI files copied
echo   CommandSet.ini and CommandButton.ini were not overwritten.

set "OVERLAY_BIG=_SPEC_DATA_ZZ_Israel_CommandCenterBONDKS.big"
if exist "%PATCH_DIR%%OVERLAY_BIG%" (
  echo Copying overlay BIG ...
  copy /Y "%PATCH_DIR%%OVERLAY_BIG%" "%GAME_ROOT%%OVERLAY_BIG%" >nul
  if errorlevel 1 goto :copyfail
  echo   OK: %GAME_ROOT%%OVERLAY_BIG%
)

echo.
echo SUCCESS: Israel dozer slot 8 builds Israel_CommandCenterBONDKS.
echo That building slot 6 buys Israel_VehicleBONDKS.
echo Military HQ, Iron Dome, Barak-8, and other countries are unchanged.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: File copy failed.
echo.
pause
endlocal
exit /b 1
