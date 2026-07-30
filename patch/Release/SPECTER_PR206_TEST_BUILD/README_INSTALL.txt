SPECTER PR #206 MERGE-READY BUILD NOTES
=======================================

Continues existing PR #206 workstream (Turkey/UAE + global audit + init fixes).
No full re-audit. No new project.

Latest init fixes (post UAE_CommandCenter):
- North Korea/Buildings/Iraq_PowerPlant.ini
  CommandSet = ChinaPowerPlantCommandSet (was comment-only)
- North Korea/Infantry/Iraq_Worker.ini
  CommandSetUpgrade -> Iraq_WorkerCommandSet (was missing GLAWorkerCommandSet)

Also:
- Merged origin/main; kept validated PR #206 Turkey_WeaponObjects,
  Turkey_CommandCenter, Turkey_Airfield_T, UAE_CommandCenter.

Packer overlays Specter North Korea tree + late short-path NK overrides.
See INIT_STARTUP_AUDIT_REPORT.txt.

Install (when packing with baseline BIG):
1. Backup Data\_SPEC_DATA_ONE.big
2. Replace with packaged _SPEC_DATA_ONE.big
3. Keep _SPEC_ART_ONE.big unchanged
4. Smoke-test skirmish startup
