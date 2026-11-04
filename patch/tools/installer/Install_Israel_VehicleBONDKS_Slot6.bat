@echo off
setlocal EnableExtensions
title SPECTER - Israel_VehicleBONDKS Command Center slot 6

REM Copies the winning ControlBar files into Data\INI\ (loose, first-wins)
REM and the overlay BIG that loads after _SPEC_DATA_ONE.big.

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
echo  SPECTER Israel_VehicleBONDKS CC slot 6
echo ============================================================
echo.
echo Installer folder:
echo   %PATCH_DIR%
echo.

if not exist "%PATCH_DIR%Data\INI\CommandSet_SpecterPatch.ini" (
  echo ERROR: Missing Data\INI\CommandSet_SpecterPatch.ini
  echo This is the winning Israel Command Center bar. Slot 6 is BONDKS.
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
  echo Install_Israel_VehicleBONDKS_Slot6.bat again.
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo Game folder:
echo   %GAME_ROOT%
echo.

if not exist "%GAME_ROOT%Data\INI\" mkdir "%GAME_ROOT%Data\INI"
if errorlevel 1 (
  echo ERROR: Cannot create Data\INI in the game folder.
  echo.
  pause
  exit /b 1
)

echo Copying winning loose CommandSet to Data\INI\ ...
copy /Y "%PATCH_DIR%Data\INI\CommandSet_SpecterPatch.ini" "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandSet_SpecterPatch.ini
  echo.
  pause
  exit /b 1
)
echo   OK: %GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini

echo Copying CommandButton to Data\INI\ ...
copy /Y "%PATCH_DIR%Data\INI\CommandButton_Israel_VehicleBONDKS.ini" "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleBONDKS.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandButton_Israel_VehicleBONDKS.ini
  echo.
  pause
  exit /b 1
)
echo   OK: %GAME_ROOT%Data\INI\CommandButton_Israel_VehicleBONDKS.ini

set "OVERLAY_BIG=_SPEC_DATA_ZZ_Israel_VehicleBONDKS.big"
if exist "%PATCH_DIR%%OVERLAY_BIG%" (
  echo Copying overlay BIG ^(loads after _SPEC_DATA_ONE.big^) ...
  copy /Y "%PATCH_DIR%%OVERLAY_BIG%" "%GAME_ROOT%%OVERLAY_BIG%" >nul
  if errorlevel 1 (
    echo ERROR: Failed to copy %OVERLAY_BIG%
    echo.
    pause
    exit /b 1
  )
  echo   OK: %GAME_ROOT%%OVERLAY_BIG%
)

if exist "%GAME_ROOT%_SPECTER_Israel_VehicleBONDKS_cc_slot6.big" (
  echo.
  echo   NOTE: _SPECTER_Israel_VehicleBONDKS_cc_slot6.big may still be here.
  echo   Slot 6 is now the loose file Data\INI\CommandSet_SpecterPatch.ini
  echo   which beats every BIG. You can delete the old overlay BIG.
  echo.
)

echo.
echo SUCCESS: Winning ControlBar files are in Data\INI\.
echo Play as Israel, select the Command Center. Slot 6 is BONDKS.
echo.
pause
endlocal
exit /b 0
