@echo off
setlocal EnableExtensions
title Specter Launcher
cd /d "%~dp0"

if exist "%~dp0generals.exe" (
  start "" "%~dp0generals.exe"
  exit /b 0
)
if exist "%~dp0Generals.exe" (
  start "" "%~dp0Generals.exe"
  exit /b 0
)
if exist "%~dp0..\generals.exe" (
  start "" "%~dp0..\generals.exe"
  exit /b 0
)
if exist "%~dp0..\Generals.exe" (
  start "" "%~dp0..\Generals.exe"
  exit /b 0
)

echo ERROR: generals.exe not found.
echo Put this launcher in the game folder or in the patch subfolder.
echo.
pause
exit /b 1
