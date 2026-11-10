SPECTER USA Patriot PAC-3 — ABM saturation fix
=============================================

Baseline: specter-usa-patriot-abm-startup-crash-fix-test (healthy, BM intercept works).
PAC-3 v1–v8 is not used. Crash-fix ClientUpdate End is kept.

Install
-------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace only:
     _SPEC_DATA_ONE.big
3. Do not replace _SPEC_ART_TWO.big or _SPEC_ART_ONE.big.
   Loose Data\INI is not in this ZIP.

What changed
------------
Patriot-only AI/weapon timing in USAPAC3.ini so a battery can cycle
ballistic targets faster and stop emptying ClipSize=8 on the first few
missiles. Damage/warhead, PRIMARY AA, Donor Guard/Draw/FIREPOINT,
US_THAAD, Weapon.ini unchanged.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
Do not treat 10/10 intercept as guaranteed. ZH still has one victim
per launcher and findClosestEnemy pile-on.
