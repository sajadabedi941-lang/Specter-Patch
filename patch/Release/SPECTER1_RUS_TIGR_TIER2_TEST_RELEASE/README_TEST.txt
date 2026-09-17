README_TEST
===========

This is an unofficial test build for Specter-Patch PR #511
(Final Upgrade_RUS_Tier2 parse crash / Tigr1+Tigr2 plant path).

It is packaged so a Windows Zero Hour install can load the current
patched DATA. It is not a final / official release.

What this DATA changes (already packed; do not edit):
  Upgrade.ini compacted to <=125 unique templates so RUS_Tier2 parses
  inside the 128-bit mask (3 veterancy bits reserved).
  Upgrade_RUS_Tier1 and Upgrade_RUS_Tier2 kept.
  Tigr2 research uses rebuilt Upgrade_Rus_Tigr2 (SU39 vehicle template).
  Tigr1 always buildable; Tigr2 unlocks after that upgrade.
  ART is unchanged. Do not replace _SPEC_ART_ONE.big.

See INSTALL.txt for install steps.
See TIGR_TIER2_FINAL_CRASH_REPORT.txt for crash source / parse result.
See SHA256.txt for hashes of every file in this folder.
