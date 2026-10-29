SPECTER — remove Arabic Alliance
================================

Arabic Alliance is the playable GLA slot (PlayerTemplate FactionGLA,
display INI:FactionGLA = "Arabic Alliance").

This pack sets:
  PlayableSide = No
  OldFaction   = No

so it is gone from skirmish, multiplayer, and the original-factions
filter. The template is kept so maps/scripts that name FactionGLA do
not crash.

Not deleted: ArabicArmy objects (Egypt's dozer still builds some),
Iraq / Saudi Arabia / UAE / Syria / Libya, CommandSet menus, Shahed
Fire, cost 8000, Vietnam radar, ART, 0_ overlays.

Zero Hour was not run. Static checks are not in-game proof.

Install
-------
1. Close Zero Hour.
2. Unzip REMOVE_ARABIC_ALLIANCE_INSTALL.zip
3. Run Install_RemoveArabicAlliance.bat from the game folder or beside it.
4. Keep 0_SPECTER_GlobalStoreCameos.big and 0_SPECTER_MissileJLMNCameos.big.
5. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

This DATA replaces _SPEC_DATA_ONE.big from vietnam-radar-minimap /
radar-shahed-fire-8000 / specter-unified and still contains those fixes.

SHA-256: see SHA256SUMS.txt.
Loose PlayerTemplate.ini must sit at Data\INI\PlayerTemplate.ini
(LocalFileSystem first-wins over archives).
