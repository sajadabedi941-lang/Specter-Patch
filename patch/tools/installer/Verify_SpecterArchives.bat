@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM Validate the four required SPECTER BIGs in one directory.
REM Usage: Verify_SpecterArchives.bat <DIR>
REM Exit 0 on match, 1 on missing certutil / missing file / size mismatch / hash mismatch.
REM Does not pause. Callers print SUCCESS only after this returns 0.

if "%~1"=="" (
  echo ERROR: Verify_SpecterArchives.bat requires a directory argument.
  exit /b 1
)

set "DIR=%~1"
if not exist "%DIR%" (
  echo ERROR: Directory does not exist:
  echo   %DIR%
  exit /b 1
)
if not "%DIR:~-1%"=="\" set "DIR=%DIR%\"

where certutil >nul 2>&1
if errorlevel 1 (
  echo ERROR: certutil.exe was not found.
  echo SHA-256 integrity checks cannot be skipped.
  echo certutil is part of Windows and must be on PATH.
  exit /b 1
)

REM Sizes and SHA-256 from SPECTER_SPEC_ART_DATA.SHA256.txt and the
REM verified 0_SPECTER_NatoSpainDisplay.big. Do not invent hashes.
call :CHECK_ONE "%DIR%_SPEC_DATA_ONE.big" 373898957 169d07b3365817abdf9c2140644a2bf4ac68a4e367a57b48dbc1b347fbeb1ae8
if errorlevel 1 exit /b 1
call :CHECK_ONE "%DIR%_SPEC_ART_ONE.big" 2144972013 9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8
if errorlevel 1 exit /b 1
call :CHECK_ONE "%DIR%_SPEC_ART_TWO.big" 307254782 a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af
if errorlevel 1 exit /b 1
call :CHECK_ONE "%DIR%0_SPECTER_NatoSpainDisplay.big" 1608985 a2558dd5ccea23b55189d96698a42a4ac91b82455db27b0d7511a366ea4b129d
if errorlevel 1 exit /b 1

echo   All four archives exist, match official byte sizes, and match SHA-256.
exit /b 0

:CHECK_ONE
set "FILE=%~1"
set "EXPSIZE=%~2"
set "EXPSHA=%~3"
if not exist "%FILE%" (
  echo ERROR: Missing required archive:
  echo   %FILE%
  echo A leftover file in another folder does not replace this source.
  exit /b 1
)
set "GOTSIZE="
for %%A in ("%FILE%") do set "GOTSIZE=%%~zA"
if not "!GOTSIZE!"=="%EXPSIZE%" (
  echo ERROR: Wrong size for:
  echo   %FILE%
  echo   got !GOTSIZE! bytes, expected %EXPSIZE%
  echo Truncated or incomplete copy. SHA-256 was not skipped.
  exit /b 1
)

set "TMPHASH=%TEMP%\specter_sha256_%RANDOM%.txt"
certutil -hashfile "%FILE%" SHA256 > "%TMPHASH%" 2>&1
if errorlevel 1 (
  echo ERROR: certutil failed to hash:
  echo   %FILE%
  echo SHA-256 integrity checks cannot be skipped.
  if exist "%TMPHASH%" type "%TMPHASH%"
  if exist "%TMPHASH%" del "%TMPHASH%" >nul 2>&1
  exit /b 1
)

set "GOTSHA="
for /f "usebackq delims=" %%L in ("%TMPHASH%") do (
  set "LINE=%%L"
  set "CAND=!LINE: =!"
  REM SHA-256 hex is exactly 64 characters after spaces are removed.
  if not "!CAND!"=="" if not "!CAND:~63,1!"=="" if "!CAND:~64,1!"=="" (
    if not defined GOTSHA set "GOTSHA=!CAND!"
  )
)
if exist "%TMPHASH%" del "%TMPHASH%" >nul 2>&1

if not defined GOTSHA (
  echo ERROR: Could not parse certutil SHA-256 output for:
  echo   %FILE%
  echo SHA-256 integrity checks cannot be skipped.
  exit /b 1
)
if /I not "!GOTSHA!"=="%EXPSHA%" (
  echo ERROR: SHA-256 mismatch for:
  echo   %FILE%
  echo   got  !GOTSHA!
  echo   want %EXPSHA%
  echo Size matched but contents are not the official archive.
  exit /b 1
)
echo   OK: %~nx1  size %EXPSIZE%  SHA-256 match
exit /b 0
