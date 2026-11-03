USAPAC3 stage 1 — base unit cloned from live packed Object US_THAAD
==================================================================

This is NOT the final PAC-3 look. New Donor models are not included.
The unit uses live SPECTER THAAD Draw (US_M1120 / US_M1120_A).

Object: USAPAC3
Cost / time: 3876 / 18.6 s
Built from: AmericaCommandCenter slot 6
Science / Rank / Upgrade / Prerequisite: none
Weapon: USAPAC3_Weapon + USAPAC3_Weapon_ABM (clones of S400R_Deploy / _ABM)
Projectile: none (THAAD deploy weapons have no ProjectileObject)

INSTALL
-------
1. Close Generals / Specter.
2. Extract this ZIP next to generals.exe (or next to Launch_Specter.bat).
3. Do not replace canonical _SPEC_ART_ONE.big (2,145,283,309 bytes).
   Download it from:
   https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big
4. Run Launch_Specter.bat.
5. America Command Center slot 6 builds USAPAC3. It should look like THAAD.

This package replaces _SPEC_DATA_ONE.big, _SPEC_ART_TWO.big, and the loose
Data\INI\CommandSet.ini + CommandButton.ini. Previous GitHub Releases are
not deleted.

Zero Hour was not run in the build environment. In-game spawn is not verified
here. Stage 1 is only successful when the unit actually builds in ZH without
crashing at construction complete.
