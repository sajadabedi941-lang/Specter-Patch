SPECTER_USA_STRING_RUNTIME_FIX
==============================
Exact String Manager runtime failure fix.

FAILING FILE: Data\English\generals.csf
CAUSE: corrupt string markers "RTSW" (should be WRTS/STR) on Turkey labels
       → FATAL: String Manager failed to initialize properly

REPAIR:
1. Replaced generals.csf with known-good CSF (full parse OK)
2. Merged USA AAB/aircraft OBJECT + CONTROLBAR keys into CSF
3. Removed Data\English\*.txt (CSF-only English folder, as in working packs)

NOT REMOVED:
America AdvancedAirBase, B-2, B-1B, B-52, E-3, C-17, KC-135, AC-130, USA heliborne,
USA AAB fighters. CommandSet.ini untouched. No factions added.
