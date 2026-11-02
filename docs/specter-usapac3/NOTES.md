# USAPAC3 load-path fix

Zero Hour was not run. In-game Command Center clicks were not tested.

## Diagnosis

The overlay BIG format was valid (same BIGF layout as `_SPECTER_PATCH_FINAL.big`).
The unit did not appear because it was **not applied on the live CommandSet path**.

1. **Wrong install target / launcher skip**
   `Launch_Specter.bat` only copied `_SPEC_DATA_ONE.big` and `_SPEC_ART_ONE.big`
   into the folder next to `generals.exe`. `_SPECTER_USAPAC3.big` was never copied.
   Zero Hour loads `*.big` next to `generals.exe`, not from `Data\`.

2. **CommandSet override used a new filename**
   Live America HQ set lives at `Data\INI\CommandSet_FactionExpansion_Armies.ini`
   inside the working SPECTER overlay BIG. The sidecar only added
   `CommandSet_ZZZZ_USAPAC3.ini`. A second `CommandSet America_MilitaryHQCommandSet`
   in a later file is not a same-path archive override, so HQ slot 6 stayed NASAMS.

Not the cause: BIG header, Art\W3D paths, or THAAD/Patriot object files.

## Fix (load only)

- Sidecar now packs the **same path** `Data\INI\CommandSet_FactionExpansion_Armies.ini`
  with America slot 6 = USAPAC3 and NASAMS moved to empty slot 12.
  Other-country CommandSets in that file are unchanged.
- `Launch_Specter.bat` / `Install_SpecterPatch.bat` copy every `_SPECTER_*.big`
  next to the launcher into the game folder.
- Install: put `_SPECTER_USAPAC3.big` next to `generals.exe`, not in `Data\`.

## Unchanged

America_AD_THAAD, America_AD_Patriot, America_AD_NASAMS objects, other countries.
