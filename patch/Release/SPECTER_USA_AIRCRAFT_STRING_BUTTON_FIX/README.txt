SPECTER - USA AIRCRAFT STRING / BUTTON FIX
=========================================
Does NOT remove USA aircraft.

Root causes addressed:
1) String Manager init — broken English text overlays
2) Match enter crash — CommandSet_USA slots pointed at missing Patch_America_* objects

Fixes:
- ASCII USA OBJECT:/CONTROLBAR: string overlays (heavies + fighters + heliborne)
- Aircraft_USA_AAB_Fighters.ini restores F22/F35/F16/F15/A10/B21/etc without
  re-importing multi-faction Aircraft_AAB_Global (which redefined E-3/B-2)
- Soft strip: only bad English dumps + CommandSet_AdvancedAirBase.ini
  (442 unresolved multi-faction button refs)
- USA Airforce / ScienceObjects / heliborne INIs kept

Kept: B-2, B-1B, B-52, E-3, C-17, KC-135, AC-130, AssaultHelo, AH-64/UH-60/CH-47
CommandSet.ini untouched. AAB Draw/Geometry untouched.
