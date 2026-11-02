USAPAC3 — EXPERIMENT B (diagnostic Draw, not final art)
=======================================================

This ZIP is a controlled A/B test. It is NOT the approved PAC-3 look.
SPAWNFIX / SPAWNFIX2 / SPAWNFIX3 are unchanged on GitHub. The original
USAPAC3.ini in the repo is unchanged.

Experiment A (control): New Donor UsaPac3Car + UsaPac3F
  Release: specter-usapac3-spawnfix3

Experiment B (this ZIP): same Object, weapon, cost 3876, time 18.6,
locomotor, Command Center slot 6. Draw uses live SPECTER US_M1120 /
US_M1120_A (Object US_THAAD). No UsaPac3F or UsaPac3Car on the spawn path.

INSTALL
-------
1. Close Generals / Specter.
2. Extract next to generals.exe.
3. Do not replace canonical _SPEC_ART_ONE.big.
4. Run Launch_Specter.bat.
5. Build USAPAC3 from America Command Center slot 6.

To restore experiment A, reinstall SPECTER_USAPAC3_SPAWNFIX3.zip.

Zero Hour was not run here. This release does not claim the crash is fixed.

If B still crashes: the New Donor model is not the proven cause; next
isolate Object modules.

If B spawns: the crash is in UsaPac3Car / UsaPac3F Draw. Do not keep B
as the final appearance.
