SPECTER Vietnam VL MICA — final Command Center button fix
=========================================================

Baseline: specter-vietnam-vl-mica-command-button-fix still had no button.
This pack installs the CommandSet the game actually uses.

Install (both steps)
--------------------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace:
     _SPEC_DATA_ONE.big
3. Copy/overwrite the loose file at this exact path:
     Data\INI\CommandSet_Vietnam.ini
   Loose Data\INI always beats the same path inside a BIG.
   If that loose file is left as the original SPECTER overlay, the
   packed CommandSet never appears.

Keep _SPEC_ART_TWO.big from specter-vietnam-vl-mica-test.

What you should see
-------------------
Vietnam starting Command Center / MilitaryHQ slot 3 = VL MICA.
Worker, VT72B, IL-76, Rally, Sell, Alhussaien stay in their slots.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
