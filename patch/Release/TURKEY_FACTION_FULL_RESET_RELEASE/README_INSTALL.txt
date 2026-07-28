SPECTER — Turkey Faction Full Reset Release
===========================================
Tag: specter-turkey-faction-full-reset
Build: 20260728
BIG: _SPECTER_TURKEY_FACTION_FULL_RESET.big
SHA256: 8365346d97e20778b51a9299a82826e687e3bac4c382fcb9aa8a4013ea71beeb
Entries: 172

WHAT THIS IS
------------
Post-PR #207 release overlay for the Turkey faction full reset.
Loads AFTER Data\_SPEC_DATA_ONE.big and overrides Turkey paths only.
Does NOT replace Art\_SPEC_ART_ONE.big.

INSTALL
-------
1. Close Command & Conquer Generals Zero Hour / Specter.
2. Backup your current Data folder (optional but recommended).
3. Copy this file into your game Data folder:
     _SPECTER_TURKEY_FACTION_FULL_RESET.big
   Example:
     ...\Command and Conquer Generals Zero Hour\Data\_SPECTER_TURKEY_FACTION_FULL_RESET.big
4. Keep existing:
     Data\_SPEC_DATA_ONE.big
     Art\_SPEC_ART_ONE.big
5. Launch Specter and start a Skirmish with Turkey.

Optional merge into _SPEC_DATA_ONE.big (advanced):
  python3 patch/tools/big/merge_patch_into_spec_big.py \
    --data-big /path/_SPEC_DATA_ONE.big \
    --art-big /path/_SPEC_ART_ONE.big \
    --patch-root patch \
    --out-dir patch/Release/SPECTER_BIG_MERGE

INCLUDED TURKEY CONTENT
-----------------------
- All Turkey Armed Forces INI under Data\INI\Object\Specter\Turkey Armed Forces\
- Turkey_WeaponObjects.ini cleared (0 custom weapon Objects)
- Rebuilt aircraft:
    Turkey_F16Block70, Turkey_F16V (+ variants)
    Turkey_TB2, Turkey_Akinci, Turkey_Kizilelma
    Turkey_Tu-22M3, Turkey_Tu-22M3_AI
- Weapon_Turkey*.ini aliases to existing USA/China/Russia projectiles
- CommandButton_Turkey.ini / CommandSet_Turkey.ini / Upgrade / Science / SpecialPower / OCL

SKIRMISH CHECK
--------------
1. Skirmish → Turkey vs USA on a small map
2. Confirm load reaches match (no EXCEPTION_ACCESS_VIOLATION)
3. Build Advanced Air Base / Airfield
4. Queue: F-16 Block70, F-16V, TB2, Akinci, Kizilelma, Tu-22M3
5. Confirm units spawn and fire without crash

VERIFY
------
See TURKEY_FILE_VERIFY.txt and VALIDATION_REPORT.txt in this ZIP.
