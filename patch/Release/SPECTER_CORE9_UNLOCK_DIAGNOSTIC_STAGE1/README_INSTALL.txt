SPECTER CORE9 UNLOCK DIAGNOSTIC STAGE1
======================================
Baseline: SPECTER_CORE9_FULL_UNLOCK_MATCH_START (pre-PR#310)

ONLY change:
  USA Barracks — remove progression Prerequisites / Science gates on
  units ALREADY present in AmericaBarracksCommandSet.

NO CommandSet merging.
NO alternate-set button imports.
NO other factions/buildings modified.

Purpose: isolate whether safe gate-stripping alone is match-stable.
RUNTIME_TEST_REQUIRED = YES
