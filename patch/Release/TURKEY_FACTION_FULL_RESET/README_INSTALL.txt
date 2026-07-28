SPECTER — Turkey Faction Full Reset
===================================

Install (overlay):
  1. Keep original Data\_SPEC_DATA_ONE.big and Art\_SPEC_ART_ONE.big.
  2. Copy _SPECTER_TURKEY_FACTION_FULL_RESET.big into the game Data\ folder
     (loads after _SPEC_DATA_ONE.big and overrides Turkey paths).
  3. Or merge this overlay into _SPEC_DATA_ONE.big with:
       python3 patch/tools/big/merge_patch_into_spec_big.py \
         --data-big /path/_SPEC_DATA_ONE.big \
         --art-big /path/_SPEC_ART_ONE.big \
         --patch-root patch \
         --out-dir patch/Release/SPECTER_BIG_MERGE

What changed:
  - Backup: patch/Release/TURKEY_FACTION_FULL_RESET_BACKUP/
  - Removed all Turkey_WeaponObjects + Projectiles custom Objects (no new weapon Objects).
  - Rebuilt aircraft from validated donors, Turkey names preserved:
      Turkey_F16Block70 / Turkey_F16V  <- Britain USA F-16D art + USA F-16 weapons
      Turkey_TB2 / Turkey_Akinci / Turkey_Kizilelma <- Japan_MQ9 (CHI_CH5 + USA MQ-9 weapons)
      Turkey_Tu-22M3 / _AI <- Patch_Russia_Tu22M3 + Russia_Weapon_Kh32_Tu22M3
  - Retargeted remaining Turkey unit weapon slots to USA/China/Russia stock weapons.
  - Weapon_Turkey*.ini rewritten as safe aliases to existing FactionExpansion projectiles.

Skirmish test checklist:
  1. Launch Zero Hour with Specter + this overlay.
  2. Skirmish -> pick Turkey vs USA on any small map.
  3. Confirm load reaches match (no EXCEPTION_ACCESS_VIOLATION).
  4. Build Advanced Air Base / Airfield and queue:
       F-16 Block70, F-16V, TB2, Akinci, Kizilelma, Tu-22M3
  5. Confirm units spawn and fire without crash.

Validation:
  python3 patch/tools/turkey_faction_validate.py
  See VALIDATION_REPORT.txt (PASS).
