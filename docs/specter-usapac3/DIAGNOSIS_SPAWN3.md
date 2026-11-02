# USAPAC3 spawn crash — isolation stage 2 (empty DEPLOYED animation)

Zero Hour was **not** run in this environment. In-game crash at construction
finish is the user's report after `specter-usapac3-spawnfix`. The attach-on-
`UsaPac3Car_w` change is treated as disproven, not as the cause.

## Packed winner (before this stage, live DATA sha `e9185998…`)

| Name | Packed path | Count |
|---|---|---:|
| `Object USAPAC3` | `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini` | 1 |
| `Weapon USAPAC3_Weapon` | `Data\INI\Weapon_USAPAC3.ini` | 1 |
| `Object USAPAC3_Projectile` | `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3_Projectile.ini` | 1 |
| `CommandSet USAPAC3CommandSet` | `Data\INI\CommandSet_ZZZZ_USAPAC3.ini` | 1 |

Overlay bytes did **not** match packed bytes until this stage (DEPLOYED
`Animation =` still present in the BIG). Packed winner is that unique path.

Live comparison vehicles in the **same** DATA BIG:

- `Object US_THAAD` (`US_M1120.ini`) — spawnable American TEL, `W3DTruckDraw`
- `Object AmericaMobileSamSiteMIM104F` (`MIM104F.ini`) — Patriot truck, Model-only
- `Irq_Fahad3` / `Irq_Fahad3_A` — other spawnable TELs using the same Draw pattern

`Object America_AD_THAAD` is **not** in packed DATA.

## Isolation stages (reversible)

| Stage | Change | Result |
|---|---|---|
| 0 | `AttachToBone` on `UsaPac3Car_w` removed (`spawnfix`) | User: still crashes |
| 1 | Second Draw removed; flags copied from `US_THAAD` (`spawnfix2`) | Packed INI **still** named `UsaPac3F.UsaPac3F` |
| 2 | **This release** | Empty F animation removed from Draw **and** from the W3D |

Each stage only edits `USAPAC3.ini` and/or `UsaPac3F.W3D` / `UsaPac3F_d.W3D`.
Original F W3Ds: `docs/specter-usapac3/backup/w3d_empty_anim/`.

## Module-by-module vs live `US_THAAD` (spawn path)

| Item | Live `US_THAAD` (spawns) | Packed `USAPAC3` after stage 1 |
|---|---|---|
| Draw | 1× `W3DTruckDraw` | 1× `W3DTruckDraw` |
| Default model + anim | `US_M1120` + 7 real channels | `UsaPac3Car` + 2 real Z channels |
| Default flags | `ONCE_BACKWARDS` + `START_FRAME_FIRST` | same |
| DEPLOYED model | `US_M1120_A` | `UsaPac3F` |
| DEPLOYED W3D anim blob | **none** (no `0x200` chunk) | **101-frame header, 0 channels** |
| DEPLOYED `Animation =` | names missing clip (engine skips) | names **present empty** clip (engine evaluates) |
| Turret / launch bones / second Draw / PRISTINE | none | none (removed in stage 1) |
| Body / Physics / Loco / Geometry | ActiveBody / Mass 400 / `Generic8x8Locomotor` / BOX 45×12×16 | same pattern (health 900) |
| WeaponSet | SECONDARY+TERTIARY | `USAPAC3_Weapon` (exists) |
| Projectile | not created at vehicle spawn | `USAPAC3_Projectile` + `pac3mis_m` (PRELOAD assets only) |
| HLOD / bones | valid | 53 bones, 52 meshes, HLOD bone indices 1–52, no NaN |

`W3DModelDraw` / `W3DTruckDraw` preloads every `ConditionState` Model **and**
every `Animation =` when the object is created. Construction-finish is that
create. DEPLOYED is therefore on the spawn path even if the unit appears packed.

## W3D evidence (ART TWO)

| File | Mesh ver | Anim frames | Channels | Used at spawn |
|---|---|---:|---:|---|
| `US_M1120.W3D` | 0x50000 | 151 | 7 real | yes (live TEL) |
| `US_M1120_A.W3D` | 0x50000 | **none** | 0 | yes (live deployed) |
| `Irq_Fahad3.W3D` | 0x50000 | 202 | 16 real | yes (other TEL) |
| `Irq_Fahad3_A.W3D` | 0x50000 | **none** | 0 | yes |
| `UsaPac3Car.W3D` | 0x40002 | 101 | 2 Z, frames 1–100 | default state |
| `UsaPac3F.W3D` (before) | 0x40002 | **101** | **0** | DEPLOYED preload |
| `UsaPac3F.W3D` (after) | 0x40002 | **none** | 0 | DEPLOYED model only |
| `UsaPac3Car_w.W3D` | 0x40002 | 101 empty | 0 | **not** in current Draw |

Mesh 0x40002 is not unique (137 ART TWO files). HLOD of F/Car is valid.
`UsaPac3Car` is a complete TEL (CORE, TIRE01–08, TURRET01, FIREPOINT01–04).
`UsaPac3Car_w` is a 3-bone axle fragment; it is not referenced after stage 0.

## Not the cause (present on live spawnable TELs, or unused at create)

`Generic8x8Locomotor` (`HasSuspension = Yes`), SECONDARY/TERTIARY weapon,
`CAN_ATTACK`, `DeployStyleAIUpdate` without `Turret{}`, Geometry 45×12×16,
`ProductionUpdate`, CommandSet buttons (`Command_ADS_MTS_SWITCH` etc. exist),
cost 3876 / time 18.6, America CC slot 6, death OCL/FX, `Engine01` on the
projectile, `Upgrade_America_Armor` (TriggeredBy only; mask 0 does not create
the drawable).

## Cause (evidence)

The remaining spawn-time difference vs every healthy deployed TEL in this BIG
is **not** Object / Physics / Geometry / Locomotor / Weapon. It is Draw
animation:

`Animation = UsaPac3F.UsaPac3F` refers to a **present** 101-frame clip with
**zero channels**. Live `US_M1120_A` / `Irq_Fahad3_A` have **no** animation
blob, so the same INI pattern is a skipped lookup, not a motion eval.

Stage 0 never touched that clip. Stage 1 still named it on DEPLOYED. That
matches the failed in-game test of `specter-usapac3-spawnfix`.

## Fix (stage 2 only)

- Keep `UsaPac3F` / `UsaPac3F_d` as **Model** for DEPLOYED (approved look).
- Do not set `Animation =` on those states.
- Strip the empty `ANIMATION` chunk from `UsaPac3F.W3D` and `UsaPac3F_d.W3D`
  so they match `US_M1120_A` (hierarchy + meshes + HLOD, no anim blob).
- Keep Car pack/unpack clips (real channels) and `US_THAAD` flags.
- No CommandSet / slot 6 / cost / weapon / THAAD / Patriot / NASAMS changes.

If this still crashes in-game, the next **reversible** isolate is to stop
loading `UsaPac3F` at create (DEPLOYED would reuse Car). That would change
deployed appearance and must be reported before it is applied.

INGAME_ZH: not executed.
