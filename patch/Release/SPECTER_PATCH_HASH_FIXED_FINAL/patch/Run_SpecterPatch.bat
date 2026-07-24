@echo off
setlocal EnableExtensions
title Specter Ultimate Warfare Expansion - Run / Install Patch
cd /d "%~dp0"

echo.
echo  Specter Ultimate Warfare Expansion
echo  Safe patch activator (overlay install)
echo  -------------------------------------
echo  This will:
echo    - Back up any overwritten game files
echo    - Copy ONLY patch Data\ and Art\ overlays
echo    - Never modify Data.zip / .big / _SPEC_* archives
echo    - Verify SYNC_MANIFEST.sha256
echo.

if not exist "%~dp0Install_SpecterPatch.bat" (
  echo ERROR: Install_SpecterPatch.bat not found next to this launcher.
  pause
  exit /b 1
)

call "%~dp0Install_SpecterPatch.bat" %*
set ERR=%ERRORLEVEL%
if %ERR% NEQ 0 (
  echo.
  echo Install finished with errors. See messages above.
  pause
  exit /b %ERR%
)

echo.
echo Patch active. Launch Specter / Zero Hour from your game folder.
pause
exit /b 0
