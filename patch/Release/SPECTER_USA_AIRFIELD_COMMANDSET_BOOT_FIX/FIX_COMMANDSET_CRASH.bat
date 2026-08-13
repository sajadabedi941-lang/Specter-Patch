@echo off
setlocal EnableExtensions EnableDelayedExpansion
title FIX_COMMANDSET_CRASH
echo.
echo ============================================================
echo  SPECTER - Fix CommandSet.ini crash (loose file cleanup)
echo ============================================================
echo  Run this from your GameRoot (folder with generals.exe /
echo  or the folder that contains Data\ and the SPEC BIG files).
echo.

REM Resolve GameRoot = directory containing this BAT
set "GAMEROOT=%~dp0"
REM strip trailing backslash for nicer logs
if "%GAMEROOT:~-1%"=="\" set "GAMEROOT=%GAMEROOT:~0,-1%"

echo GameRoot: "%GAMEROOT%"
echo.

if not exist "%GAMEROOT%\Data" (
  echo ERROR: Data folder not found next to this BAT.
  echo Place FIX_COMMANDSET_CRASH.bat in your GameRoot and run again.
  echo.
  pause
  exit /b 1
)

set "HIT=0"
set "LOG=%GAMEROOT%\FIX_COMMANDSET_CRASH_LOG.txt"
echo FIX_COMMANDSET_CRASH log > "%LOG%"
echo GameRoot=%GAMEROOT%>> "%LOG%"
echo.>> "%LOG%"

REM ---- 1) Primary loose override: Data\INI\CommandSet.ini ----
set "CS=%GAMEROOT%\Data\INI\CommandSet.ini"
set "CSBAK=%GAMEROOT%\Data\INI\CommandSet.ini.DISABLED_BACKUP"
if exist "%CS%" (
  echo FOUND loose override: Data\INI\CommandSet.ini
  echo FOUND loose override: Data\INI\CommandSet.ini>> "%LOG%"
  if exist "%CSBAK%" (
    echo   Backup already exists: CommandSet.ini.DISABLED_BACKUP
    echo   Renaming active file to CommandSet.ini.DISABLED_BACKUP_ACTIVE
    echo   Backup already exists>> "%LOG%"
    if exist "%GAMEROOT%\Data\INI\CommandSet.ini.DISABLED_BACKUP_ACTIVE" del /f /q "%GAMEROOT%\Data\INI\CommandSet.ini.DISABLED_BACKUP_ACTIVE"
    ren "%CS%" "CommandSet.ini.DISABLED_BACKUP_ACTIVE"
  ) else (
    echo   Backing up to Data\INI\CommandSet.ini.DISABLED_BACKUP
    ren "%CS%" "CommandSet.ini.DISABLED_BACKUP"
  )
  set "HIT=1"
) else (
  echo OK: no loose Data\INI\CommandSet.ini
  echo OK: no loose Data\INI\CommandSet.ini>> "%LOG%"
)

echo.
echo ---- Scanning Data\INI for loose AmericaAirfieldCommandSet* defs ----
echo.>> "%LOG%"
echo Loose AmericaAirfieldCommandSet* scan:>> "%LOG%"

REM Use findstr recursively; rename matching .ini files (not already DISABLED)
for /f "delims=" %%F in ('findstr /s /m /i /c:"CommandSet AmericaAirfieldCommandSet" "%GAMEROOT%\Data\INI\*.ini" 2^>nul') do (
  set "F=%%F"
  echo MATCH: %%F
  echo MATCH: %%F>> "%LOG%"
  echo %%F | findstr /i "DISABLED_BACKUP" >nul
  if errorlevel 1 (
    if /i not "%%~nxF"=="CommandSet.ini" if /i not "%%~nxF"=="CommandSet.ini.DISABLED_BACKUP" if /i not "%%~nxF"=="CommandSet.ini.DISABLED_BACKUP_ACTIVE" (
      if not exist "%%F.DISABLED_BACKUP" (
        echo   Renaming to %%~nxF.DISABLED_BACKUP
        echo   Renamed to %%~nxF.DISABLED_BACKUP>> "%LOG%"
        ren "%%F" "%%~nxF.DISABLED_BACKUP"
        set "HIT=1"
      ) else (
        echo   Backup exists; renaming to %%~nxF.DISABLED_BACKUP_ACTIVE
        if exist "%%F.DISABLED_BACKUP_ACTIVE" del /f /q "%%F.DISABLED_BACKUP_ACTIVE"
        ren "%%F" "%%~nxF.DISABLED_BACKUP_ACTIVE"
        set "HIT=1"
      )
    )
  )
)

echo.
if "%HIT%"=="1" (
  echo DONE: loose CommandSet override^(s^) disabled. Backups kept.
  echo The game should now load CommandSet.ini from _SPEC_DATA_ONE.big.
) else (
  echo DONE: no active loose AmericaAirfield CommandSet overrides found.
)
echo.
echo Log written to: "%LOG%"
echo.
echo Next: ensure Data\_SPEC_DATA_ONE.big and Data\_SPEC_ART_ONE.big
echo from SPECTER_USA_AIRFIELD_COMMANDSET_BOOT_FIX are installed.
echo.
pause
endlocal
