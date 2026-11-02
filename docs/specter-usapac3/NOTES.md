# USAPAC3 — Patriot PAC-3 battery (THAAD gameplay)

Zero Hour was not run. In-game Command Center clicks were not tested.

## Baseline (before)

`America_MilitaryHQ` → `America_MilitaryHQCommandSet` (only defined in `CommandSet_FactionExpansion_Armies.ini` on `main`):

| Slot | Command |
|---|---|
| 1 | Tomahawk TEL |
| 2 | PrSM TEL |
| 3 | C-RAM |
| 4 | America_AD_Patriot |
| 5 | America_AD_THAAD |
| **6** | **America_AD_NASAMS** |
| 7 | Hawk |
| 8 | RQ-180 |
| 9 | MQ-9 |
| 10 | ARRW TEL |
| 11 | PGS TEL |
| 12 | empty |
| 13 | Rally |
| 14 | Sell |

Slot 6 was occupied. NASAMS was **not** deleted. It was moved to empty slot 12. Slots 1–5, 7–11, 13–14 unchanged. Patriot and THAAD objects were not edited.

## Art (New Donor only)

From `00PMBeta993.big` / `00PMBeta999.big` in `New donor.part001.rar` (`New folder/…`):

- Models: `UsaPac3Car`, `UsaPac3Car_d`, `UsaPac3Car_w`, `UsaPac3F`, `UsaPac3F_d`, `pac3mis_m`
- Textures: `usaPAC3TRUCKmap(.dds)`, `ampac3map*`, `ABNPatriot02`, `pac3missilemap`, `USAPAC3.tga`, `USAPAC3TB.tga`

Housecolor `CWCusHC_B` was **not** wired: `CWCusHousecolor.tga` is missing from the donor BIGs.

No New Donor DATA/INI gameplay was copied.

## Gameplay (SPECTER THAAD)

Cloned from live HQ unit `America_AD_THAAD` / `America_Weapon_THAAD` / `America_Projectile_THAAD`:

- Cost 3876 / time 18.6s / SCIENCE_Rank3
- AttackRange 800, WeaponSpeed 1500, ClipSize 2, Delay 1500, damage 850
- DeployStyleAIUpdate + Generic8x8Locomotor
- Independent names: `USAPAC3`, `USAPAC3_Weapon`, `USAPAC3_Projectile`, `USAPAC3CommandSet*`

`America_Weapon_THAAD` has no `AntiBallisticMissile` line. `USAPAC3_Weapon` sets `AntiBallisticMissile = Yes` so the unit can engage ballistic missiles as requested. Overlay THAAD itself was not changed.

## Slot 6

Last-wins `CommandSet_ZZZZ_USAPAC3.ini`:

- Slot **6** = `Command_ConstructUSAPAC3`
- Slot **12** = `Command_ConstructAmerica_AD_NASAMS` (relocated)

## BIG

`_SPECTER_USAPAC3.big` — place in game Data with other SPECTER BIGs. Filename loads after `_SPEC_DATA_ONE.big` and `_SPECTER_PATCH_FINAL.big`.
