SPECTER - USA AIRCRAFT STRING / BUTTON AUDIT FIX
================================================
Keeps ALL USA aircraft INIs (B-2, B-1B, B-52, E-3, C-17, KC-135, AC-130,
heliborne, AAB fighters, ScienceObjects, Airforce folder).

Fixes only:
- ASCII English string overlays (OBJECT: / CONTROLBAR: keys)
- CommandButton TextLabel / DescriptLabel coverage
- CommandSet_USA refs to missing Patch_America_* objects
  (fighters restored via Aircraft_USA_AAB_Fighters.ini without
   re-importing multi-faction Aircraft_AAB_Global that redefined E-3/B-2)

Stripper removes ONLY broken String Manager text dumps and multi-faction
AAB overlays that break runway bones / unresolved CommandSet refs.
Does NOT delete USA aircraft INIs. CommandSet.ini untouched.
