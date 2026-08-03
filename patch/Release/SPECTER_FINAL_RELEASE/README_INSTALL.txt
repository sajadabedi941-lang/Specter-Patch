SPECTER FINAL RELEASE - CommandSet Dozer Syntax Fix
====================================================

This release fixes the Specter GameRoot BIG crash at:
  Data\INI\CommandSet.ini parsing error / CommandSet AmericaDozerCommandSet

Install by running Install_SpecterPatch.bat or copying _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into GameRoot.

WARNING: Do not leave a loose Data\INI\CommandSet.ini override in GameRoot or a higher-priority patch folder.
Loose overrides can reintroduce stale commandsets or mixed line endings.

Fixes verified:
- Existing stock AmericaDozerCommandSet patched in-place; no duplicate created.
- CommandSet.ini is LF-only.
- AmericaVehicleDozer uses AmericaDozerCommandSet.
- America Command Center is untouched.
- AAB six-aircraft, early unlock, approx 2x size retained.
- Russia 9M317_MissileObject remains no PRELOAD.

DATA SHA256=2fcc582e767001ac3e44e319a4f95f781dd112ebd7f612e6d216f1ea2be87f5c
ART  SHA256=bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
ZIP  SHA256=ab75510c1346b9865014f223f3498487c7cdcad972926b0c6fd4028cbbe29d00
