SPECTER Vietnam radar minimap
=============================

Vietnam_RadarStation already granted Upgrade_AmericaRadar but RadarUpgrade
had no TriggeredBy, so the radar map / minimap did not turn on.

The working project pattern (Japan / Iran / Iraq overlay / America) is:

  GrantUpgradeCreate  UpgradeToGrant = Upgrade_AmericaRadar
  RadarUpgrade        TriggeredBy    = Upgrade_AmericaRadar

That TriggeredBy line is now on both Vietnam_RadarStation definitions
(first-win donor file and the later own file). Upgrade name was not invented.

Not changed: radar menus, Shahed_136 Mobile Launcher Fire, cost 8000,
CommandSet.ini, CommandButton.ini, other countries, ART, 0_ overlays.

Zero Hour was not run. Static checks are not in-game proof.

Install
-------
1. Close Zero Hour.
2. Unzip VIETNAM_RADAR_MINIMAP_INSTALL.zip
3. Run Install_VietnamRadarMinimap.bat from the game folder or beside it.
4. Keep 0_SPECTER_GlobalStoreCameos.big and 0_SPECTER_MissileJLMNCameos.big.
5. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

This DATA replaces _SPEC_DATA_ONE.big from radar-shahed-fire-8000 /
specter-unified and still contains those DATA changes.

SHA-256: see SHA256SUMS.txt.
