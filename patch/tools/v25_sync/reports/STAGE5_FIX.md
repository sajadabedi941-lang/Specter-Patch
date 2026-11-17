# Stage 5 INI fix report

- Generated: 2026-11-11 15:39 Asia/Tehran
- Original SPECTER BIGs unchanged: **True**
- Loose INI written: **False**
- Generals.exe run: **False**
- Members replaced in experimental DATA only: 3
- Added Silent Death INIs validated: 19 (structure, FXList Ends, no tokens after Object End, Armor refs)

## Replaced members

- `Data\INI\FXList_SilentDeath.ini` — 7 FXList, 7 column-0 End. Names unchanged.
- `Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini` — DEPLOYED ConditionStates inside first W3DTruckDraw; Object ends at column-0 End.
- `Data\INI\Armor_SilentDeath.ini` — one `SD25_ProjectileArmor`; CSSA1 → `SD25_TankArmor`; HQ11 → `SD25_HumveeArmor`.

## Hashes

- Original DATA `7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`
- Original ART TWO `81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf`
- Stage 5 ART TWO (unchanged, not in ZIP) `bce126e0943ca771bcf5a13cf222c5a41a590b10b244ea6812d2a770a62dacd5`
- Fixed DATA `c9d1b6ac805d9d9edd18d643f945bf740b822d88bf07d6e280129aa204f2880c`
- ZIP `SPECTER_V25_STAGE5_INI_FIX.zip` `641618e790d9e2b4ed1a566d19b8006e184e3e1d4cba3c4b7ce756627efaf773`
