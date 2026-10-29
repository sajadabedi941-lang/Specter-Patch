# Unified SPECTER pack: Israel Global Store + India UAV removal

**Zero Hour was not run.** Neither PR #728 nor PR #729 has been
confirmed inside the game. This pack only concatenates the already
statically-checked DATA lineage:

`aa-combo-hide` → `israel-gs-strategy` → `india-no-drones`

## Israel

`AirF_AmericaDozerCommandSet` slot 2 = `Command_ConstructIsrael_GlobalStore`.
Extra `CommandSet_*` copies of the same AirF set match. USA Strategy Center
on `AmericaDozerCommandSet` slot 15 is unchanged.

## India

`India_RadarCommandSet` and `India_HeavyAirBaseCommandSet` no longer have
active CombatDrone / LoiteringDrone slots. The three UAV objects have
`Buildable = No`. Heron / MQ-4 / Orlan-10 / Shahed stay on India radar.

## Installer

`Install_IsraelIndiaFixes.bat` copies only:

- `_SPEC_DATA_ONE.big`
- `Data\INI\CommandSet.ini`
- `Data\INI\CommandButton.ini`
- `Data\INI\PlayerTemplate.ini`

It does not copy `_SPEC_ART_ONE.big`, `_SPEC_ART_TWO.big`, or `0_*.big`.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e` |
| `CommandSet.ini` | `ba1c8175abc717aac5bb67d23abf249f24ebe24fe63ce00ffcbe250c40ae1e57` |
| `CommandButton.ini` | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `PlayerTemplate.ini` | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |
| `SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip` | `72e59762ca086c54bc57294e46d042cefeb8773859f25ba5e81ab5bc349b962b` |
