# USAPAC3 A/B spawn experiment

Zero Hour was **not** run in this environment. This package does **not**
claim the crash is fixed. SPAWNFIX / SPAWNFIX2 / SPAWNFIX3 are treated as
failed in-game tests (user report). Previous hypotheses are not assumed.

## Design

| | Experiment A (control) | Experiment B (isolate) |
|---|---|---|
| Object name | `USAPAC3` | `USAPAC3` (same, so slot 6 still builds it) |
| Draw | current New Donor `UsaPac3Car` + `UsaPac3F` | live SPECTER `US_M1120` / `US_M1120_A` from `Object US_THAAD` |
| Cost / time | 3876 / 18.6 | 3876 / 18.6 |
| Weapon / projectile | `USAPAC3_Weapon` / `USAPAC3_Projectile` | same |
| Locomotor | `Generic8x8Locomotor` | same |
| Command Center / slot 6 | unchanged | unchanged |
| THAAD / Patriot / NASAMS | untouched | untouched |
| Appearance | approved PAC-3 look | **diagnostic only** (looks like live THAAD TEL) |

`W3DModelDraw` / `W3DTruckDraw` preloads **every** `ConditionState` Model at
object create. Disabling only `UsaPac3F` while leaving `UsaPac3Car` on Default
would still load a New Donor W3D at spawn. B therefore swaps **all** New Donor
models in Draw so the isolate is “Draw/model vs rest of Object”.

B is not the approved look. Restore A from
`docs/specter-usapac3/abtest/USAPAC3_EXPERIMENT_A.ini` (byte-identical to
`patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini`).

Original spawnfix3 DATA was not overwritten:

`7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`

## Recorded experiment A (control)

Packed winner: `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini` (1).

Draw: 1× `W3DTruckDraw`. Models `UsaPac3Car`, `UsaPac3Car_d`, `UsaPac3F`,
`UsaPac3F_d`. Default animation `UsaPac3Car.UsaPac3Car` `ONCE_BACKWARDS`
`START_FRAME_FIRST`. DEPLOYED is Model-only `UsaPac3F` (empty anim chunk
already stripped in spawnfix3). Tire bones `TIRE01`–`TIRE08`.

Unchanged gameplay: `Weapon SECONDARY+TERTIARY USAPAC3_Weapon`,
`Generic8x8Locomotor`, `ActiveBody` 900, `PhysicsBehavior` Mass 400,
`DeployStyleAIUpdate` Pack/Unpack 6555, Geometry BOX 45×12×16,
`CommandSet USAPAC3CommandSet`, no Science/Prerequisites.

## Experiment B (this ZIP)

Only the Draw block changes. Models `US_M1120`, `US_M1120D`, `US_M1120_A`,
`US_M1120_AD` (already in `_SPEC_ART_TWO.big`). Tire bones `Tire01`–`Tire08`
as on live `US_THAAD`. No `UsaPac3F` / `UsaPac3Car` on any Model/Animation
line.

ART TWO, CommandSet.ini, CommandButton.ini, original overlay INI, and
previous GitHub Releases are unchanged.

## How to read the in-game result

These outcomes are for **you** after installing this ZIP. They are not
results from this environment.

1. **B still crashes at construction finish**  
   Do not blame `UsaPac3F`. The rest of Object (weapon, projectile, locomotor,
   AI, body, physics, geometry, upgrades, CommandSet) is still on the spawn
   path. Next reversible isolate: strip modules one at a time on a copy of B
   (start with `MaxHealthUpgrade` / `Upgrade_America_Armor`, then weapon set,
   then `DeployStyleAIUpdate`). Keep Draw as `US_M1120`.

2. **B finishes construction and the unit exists**  
   Crash is in the New Donor Draw/models (`UsaPac3Car` and/or `UsaPac3F`), not
   the gameplay Object. Next reversible isolates on copies, still not the
   original:
   - B2: Default `UsaPac3Car`, DEPLOYED `US_M1120_A` (F off spawn, Car on)
   - B3: Default `US_M1120`, DEPLOYED `UsaPac3F` (Car off spawn, F on)  
   Whichever of B2/B3 crashes is the failing W3D. Then rebuild/replace that
   file and restore the approved Draw from experiment A.

## Static validation (this environment)

`STATIC_OK`. Packed B object == `USAPAC3_EXPERIMENT_B.ini`. Only that one
path differs from spawnfix3 DATA. Slot 6, cost, time, weapon, locomotor
unchanged. Original overlay still contains `UsaPac3F`.

INGAME_ZH: not executed.  
CRASH_FIXED: not claimed.

## Files

- `USAPAC3_EXPERIMENT_A.ini` — control snapshot (original)
- `USAPAC3_EXPERIMENT_B.ini` — diagnostic Draw
- `_SPEC_DATA_ONE.big` in this ZIP — packed B
- Previous Release `specter-usapac3-spawnfix3` — packed A; not rewritten
