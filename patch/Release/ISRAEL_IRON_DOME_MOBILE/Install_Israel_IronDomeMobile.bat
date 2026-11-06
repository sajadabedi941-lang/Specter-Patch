@echo off
setlocal EnableExtensions
title Install Israel Iron Dome Mobile

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"
echo.
echo ============================================================
echo  Israel Iron Dome Mobile
echo ============================================================
echo  Installer folder:
echo    %PATCH_DIR%
echo.

if not exist "%PATCH_DIR%Data\INI\CommandSet.ini" (
  echo ERROR: Missing Data\INI\CommandSet.ini
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\CommandSet_SpecterPatch.ini" (
  echo ERROR: Missing Data\INI\CommandSet_SpecterPatch.ini
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" (
  echo ERROR: Missing Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" (
  echo ERROR: Missing Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" (
  echo ERROR: Missing object INI
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Art\W3D\BONDKS.W3D" (
  echo ERROR: Missing Art\W3D\BONDKS.W3D
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Art\Textures\T_M978_D02.tga" (
  echo ERROR: Missing Art\Textures\T_M978_D02.tga
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%Data\English\generals.csf" (
  echo ERROR: Missing Data\English\generals.csf
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
  echo Copy this folder into SPECTER FINAL and run the installer again,
  echo or copy the Data and Art folders into the game folder yourself.
  pause
  exit /b 1
)

echo Game folder:
echo   %GAME_ROOT%
echo.

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
if not exist "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled" mkdir "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled"
if not exist "%GAME_ROOT%Data\English" mkdir "%GAME_ROOT%Data\English"
if not exist "%GAME_ROOT%Art\W3D" mkdir "%GAME_ROOT%Art\W3D"
if not exist "%GAME_ROOT%Art\Textures" mkdir "%GAME_ROOT%Art\Textures"

echo Copying INI...
copy /Y "%PATCH_DIR%Data\INI\CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
copy /Y "%PATCH_DIR%Data\INI\CommandSet_SpecterPatch.ini" "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini" >nul
copy /Y "%PATCH_DIR%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" >nul
copy /Y "%PATCH_DIR%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" "%GAME_ROOT%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" >nul
copy /Y "%PATCH_DIR%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" >nul

echo Copying English strings...
REM ss1 has no loose generals.csf. This file is the winning ss1 CSF
REM from _SPEC_DATA_ONE.big plus three Iron Dome Mobile labels only.
copy /Y "%PATCH_DIR%Data\English\generals.csf" "%GAME_ROOT%Data\English\generals.csf" >nul

echo Copying model and textures...
copy /Y "%PATCH_DIR%Art\W3D\BONDKS.W3D" "%GAME_ROOT%Art\W3D\BONDKS.W3D" >nul
copy /Y "%PATCH_DIR%Art\Textures\*.tga" "%GAME_ROOT%Art\Textures\" >nul

echo.
echo Installed:
echo   Data\INI\CommandSet.ini
echo     AirF_AmericaCommandCenterCommandSet slot 11 = Iron Dome Mobile
echo   Data\INI\CommandSet_SpecterPatch.ini
echo     Israel_CommandCenterCommandSet slot 1 = Iron Dome Mobile
echo   Object Israel_VehicleIronDomeMobile
echo   Art\W3D\BONDKS.W3D
echo.
echo This installer does not change Iron Dome static, Barak8, MilitaryHQ,
echo the Israel dozer, or Israel_CommandCenter.ini.
echo.
pause
exit /b 0
