# India: remove country UAVs from production

**Zero Hour was not run.** Static INI / BIG validation is not an in-game
screenshot.

## Identified India drones (Side=India, KindOf includes AIRCRAFT DRONE)

| Object | File | Construct button | Produced from |
| --- | --- | --- | --- |
| `India_CombatDrone` | `Drones\India_CombatDrone.ini` | `Command_ConstructIndia_CombatDrone` | Radar slot 1, Heavy Air Base slot 3 |
| `India_LoiteringDrone` | `Drones\India_LoiteringDrone.ini` | `Command_ConstructIndia_LoiteringDrone` | Radar slot 2, Heavy Air Base slot 4 |
| `India_HeavyUAV` | `Drones\India_HeavyUAV.ini` | none | not on any live CommandSet |

Overlay: `CommandSet_ZZZZ_SpySatelliteRadar.ini` redefined
`India_RadarCommandSet` with the same Combat/Loitering slots.

## Not removed

- `IndiaInfantryDroneOperatorFPV`, `IndiaInfantryLancetTeam` (INFANTRY)
- `India_AD_AntiDrone` (air defense)
- `India_Systems.ini` dummy DRONE KindOf objects
- Specter radar UAVs on India radar (Heron, MQ-4, Orlan-10, Shahed)
- Heavy Air Base manned aircraft (Mi-8T, IL-76, Tu-22M3M, B-2A, Ka-52)
- Other countries' drone buttons and radar menus
- ART / `0_` overlays / weapons / stats of unrelated units

## Fix

Comment out the four production slots. Set `Buildable = No` on the three
drone objects. CommandButton.ini is unchanged (buttons unused).

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e` |
| `CommandSet.ini` | `ba1c8175abc717aac5bb67d23abf249f24ebe24fe63ce00ffcbe250c40ae1e57` |
| `CommandButton.ini` | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `PlayerTemplate.ini` | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |
| `INDIA_NO_DRONES_INSTALL.zip` | `160245775473d796202e5c7dc4bbd1391e41161074a5cee23b5d74db3803d1dd` |
