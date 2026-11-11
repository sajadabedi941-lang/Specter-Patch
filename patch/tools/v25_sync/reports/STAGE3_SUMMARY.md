# Stage 3 — nested ART recovery and CWC rebuild plans

- Generated: 2026-11-11 13:31 Asia/Tehran
- Game writes: **False**
- Generals.exe run: **False**
- Nested BIGs indexed: 9 (`WYS/Textures.big`, `WYS/W3D.big`, `WYS/Window.big`, `TexturesZH.big`, `W3DZH.big`, `W3DEnglishZH.big`, `WindowZH.big`, `TerrainZH.big`, `WYS/Terrain.big`)
- ART stems (exact, no substitutes): **22415**

## Sample equipment

| Object | DATA | ART | Resolver readiness | CWC |
|---|---|---|---|---|
| `ChinaCSSA1` | `MANUAL_REBUILD` | `AUTO_RECOVERABLE` | `manual_rebuild` | none |
| `ChinaHQ11` | `MANUAL_REBUILD` | `AUTO_RECOVERABLE` | `manual_rebuild` | RiderChangeContain, OCLSpecialPower, EnemyNearUpdate, FireWeaponUpdate |

DATA stays `MANUAL_REBUILD` because stock-ZH FX/crate names (`TankDamageFX`, `SalvageCrateData`, `TruckDamageFX`) are not in the V25 zip or the SPECTER overlay, and because HQ11 still needs an independent pack/unpack rebuild (`RiderChangeContain` is CWC.exe-only). Those gaps are not filled with look-alike files.

ART is `AUTO_RECOVERABLE`: models, nested-BIG textures (`EXTireTrack`, `NVBtmstr_D1`), and multi-texture W3D chains were found by exact stem.

## What was actually tested vs analysis-only

**Tested (this machine):**

- 29 unit tests: nested BIG writer/index, texture inside nested BIG, multi-texture W3D, missing ART (no substitute), CWC inspect, shared ART, MappedImage vs file stem, apply refused, stage-2 resolver regression.
- Live V25 158-volume zip: ArtIndex of 9 nested BIGs (22415 stems). `ChinaCSSA1` and `ChinaHQ11` plans regenerated with W3D texture walk.
- `apply` refused.
- SPECTER `_SPEC_DATA_ONE.big` / `_SPEC_ART_TWO.big` SHA256 unchanged.

**Analysis / planning only (not in-game):**

- SPECTER-safe rebuild of `RiderChangeContain` via `DeployStyleAIUpdate` + `DEPLOYED` ConditionState.
- Whether stock ZH `TankDamageFX` / `SalvageCrateData` exist in vanilla Generals (not in SPECTER overlay).
- Generals.exe was **not** run. No Object was imported.

## Status values

`READY_FOR_TRANSFER_PLAN` | `AUTO_RECOVERABLE` | `MANUAL_REBUILD` | `BLOCKED`
