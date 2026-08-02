SPECTER — AAB FIVE-AIRCRAFT FINAL FULL RELEASE
==============================================
(+ Russia 9M317_MissileObject parse crash fix)

ONE ZIP with full replacement Specter BIG archives (NOT a small overlay).

CONTENTS
--------
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  Install_SpecterPatch.bat
  README_INSTALL.txt
  VERIFY_REPORT.txt
  HASHES.txt

ADVANCED AIR BASE
-----------------
  Building: America_AdvancedAirBase
  Scale: 1.60
  Pads: 16

  ONLY these aircraft:
    1. B-2     -> Patch_America_B2
    2. B-21    -> Patch_America_B21
    3. B-52    -> Patch_America_B52
    4. AWACS   -> Patch_America_E3
    5. AN-225  -> Patch_America_AN225

RUSSIA FIX (this rebuild)
-------------------------
  Object 9M317_MissileObject:
    - Removed KindOf PRELOAD (was crashing ZH during russia_weaponobjects.ini parse)
    - Locomotor = SET_NORMAL 9M317MissileLocomotor

INSTALL
-------
1. Close Specter / Generals completely.
2. Unzip SPECTER_AAB_FIVE_AIRCRAFT_FINAL_FULL.zip
3. Run Install_SpecterPatch.bat and enter GameRoot
   OR copy both .big files into GameRoot (replace existing).
4. Launch Specter.

Do NOT install a separate loose patch/Data overlay for this release.
Multiplayer clients must all use the same BIG pair.

CHECKSUMS
---------
  DATA SHA256=27f73129627ef868e580a1ce12ef9196d48e75008a4d27d09c22a1e790a88059
  ART  SHA256=bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
