# AmericaRadarAN/MPQ65 mobile radar

Object `AmericaRadarAN/MPQ65` is now a movable US Patriot fire-control radar. Same W3D, name, side, and radar function. No duplicate Object. PAC-3 launchers, weapons, Iron Dome, and other countries were not changed.

Zero Hour was not run. In-game move/stop was not tested.

## What changed

File (overlay last-wins, same packed path):

`patch/Data/INI/Object/Specter/United States Of America/AirDefense Installation/AN_MPQ65.ini`

| Field | Before (packed DATA) | After |
|---|---|---|
| Model | `US_AN_MPQ65` | unchanged, LOOP animation kept |
| DisplayName / Side | `OBJECT:ANMPQ65` / America | unchanged |
| KindOf | `VEHICLE IMMOBILE` | `VEHICLE` (IMMOBILE removed) + `SCORE DONT_AUTO_CRUSH_INFANTRY` |
| Locomotor | none | `SET_NORMAL Generic8x8Locomotor` (same as `US_AN_TPY2`) |
| AI | none | `AIUpdateInterface` (required for pathing) |
| CommandSet | `None` | `GenericCommandSet` (`AttackMove`, `Guard`, `Stop`) |
| Physics / Body | Mass 300 / ActiveBody 800 | unchanged |
| Radar | `AN_MPQ65_WaveEmitter` + StealthDetector 970 | unchanged |
| Hole object `AmericaMPQ65Damaged` | IMMOBILE structure | copied unchanged |

Healthy SPECTER reference for movement: `US_AN_TPY2` (Generic8x8Locomotor, W3DTruckDraw, Physics Mass 300, ActiveBody 800). TPY-2 deploy/pack was **not** copied.

## Deploy / pack limitation (no new deploy behavior)

`US_AN_MPQ65.W3D` has one looping scan animation and meshes `CHASSIS` / `TIRES` / `AN/MPQ65`. It does **not** have:

- a packed companion model (`US_AN_MPQ65D` is absent)
- `Tire01`–`Tire08` bones (wheels will not spin; truck can still locomote)
- PACKING / UNPACKING / DEPLOYED art used by `US_AN_TPY2`

Patriot cueing on this Object is `FireWeaponUpdate` (`AN_MPQ65_WaveEmitter`) plus `StealthDetectorUpdate`, not a turret that only works while deployed. Adding `DeployStyleAIUpdate` would invent pack/unpack from a scan-loop animation and could gate FCR behind deploy. That was not added.

Move and stop use locomotor + `Command_Stop`. Radar FCR stays always-on while the unit is alive, including while driving.

## BIG

`_SPECTER_PATRIOT_MPQ65_MOBILE.big` contains only this INI. Place it in the game Data folder with other SPECTER BIGs. Alphabetical last-wins: this name loads after `_SPEC_DATA_ONE.big` and `_SPECTER_PATCH_FINAL.big`.
