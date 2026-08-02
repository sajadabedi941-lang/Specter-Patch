SPECTER B-2 COMPLETE PORT
=========================

File: ZZZZZZ_SPECTER_B2_COMPLETE_PORT.big

WHAT THIS IS
- Complete playable B-2 Spirit (Patch_America_B2)
- Full Object INI (weapons, AI/JetAIUpdate, locomotor, death FX, PDL, countermeasures, upgrades)
- Art: AVB3bmbr W3D models + AVB2A TGA textures + stock avb3bmbr DDS + MK-84 + countermeasure flare
- Data: weapons, FXLists, OCLs, particle systems, armor, upgrades, AudioEvents, CommandButton

AAB CONNECTION (B-2 ONLY)
- America_AdvancedAirBase -> America_AdvancedAirBaseCommandSet slot -> Command_ConstructPatch_America_B2 -> Patch_America_B2
- Advanced Air Base design is NOT changed by this BIG
- Runway requirement remains enabled (NeedsRunway = Yes)
- Other AAB aircraft are unchanged (this BIG does not rewrite the AAB CommandSet)

INSTALL
1. Copy ZZZZZZ_SPECTER_B2_COMPLETE_PORT.big into your Generals Zero Hour / Specter Patch folder
   (same place as your other .big patch files).
2. Load it as the LAST patch file (the ZZZZZZ_ prefix sorts last alphabetically).
3. Keep your existing Specter / Advanced Air Base patch loaded underneath this file.
4. Start a USA game, build America Advanced Air Base (+ heavy runway as required),
   then build B-2 from the AAB production buttons.

NOTES
- Voice AudioEvents are included and reference stock ZH Aurora/Raptor voice stems
  (vaur*, gradio*, etc.). Those WAV files ship with base Generals Zero Hour English audio.
- Ambient / afterburner support WAVs included when available in donor archives.
