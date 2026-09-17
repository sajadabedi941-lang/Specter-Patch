# Verify parse-fix DATA before a Windows ZH launch. Run from this folder.
$ErrorActionPreference = "Stop"
$expected = "4bf21a180a64dbd82a15cf5f9d67e5f7c059422a7be8bea6cf2ad9f837fb3855"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $here "_SPEC_DATA_ONE.big"
if (-not (Test-Path $data)) {
    Write-Error "Missing $data"
    exit 1
}
$actual = (Get-FileHash -LiteralPath $data -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "FILE   $data"
Write-Host "EXPECT $expected"
Write-Host "ACTUAL $actual"
if ($actual -ne $expected) {
    Write-Error "SHA256 mismatch. Do not launch. Do not ZIP."
    exit 1
}
Write-Host "SHA256 OK. Copy this BIG next to Windows generals.exe. Do not replace ART."
exit 0
