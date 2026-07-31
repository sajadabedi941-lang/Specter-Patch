SPECTER_USA_AAB_FINAL_FIX
=========================
Final USA-only playable repair for Advanced Air Base + USA aircraft.

Problems fixed:
1) String Manager failed to initialize / corrupted text
   - Single deduplicated ASCII USA string overlay (OBJECT:/CONTROLBAR:)
   - Removed duplicate AdvancedAirBase/AWACS string files
2) Crash entering USA match / broken aircraft buttons
   - Restored missing Patch_America_* objects for CommandSet buttons
   - Removed unresolved multi-faction CommandSet_AdvancedAirBase
   - America-only AirForceExpansion (no Russia/China/France/etc aircraft)

KEEP all USA content:
- America AdvancedAirBase
- B-2, B-1B, B-52, E-3 AWACS, C-17, KC-135, AC-130
- USA heliborne (AssaultHelo, AH-64, UH-60, CH-47)
- USA AAB fighters / support

NOT included: any new factions. CommandSet.ini untouched.
