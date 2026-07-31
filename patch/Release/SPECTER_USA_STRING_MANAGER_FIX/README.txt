SPECTER - USA STRING MANAGER FIX (USA ONLY)
==========================================
Fixes FATAL: String Manager failed to initialize properly.

Cause:
- UTF-8 / multi-faction English *.txt overlays (STRINGS_TO_ADD, FactionFramework, etc.)
- Missing OBJECT:/CONTROLBAR: strings for USA heavy runway aircraft (E-3, B-2, B-1, B-52, ...)

Fix:
- ASCII-only AdvancedAirBase / AdvancedAWACS / USA_HeavyAircraft string overlays
- Strip non-USA English string dumps from USA DATA packs
- America-only AdvancedAirBase aircraft CommandButtons
- Add DisplayName/TextLabel strings for USA heavies + AWACS + AAB

Preserved:
- General Star B-2 AAB runway fix
- E-3 parse fix (no ArmorSetFlag)
- CommandSet.ini untouched
- AdvancedAirBase Draw/Geometry untouched
