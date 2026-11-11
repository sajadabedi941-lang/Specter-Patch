# Stage 5 INI fix — FXList End, HQ11 DEPLOYED, duplicate Armor

Fixes only the three diagnosed parse errors in the experimental Stage 5 DATA BIG. Stage 6 is not started. Original SPECTER FINAL is never opened for write. No loose INI.

Generals.exe was **not** run.

## What changed inside `_SPEC_DATA_ONE.big`

| Path | Fix |
|---|---|
| `Data\INI\FXList_SilentDeath.ini` | Each of 7 `FXList` blocks now has nested `End` plus a column-0 `End` (SPECTER `FXList.ini` pattern). Names and effect bodies unchanged. |
| `Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini` | `DEPLOYED` ConditionState groups sit inside `W3DTruckDraw` (full RIDER2 visuals copied as DEPLOYED). Nothing after Object `End`. Pack/deploy via `DeployStyleAIUpdate` + `WeaponSet Conditions = DEPLOYED` kept. |
| `Data\INI\Armor_SilentDeath.ini` | Duplicate `Armor SD25_ProjectileArmor` removed. Remaining: `SD25_ProjectileArmor`, `SD25_TankArmor`, `SD25_HumveeArmor`, `SD25_InvulnerableAllArmor`. CSSA1 still uses `SD25_TankArmor`; HQ11 still uses `SD25_HumveeArmor`. |

ART TWO is unchanged (`bce126e0…`) and is not in this ZIP. SPECTER public Armor/FXList INIs are not touched.

## Hashes (Asia/Tehran)

Original SPECTER (untouched):

- `_SPEC_DATA_ONE.big` `7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`
- `_SPEC_ART_TWO.big` `81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf`

Fixed experimental DATA:

- `_SPEC_DATA_ONE.big` `c9d1b6ac805d9d9edd18d643f945bf740b822d88bf07d6e280129aa204f2880c`

ZIP:

- `SPECTER_V25_STAGE5_INI_FIX.zip` `641618e790d9e2b4ed1a566d19b8006e184e3e1d4cba3c4b7ce756627efaf773`
- Contents: complete corrected `_SPEC_DATA_ONE.big`, `INSTALL.txt`, `REVERT.txt`, `SHA256SUMS.txt`
