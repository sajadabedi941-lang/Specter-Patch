USAPAC3 independent functional stage 1
======================================

CommandSet, Deploy OCL, CombatMode, and FireControlSystem are now
USAPAC3-only. Appearance is still live THAAD Draw (US_M1120). New Donor
art is not included.

Object: USAPAC3
Cost / time: 3876 / 18.6 s
Built from: America Command Center slot 6
Science / Rank / Upgrade / Prerequisite: none

Independent names
-----------------
CommandSet: USAPAC3CommandSet, _AA, _ABM, _Deployed
OCL: OCL_USAPAC3_Deployed, OCL_USAPAC3_Deployed_ABM, OCL_USAPAC3_Pack
Objects: USAPAC3_CombatMode, USAPAC3_FireControlSystem,
         USAPAC3_FireControlSystem_ABM

Shared THAAD files were not rewritten: US_M1120.ini, S400ECommandSet,
OCL_THAAD_*, S400R_Deploy, Weapon.ini, ART ONE, ART TWO.

INSTALL
-------
1. Close Generals / Specter.
2. Extract this ZIP next to generals.exe (or next to Launch_Specter.bat).
3. Do not replace canonical _SPEC_ART_ONE.big.
4. ART TWO is unchanged from specter-usapac3-base-thaad; keep the copy
   you already have, or download:
   https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-usapac3-base-thaad/_SPEC_ART_TWO.big
5. Run Launch_Specter.bat.
6. America Command Center slot 6 builds USAPAC3.

This package replaces _SPEC_DATA_ONE.big and the loose Data\INI\CommandSet.ini
+ CommandButton.ini (those two INI files are byte-identical to stage 1;
only DATA changed). Previous GitHub Releases are not deleted.

Zero Hour was not run in the build environment. In-game Deploy is not
verified here. Static validation only.
