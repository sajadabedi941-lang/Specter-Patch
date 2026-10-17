#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mcs -sdk:4 -target:winexe \
  -r:System.Windows.Forms.dll -r:System.Drawing.dll \
  -out:"$ROOT/Install_SpecterPatch.exe" \
  "$ROOT/Install_SpecterPatch.cs"
file "$ROOT/Install_SpecterPatch.exe"
