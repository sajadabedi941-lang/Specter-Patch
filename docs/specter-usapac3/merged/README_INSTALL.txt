USAPAC3 — spawn isolate stage 2 (empty DEPLOYED animation)
==========================================================

After specter-usapac3-spawnfix the game still crashed when construction
finished. Attach-on-UsaPac3Car_w was not the cause.

Packed USAPAC3 still named Animation = UsaPac3F.UsaPac3F at object create.
UsaPac3F.W3D had a 101-frame animation header and zero channels. Live
US_THAAD deployed model US_M1120_A has no animation blob at all.

This package:
- keeps the approved UsaPac3F model on DEPLOYED
- removes that empty Animation= from Draw
- strips the empty ANIMATION chunk from UsaPac3F / UsaPac3F_d
- does not change slot 6, cost 3876, time 18.6, weapons, THAAD/Patriot/NASAMS

INSTALL
-------
1. Close Generals / Specter.
2. Extract the ZIP next to Launch_Specter.bat.
3. Do not replace canonical _SPEC_ART_ONE.big (2,145,283,309 bytes).
4. Run Launch_Specter.bat.

ART ONE:
https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

Zero Hour was not run here; spawn crash is not verified in-game in this environment.
