SPECTER FINAL RELEASE - CommandSet Dozer Syntax + Advanced Airfield Fix
======================================================================

Install by running Install_SpecterPatch.bat or copying _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into GameRoot.

WARNING: Do not leave a loose Data\INI\CommandSet.ini override in GameRoot or a higher-priority patch folder.
Loose overrides can reintroduce stale commandsets or mixed line endings.

America Advanced Airfield roster:
  1. Command_ConstructPatch_America_B2 -> Patch_America_B2
  2. Command_ConstructPatch_America_B21 -> Patch_America_B21
  3. Command_ConstructPatch_America_B52 -> Patch_America_B52
  4. Command_ConstructAmericaJetC5Galaxy_AAB -> Patch_America_C17
  5. Command_ConstructAmericaJetF117_AAB -> AmericaJetStealthFighter
  6. Command_ConstructPatch_America_E3 -> Patch_America_E3

America_AdvancedAirBase:
  Prerequisites=empty
  Scale=2.00
  Geometry=224.0 x 148.0 x 50.0
  Model/art=US_AirField

Fixes verified:
- Existing stock AmericaDozerCommandSet patched in-place; no duplicate created.
- CommandSet.ini is LF-only.
- USA dozer Strategy Center commands removed; Advanced Airfield button inserted.
- AmericaVehicleDozer uses AmericaDozerCommandSet.
- America Command Center is untouched.
- F-117 science gate cleared.
- Russia 9M317_MissileObject remains no PRELOAD.

DATA SHA256=bbb247809bfb6bde10aca03a9bf9bad802f50b2ce6a5c25aa6f538487a148f08
ART  SHA256=bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
ZIP  SHA256=9bcf8ba305c265e8218292728f17208b3659840d2ec9744ab3e648378b8ae9a8
