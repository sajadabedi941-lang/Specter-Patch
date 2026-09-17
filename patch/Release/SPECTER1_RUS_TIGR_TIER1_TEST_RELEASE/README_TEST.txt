README_TEST
===========

This is an unofficial test build for Specter-Patch PR #511
(Fix Upgrade_RUS_Tier1 parse crash / Tigr1+Tigr2 plant path).

It is packaged so a Windows Zero Hour install can load the current
patched DATA. It is not a final / official release.

Windows validation is still required.
Menu, skirmish, Russia, Tigr1, Tigr2, upgrade apply, and gameplay
have not been signed off on a real Windows generals.exe client.

Current known Wine/Linux failures are environment-related.
Wine 9.0 on Linux hits an init access violation in stock game.dat
(EIP 0x007D1A0F, write 056F0000) with or without this DATA pack.
That crash is not caused by Specter INI/DATA changes in this PR.
Do not treat a Wine crash as a fail of this test ZIP.

What this DATA changes (already packed; do not edit):
  Upgrade.ini left at 128 unique templates (no extra Upgrade_Rus_Tigr2).
  Tigr2 research button uses existing Upgrade_RUS_Tier1.
  Tigr1 always buildable; Tigr2 unlocks after that upgrade.
  ART is unchanged. Do not replace _SPEC_ART_ONE.big.

See INSTALL.txt for install steps.
See SHA256.txt for hashes of every file in this folder.
