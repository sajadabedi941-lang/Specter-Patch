SPECTER PR #206 TEST BUILD
==========================

Baseline: PR #206 Turkey WeaponObjects full rebuild BIG
Plus: current PR #206 branch Turkey Armed Forces INI fixes embedded.
Plus: UAE_MilitaryHQ AmericaCommandCenter donor remap (v2).
Plus: UAE_Worker GLAWorkerCommandSet / UIWRKR_SKN fix.

NOT included: PR #207 / #208 faction reset work.
No faction rebuild was performed for this package.

UAE_Worker fix:
- Object name unchanged: UAE_Worker
- Model UIWRKR_SKN -> AIRNGR_IDG (ART present)
- CommandSetUpgrade no longer references missing GLAWorkerCommandSet
  (BIG has typo GLAWorkerCommandSetg); uses UAE_WorkerCommandSet
- ASCII-only INI

Install:
1. Backup your current Data\_SPEC_DATA_ONE.big
2. Replace Data\_SPEC_DATA_ONE.big with this package file
3. Keep Data\_SPEC_ART_ONE.big unchanged
4. Launch skirmish and smoke-test UAE worker / Military HQ path

After successful test: merge PR #206 and cut final release.
