# America MIM-104F Patriot PAC-3 — V25 → SS2

## V25 source (America)

| Piece | V25 name | File |
|---|---|---|
| Launcher | `AmericaPATRIO` | `object/AmericaVehicle.ini` model `USPAC3` |
| MSE variant | `AmericaPAC3MSE` | same file, model `PAC3MSE` |
| Weapon | `PAC3Weapon` / `PAC3MSEWeapon` | `Weapon.ini` |
| Projectile | `AIGUOZHEDAODAN` | CWC |
| Bones | `TURRET01`, `TURRETEL`, `WeaponA` | USPAC3 |
| CC button | `Command_ConstructAmericaPAC3MSE` slot 12 | `CommandSet.ini` |

V25 fires one weapon with `AntiAirborneVehicle=Yes` and `AntiBallisticMissile=Yes`, `DamageType=JET_MISSILES`.

## SS2 engine load map (destination)

ControlBar opens only `Data/INI/CommandSet.ini` and `Data/INI/CommandButton.ini`.
ThingFactory globs `Data/INI/Object/**/*.ini`. Weapon blocks inside those Object files are parsed.
`Weapon_*.ini` at INI root is **not** loaded. No BIG members are written.

Live America CC (`AmericaCommandCenterCommandSet` in `CommandSet.ini`):

- Slot 1 dozer (kept)
- Slot 6 `USAPAC3` (kept, not this unit)
- Slot 10 free → new Patriot
- `Command_ConstructAmerica_MIM104F` already exists but is **not** on the live CC (only extra `CommandSet_*.ini` files, which ControlBar does not open)

## Incompatible V25 pieces (not imported)

| V25 | Why | SS2 replacement |
|---|---|---|
| Models `USPAC3`, `PAC3MSE` | Not in `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` | `US_MIM104F_L` + missile `PAC-3` (ART TWO) |
| `CWCruS300Locomotor` | Missing | `Generic8x8Locomotor` |
| Projectile `AIGUOZHEDAODAN` | Missing | Unique `AmericaVehiclePatriotPAC3_*_Object` |
| `OCL_Pac3Hull`, CWC FX, `CWCruSA10RadarWeapon`, `Upgrade_CWCgenAntiRadarDrone` | Missing | SS2 SlowDeath / Avenger voice / no CWC radar drone |
| `DamageType=JET_MISSILES` | AirplaneArmor 25%; CruiseMissileArmor 0% | AA `PENALTY` (AirplaneArmor 80%); ABM `CRUSH` |
| One weapon for air + ballistic | SS2 BM armor `PENALTY=0%` `CRUSH=100%`; cruise also needs `CRUSH` | Two WeaponSet slots |

Unknown CWC modules were not copied.

## SS2 armor (THAAD lesson)

- `AirplaneArmor`: PENALTY 80%, CRUSH 0%, JET_MISSILES 25%
- `BallisticMissileArmor` / `SRBMArmor`: PENALTY 0%, FALLING 0%, WATER 0%, **CRUSH 100%**
- `CruiseMissileArmor`: DEFAULT 0%, PENALTY 0%, **CRUSH 100%**

Stock `THAADMissile_ABM` / `PAC3_ABM_Object` either use FALLING/WATER fuzes or have no CRUSH fuze. This unit’s ABM projectile has `FireWeaponUpdate` fuze `DamageType=CRUSH` (same working path as `USAPAC3_THAAD_ABM_OBJECT`). `US_THAAD` is not edited.

## Two missions

1. **AA (PRIMARY)** `AmericaVehiclePatriotPAC3_AA` — PENALTY, `AntiAirborneVehicle`, `AntiAirborneInfantry`, not anti-BM. Fighters/bombers.
2. **ABM + cruise (SECONDARY)** `AmericaVehiclePatriotPAC3_ABM` — CRUSH, `AntiBallisticMissile`, `AntiSmallMissile`, plus CRUSH proximity fuze. Ballistic and cruise missiles.

## Files written

- `Data/INI/CommandSet.ini` — America CC slot 10 + unique unit CommandSet
- `Data/INI/CommandButton.ini` — unique `Command_ConstructAmericaVehiclePatriotPAC3`
- `Data/INI/Object/Specter/United States Of America/AirDefense/AmericaVehiclePatriotPAC3.ini`

Turkey, GLA, Iran factory, THAAD, missile factories, SS1, ART, and other countries are unchanged.
