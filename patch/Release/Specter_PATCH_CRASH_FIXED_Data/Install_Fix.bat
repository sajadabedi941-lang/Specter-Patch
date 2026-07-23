@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter PATCH CRASH FIXED
cd /d "%~dp0"
echo.
echo  Specter_PATCH_CRASH_FIXED - merge repaired INIs
echo.
set "GAMEROOT=%~1"
if not defined GAMEROOT set /p "GAMEROOT=Enter GameRoot (folder with Data\): "
if not defined GAMEROOT (echo ERROR: no GameRoot & exit /b 1)
if not exist "%GAMEROOT%\Data\" (echo ERROR: Data not found & exit /b 1)
echo GameRoot: %GAMEROOT%
echo.
echo [1/3] Removing flat duplicate INIs from Data\INI\ root...
if exist "%GAMEROOT%\Data\INI\AIR_FORCE_EXPANSION.txt" (
  echo   DELETE Data\INI\AIR_FORCE_EXPANSION.txt
  del /f /q "%GAMEROOT%\Data\INI\AIR_FORCE_EXPANSION.txt"
)
if exist "%GAMEROOT%\Data\INI\AbbasLauncher.ini" (
  echo   DELETE Data\INI\AbbasLauncher.ini
  del /f /q "%GAMEROOT%\Data\INI\AbbasLauncher.ini"
)
if exist "%GAMEROOT%\Data\INI\Airborne.ini" (
  echo   DELETE Data\INI\Airborne.ini
  del /f /q "%GAMEROOT%\Data\INI\Airborne.ini"
)
if exist "%GAMEROOT%\Data\INI\Aircraft_AAB_Global.ini" (
  echo   DELETE Data\INI\Aircraft_AAB_Global.ini
  del /f /q "%GAMEROOT%\Data\INI\Aircraft_AAB_Global.ini"
)
if exist "%GAMEROOT%\Data\INI\Aircraft_AirForceExpansion.ini" (
  echo   DELETE Data\INI\Aircraft_AirForceExpansion.ini
  del /f /q "%GAMEROOT%\Data\INI\Aircraft_AirForceExpansion.ini"
)
if exist "%GAMEROOT%\Data\INI\Britain_CombatDrone.ini" (
  echo   DELETE Data\INI\Britain_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\Britain_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\Britain_F35B.ini" (
  echo   DELETE Data\INI\Britain_F35B.ini
  del /f /q "%GAMEROOT%\Data\INI\Britain_F35B.ini"
)
if exist "%GAMEROOT%\Data\INI\Egypt_CommandCenter.ini" (
  echo   DELETE Data\INI\Egypt_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Egypt_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Egypt_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Egypt_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Egypt_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\France_CombatDrone.ini" (
  echo   DELETE Data\INI\France_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\France_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\Germany_CombatDrone.ini" (
  echo   DELETE Data\INI\Germany_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\Germany_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\India_CombatDrone.ini" (
  echo   DELETE Data\INI\India_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\India_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\India_CommandCenter.ini" (
  echo   DELETE Data\INI\India_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\India_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\India_MilitaryHQ.ini" (
  echo   DELETE Data\INI\India_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\India_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\India_TejasMk2.ini" (
  echo   DELETE Data\INI\India_TejasMk2.ini
  del /f /q "%GAMEROOT%\Data\INI\India_TejasMk2.ini"
)
if exist "%GAMEROOT%\Data\INI\Israel_CommandCenter.ini" (
  echo   DELETE Data\INI\Israel_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Israel_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Israel_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Israel_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Israel_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Italy_CombatDrone.ini" (
  echo   DELETE Data\INI\Italy_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\Italy_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\Japan_CombatDrone.ini" (
  echo   DELETE Data\INI\Japan_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\Japan_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\Japan_MQ9.ini" (
  echo   DELETE Data\INI\Japan_MQ9.ini
  del /f /q "%GAMEROOT%\Data\INI\Japan_MQ9.ini"
)
if exist "%GAMEROOT%\Data\INI\Karrar-2.ini" (
  echo   DELETE Data\INI\Karrar-2.ini
  del /f /q "%GAMEROOT%\Data\INI\Karrar-2.ini"
)
if exist "%GAMEROOT%\Data\INI\Lamiaa.ini" (
  echo   DELETE Data\INI\Lamiaa.ini
  del /f /q "%GAMEROOT%\Data\INI\Lamiaa.ini"
)
if exist "%GAMEROOT%\Data\INI\Libya_CommandCenter.ini" (
  echo   DELETE Data\INI\Libya_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Libya_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Libya_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Libya_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Libya_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\MilitaryHQ_StockFactions.ini" (
  echo   DELETE Data\INI\MilitaryHQ_StockFactions.ini
  del /f /q "%GAMEROOT%\Data\INI\MilitaryHQ_StockFactions.ini"
)
if exist "%GAMEROOT%\Data\INI\Pakistan_CommandCenter.ini" (
  echo   DELETE Data\INI\Pakistan_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Pakistan_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Pakistan_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Pakistan_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Pakistan_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Russia_AD_TorM.ini" (
  echo   DELETE Data\INI\Russia_AD_TorM.ini
  del /f /q "%GAMEROOT%\Data\INI\Russia_AD_TorM.ini"
)
if exist "%GAMEROOT%\Data\INI\SaudiArabia_CombatDrone.ini" (
  echo   DELETE Data\INI\SaudiArabia_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\SaudiArabia_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\SaudiArabia_CommandCenter.ini" (
  echo   DELETE Data\INI\SaudiArabia_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\SaudiArabia_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\SaudiArabia_MilitaryHQ.ini" (
  echo   DELETE Data\INI\SaudiArabia_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\SaudiArabia_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\SouthAfrica_CommandCenter.ini" (
  echo   DELETE Data\INI\SouthAfrica_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\SouthAfrica_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\SouthAfrica_MilitaryHQ.ini" (
  echo   DELETE Data\INI\SouthAfrica_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\SouthAfrica_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\SouthKorea_CombatDrone.ini" (
  echo   DELETE Data\INI\SouthKorea_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\SouthKorea_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\SpecialForces.ini" (
  echo   DELETE Data\INI\SpecialForces.ini
  del /f /q "%GAMEROOT%\Data\INI\SpecialForces.ini"
)
if exist "%GAMEROOT%\Data\INI\Sweden_CombatDrone.ini" (
  echo   DELETE Data\INI\Sweden_CombatDrone.ini
  del /f /q "%GAMEROOT%\Data\INI\Sweden_CombatDrone.ini"
)
if exist "%GAMEROOT%\Data\INI\Syria_CommandCenter.ini" (
  echo   DELETE Data\INI\Syria_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Syria_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Syria_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Syria_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Syria_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_AWACS.ini" (
  echo   DELETE Data\INI\Turkey_AWACS.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_AWACS.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_Akinci.ini" (
  echo   DELETE Data\INI\Turkey_Akinci.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_Akinci.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_Bora.ini" (
  echo   DELETE Data\INI\Turkey_Bora.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_Bora.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_CommandCenter.ini" (
  echo   DELETE Data\INI\Turkey_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_EliteMaroonBerets.ini" (
  echo   DELETE Data\INI\Turkey_EliteMaroonBerets.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_EliteMaroonBerets.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_F16Block70.ini" (
  echo   DELETE Data\INI\Turkey_F16Block70.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_F16Block70.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_Kizilelma.ini" (
  echo   DELETE Data\INI\Turkey_Kizilelma.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_Kizilelma.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Turkey_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_TB2.ini" (
  echo   DELETE Data\INI\Turkey_TB2.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_TB2.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_Tu-22M3.ini" (
  echo   DELETE Data\INI\Turkey_Tu-22M3.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_Tu-22M3.ini"
)
if exist "%GAMEROOT%\Data\INI\Turkey_WeaponObjects.ini" (
  echo   DELETE Data\INI\Turkey_WeaponObjects.ini
  del /f /q "%GAMEROOT%\Data\INI\Turkey_WeaponObjects.ini"
)
if exist "%GAMEROOT%\Data\INI\UAE_CommandCenter.ini" (
  echo   DELETE Data\INI\UAE_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\UAE_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\UAE_MQ9.ini" (
  echo   DELETE Data\INI\UAE_MQ9.ini
  del /f /q "%GAMEROOT%\Data\INI\UAE_MQ9.ini"
)
if exist "%GAMEROOT%\Data\INI\UAE_MilitaryHQ.ini" (
  echo   DELETE Data\INI\UAE_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\UAE_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Ukraine_CommandCenter.ini" (
  echo   DELETE Data\INI\Ukraine_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Ukraine_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Ukraine_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Ukraine_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Ukraine_MilitaryHQ.ini"
)
if exist "%GAMEROOT%\Data\INI\Vietnam_CommandCenter.ini" (
  echo   DELETE Data\INI\Vietnam_CommandCenter.ini
  del /f /q "%GAMEROOT%\Data\INI\Vietnam_CommandCenter.ini"
)
if exist "%GAMEROOT%\Data\INI\Vietnam_MilitaryHQ.ini" (
  echo   DELETE Data\INI\Vietnam_MilitaryHQ.ini
  del /f /q "%GAMEROOT%\Data\INI\Vietnam_MilitaryHQ.ini"
)
echo.
echo [2/3] Removing leftover tool schemas (init crash)...
if exist "%GAMEROOT%\Data\INI\CountryBalance.ini" del /f /q "%GAMEROOT%\Data\INI\CountryBalance.ini"
if exist "%GAMEROOT%\Data\INI\GlobalBuildLimits_SpecterPatch.ini" del /f /q "%GAMEROOT%\Data\INI\GlobalBuildLimits_SpecterPatch.ini"
if exist "%GAMEROOT%\Data\INI\CommandButton_RuntimeFix_RussiaRS24.ini" del /f /q "%GAMEROOT%\Data\INI\CommandButton_RuntimeFix_RussiaRS24.ini"
if exist "%GAMEROOT%\Data\INI\Economy\" rmdir /s /q "%GAMEROOT%\Data\INI\Economy"
echo.
echo [3/3] Merging repaired Data files...
xcopy "%~dp0Data\*" "%GAMEROOT%\Data\" /E /I /Y /Q
if errorlevel 1 (echo ERROR: xcopy failed & exit /b 1)
echo.
echo DONE. Launch ZH and verify Main Menu + Skirmish.
pause
endlocal
