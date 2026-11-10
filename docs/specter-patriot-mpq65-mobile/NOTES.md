# PR #743 correction — new mobile Patriot radar vehicle

The static site radar `AmericaRadarAN/MPQ65` is restored. A **new** Object `AmericaVehiclePatriotMPQ65` is produced from `America_MilitaryHQ`.

Zero Hour was not run. In-game Command Center clicks were not tested.

## Static Patriot radar (unchanged)

Packed `_SPEC_DATA_ONE.big` → `Data/INI/Object/Specter/United States Of America/AirDefense Installation/AN_MPQ65.ini`

- Object `AmericaRadarAN/MPQ65` still `KindOf ... VEHICLE IMMOBILE`, no Locomotor
- Overlay no longer redefines this Object (the PR #743 rewrite file was deleted)

MIM-104F still spawns this static FCR via `SpawnMPQ65ViaWeapon`. PAC-3 launchers and Iron Dome were not edited.

## New vehicle

| Field | Value |
|---|---|
| Object | `AmericaVehiclePatriotMPQ65` |
| Model | `US_AN_MPQ65.W3D` (same art, new Object) |
| Side | America |
| Locomotor | `Generic8x8Locomotor` + `AIUpdateInterface` |
| CommandSet (unit) | `GenericCommandSet` (Stop / Guard / AttackMove) |
| Radar | `AN_MPQ65_WaveEmitter` + StealthDetector **970** |
| Cost / time | 2600 / 15.0s (same as packed `US_AN_TPY2`) |
| HQ | `America_MilitaryHQ` → `America_MilitaryHQCommandSet` **slot 12** (was empty) |
| Button | `Command_ConstructAmericaVehiclePatriotMPQ65` / `SAPatriot` |

Last-wins CommandSet file only redefines `America_MilitaryHQCommandSet`. Other countries' HQ sets are untouched.

No pack/unpack: `US_AN_MPQ65.W3D` has no packed companion model. FCR stays always-on.

## BIG

`_SPECTER_PATRIOT_MPQ65_VEHICLE.big` — does **not** contain `AN_MPQ65.ini`.

If `_SPECTER_PATRIOT_MPQ65_MOBILE.big` from the first PR #743 release is still in the game Data folder, **remove it**; that archive overwrote the static radar.
