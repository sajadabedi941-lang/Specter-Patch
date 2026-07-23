@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter Startup Crash Fix
cd /d "%~dp0"
echo.
echo  Specter Ultimate Warfare - Startup Crash Fix
echo  Lightweight merge into existing GameRoot Data
echo.
set "GAMEROOT=%~1"
if not defined GAMEROOT (
  set /p "GAMEROOT=Enter GameRoot path (folder with Data and generals.exe): "
)
if not defined GAMEROOT (
  echo ERROR: GameRoot not set.
  exit /b 1
)
if not exist "%GAMEROOT%\Data\" (
  echo ERROR: "%GAMEROOT%\Data" not found.
  exit /b 1
)
echo GameRoot: %GAMEROOT%
echo.
echo [1/2] Removing stale crash files...
if exist "%GAMEROOT%\Data\INI\CommandButton_RuntimeFix_RussiaRS24.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\CommandButton_RuntimeFix_RussiaRS24.ini
  del /f /q "%GAMEROOT%\Data\INI\CommandButton_RuntimeFix_RussiaRS24.ini"
)
if exist "%GAMEROOT%\Data\INI\CountryBalance.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\CountryBalance.ini
  del /f /q "%GAMEROOT%\Data\INI\CountryBalance.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\" (
  echo   DELDIR %GAMEROOT%\Data\INI\Economy
  rmdir /s /q "%GAMEROOT%\Data\INI\Economy"
)
if exist "%GAMEROOT%\Data\INI\Economy\AsymmetricBalance.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\AsymmetricBalance.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\AsymmetricBalance.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\BUYER_PRICE_EXAMPLES.txt" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\BUYER_PRICE_EXAMPLES.txt
  del /f /q "%GAMEROOT%\Data\INI\Economy\BUYER_PRICE_EXAMPLES.txt"
)
if exist "%GAMEROOT%\Data\INI\Economy\COUNTRY_BALANCE.txt" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\COUNTRY_BALANCE.txt
  del /f /q "%GAMEROOT%\Data\INI\Economy\COUNTRY_BALANCE.txt"
)
if exist "%GAMEROOT%\Data\INI\Economy\DYNAMIC_PRICING.txt" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\DYNAMIC_PRICING.txt
  del /f /q "%GAMEROOT%\Data\INI\Economy\DYNAMIC_PRICING.txt"
)
if exist "%GAMEROOT%\Data\INI\Economy\DomesticProduction.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\DomesticProduction.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\DomesticProduction.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\EquipmentOrigin.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\EquipmentOrigin.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\EquipmentOrigin.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\FactionEconomy.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\FactionEconomy.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\FactionEconomy.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\PricingDefaults.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\PricingDefaults.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\PricingDefaults.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\ResourceIncome.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\ResourceIncome.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\ResourceIncome.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\TechnologyClass.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\TechnologyClass.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\TechnologyClass.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\UnitCategory.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\UnitCategory.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\UnitCategory.ini"
)
if exist "%GAMEROOT%\Data\INI\Economy\UnitPricingRegistry.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\Economy\UnitPricingRegistry.ini
  del /f /q "%GAMEROOT%\Data\INI\Economy\UnitPricingRegistry.ini"
)
if exist "%GAMEROOT%\Data\INI\GlobalBuildLimits_SpecterPatch.ini" (
  echo   DELETE %GAMEROOT%\Data\INI\GlobalBuildLimits_SpecterPatch.ini
  del /f /q "%GAMEROOT%\Data\INI\GlobalBuildLimits_SpecterPatch.ini"
)
echo.
echo [2/2] Merging fixed Data files...
if not exist "%~dp0Data\" (
  echo ERROR: Data folder missing next to Install_Fix.bat
  exit /b 1
)
xcopy "%~dp0Data\*" "%GAMEROOT%\Data\" /E /I /Y /Q
if errorlevel 1 (
  echo ERROR: xcopy failed.
  exit /b 1
)
echo.
echo DONE. Launch Generals Zero Hour and verify Main Menu + Skirmish.
echo.
pause
endlocal
