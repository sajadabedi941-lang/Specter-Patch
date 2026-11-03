USAPAC3 CommandSet load-path fix
================================

Release 748 hid every USAPAC3 unit button because the unique CommandSets
were only in packed CommandSet_USAPAC3.ini. Zero Hour ControlBar reads
loose Data\INI\CommandSet.ini (Launch_Specter copies that file). Live
THAAD menus are in CommandSet.ini as S400ECommandSet*. This package
registers USAPAC3CommandSet / _AA / _ABM / _Deployed in that same file.

Object: USAPAC3
Cost / time: 3876 / 18.6 s
Built from: America Command Center slot 6
Science / Rank / Upgrade / Prerequisite: none

Initial bar: MultiTarget (still disabled), Anti Air, Anti Missile, Stop.
After AA/ABM: Deploy. After deploy: Pack.

Appearance is still live THAAD Draw (US_M1120). New Donor art is not
included. Shared THAAD files were not rewritten.

INSTALL
-------
1. Close Generals / Specter.
2. Extract this ZIP next to generals.exe (or next to Launch_Specter.bat).
   CommandSet.ini must sit next to Launch_Specter.bat AND in Data\INI.
3. Do not replace canonical _SPEC_ART_ONE.big.
4. ART TWO is unchanged from specter-usapac3-base-thaad; keep the copy
   you already have, or download:
   https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-usapac3-base-thaad/_SPEC_ART_TWO.big
5. Run Launch_Specter.bat so it recopies the new CommandSet.ini.
6. America Command Center slot 6 builds USAPAC3.

This package replaces _SPEC_DATA_ONE.big and Data\INI\CommandSet.ini.
CommandButton.ini is unchanged from Release 748. Previous GitHub
Releases are not deleted. Release 748 remains downloadable.

Zero Hour was not run in the build environment. In-game buttons are not
verified here. Static CommandSet/CommandButton validation only.
