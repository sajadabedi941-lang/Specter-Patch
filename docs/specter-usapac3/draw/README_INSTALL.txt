USAPAC3 appearance stage (PAC-3 TEL Draw)
=========================================

Object USAPAC3 and USAPAC3_CombatMode now use archive PAC-3 meshes
(UsaPac3Car packed, UsaPac3F deployed). Gameplay, CommandSets, weapons,
OCL, Deploy/Pack, and FireControlSystem are unchanged from
specter-usapac3-commandset-fix.

UsaPac3Car_w is not used. In-flight missiles still use the existing THAAD
projectile art; pac3mis_m is stored in ART TWO but not wired to weapons.

INSTALL
-------
1. Close Generals / Specter.
2. Extract this ZIP next to generals.exe (or next to Launch_Specter.bat).
3. Replace _SPEC_DATA_ONE.big AND _SPEC_ART_TWO.big.
4. Do not replace canonical _SPEC_ART_ONE.big.
5. CommandSet.ini must sit next to Launch_Specter.bat (same file as
   specter-usapac3-commandset-fix).
6. Run Launch_Specter.bat.

This package replaces DATA and ART TWO. Previous GitHub Releases are not
deleted. Release specter-usapac3-commandset-fix remains downloadable.

Zero Hour was not run in the build environment for this Draw attach.
In-game look is not verified here. Static validation only.
