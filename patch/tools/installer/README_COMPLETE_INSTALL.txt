SPECTER Complete Install — Spain display + country supply income
================================================================

This package is a full drop-in set of SPECTER BIG archives for Command &
Conquer Generals Zero Hour. Copy every BIG in this ZIP into the same folder
as generals.exe (the game root). Do not put them inside Data\ or Art\.
Do not rename the files.

Required files (all five, at the ZIP root)
------------------------------------------
  0_SPECTER_CountrySupplyIncome.big
  0_SPECTER_NatoSpainDisplay.big
  _SPEC_ART_ONE.big
  _SPEC_ART_TWO.big
  _SPEC_DATA_ONE.big

Backup first
------------
Back up your current game folder, especially any existing
_SPEC_*.big and 0_SPECTER_*.big files, before replacing them.

You still need a working Zero Hour / SPECTER install that already has
generals.exe plus the stock archives that ship with the game
(INIZH.big, AudioZH.big, and so on). This ZIP does not replace those.

Load order (Zero Hour, overwrite=FALSE, first registered path wins)
-------------------------------------------------------------------
  0_SPECTER_CountrySupplyIncome.big
  0_SPECTER_NatoSpainDisplay.big
  INIZH.big                          (already in the game folder)
  _SPEC_ART_ONE.big
  _SPEC_ART_TWO.big
  _SPEC_DATA_ONE.big

The 0_ prefix is required so these overlays load before INIZH and the
SPEC archives.

What this package contains
--------------------------
- Official SPECTER SPEC ART and DATA archives (unchanged hashes).
- Spain / Spanish Armed Forces display-name and flag overlay (NATO side).
- Country-specific supply dump income for 25 playable countries.
  Engine formula: cash = MaxBoxes * ValuePerSupplyBox (25).
  Map supply piles keep their previous dollar totals by tripling
  StartingBoxes. Unique workers keep $75 trips (MaxBoxes 1 -> 3).

Validation
----------
Supply income passed static validation (INI/BIG parse and hash checks).
In-game Zero Hour runtime testing has not been performed.

نصب کوتاه
---------
هر پنج فایل BIG را کنار generals.exe بگذارید. قبل از جایگزینی از پوشه
بازی پشتیبان بگیرید. نام فایل‌ها را عوض نکنید.
