USAPAC3 — America Command Center slot 6
=======================================

CAUSE
-----
America's live Command Center is Object AmericaCommandCenter
(CommandSet = AmericaCommandCenterCommandSet in Data\INI\CommandSet.ini).
FactionAmerica starts with that building.

USAPAC3 was previously wired only to America_MilitaryHQCommandSet.
Object America_MilitaryHQ is not in live DATA, so that slot never appears.
_SPECTER_PATCH_FINAL.big being deleted does not change this. ControlBar
first-wins loose Data\INI\CommandSet.ini.

FIX
---
AmericaCommandCenterCommandSet slot 6 = Command_ConstructUSAPAC3.
Slots 1, 12-18 unchanged. THAAD / Patriot / NASAMS / other countries
untouched. Button, object, and ART TWO models were already valid.

INSTALL
-------
1. Close Generals / Specter.
2. Keep canonical _SPEC_ART_ONE.big next to generals.exe
   (2,145,283,309 bytes). Do not replace it with a 524 MB repo zip.
3. Replace / copy next to generals.exe:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
     Launch_Specter.bat
     CommandSet.ini
4. Run Launch_Specter.bat — it copies the BIGs and installs
   CommandSet.ini to Data\INI\CommandSet.ini (ControlBar first-win).
5. Keep _SPECTER_PATCH_FINAL.big and _SPECTER_USAPAC3.big deleted.

ART ONE download (unchanged original):
https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

The construct button is locked until SCIENCE_Rank3 (same as THAAD).
The slot itself is visible on America's Command Center.

ROLLBACK
--------
  ART ONE  15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66
  ART TWO  a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af
  DATA     c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac
