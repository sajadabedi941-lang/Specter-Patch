# PR #787 crash vs healthy SS2

Crash timing: America selected, countdown ends (Command Center created / faction drawables bound). Other factions were not required.

## What #787 did that live SS2 does not

| #787 | Live SS2 that works |
|---|---|
| `W3DTruckDraw` + `TrackMarks` + `Dust` + `DirtSpray` on model `US_MIM104F_L` | `America_MIM104F_Launcher` uses that model with **no** TrackMarks/Dust/tires. THAAD only puts TrackMarks on `US_M1120`, which has Tire01–08. |
| `KindOf` includes `FS_BASE_DEFENSE HUGE_VEHICLE` | CC-built `USAPAC3` is `PRELOAD SELECTABLE CAN_ATTACK … VEHICLE SCORE` only |
| `AIUpdateInterface` turret `FirePitch` / `NaturalTurretPitch` / `FiresWhileTurning` | V25 Patriot turret is Turn/Pitch/AllowsPitch/scan only; FirePitch is a DeployStyle field on THAAD/USAPAC3 |
| Custom AA/ABM projectiles (`ENGINEFX`, `CAN_ATTACK`) | Live THAAD AA is `THAAD_AA_OBJECT1` (`Engine01`, `PROJECTILE SMALL_MISSILE`, `THAADMissileLocomotor1`) |
| Extra `CommandSet AmericaVehiclePatriotPAC3CommandSet` | `USAPAC3` reuses live `GLAVehicleRocketBuggyCommandSet` |

W3DTruckDraw + tire particles on a launcher with no tire bones is the match-start drawable crash. `FS_BASE_DEFENSE` can also pull the template into America’s base-defense scan when the CC spawns.

## Fix (this pack)

- Draw: `W3DModelDraw`, bones `TURRET` / `TURRETLE` / `MISSILE` / `EXH` from live `America_MIM104F_Launcher`. V25 `USPAC3` W3D is not in SS2 ART.
- KindOf / CommandSet: same as live `USAPAC3`.
- Turret: V25 rates, `AllowsPitch=Yes` for ABM loft. No FirePitch.
- AA: unique clone of `8x_LRSAM_THAAD` / `THAAD_AA_OBJECT1` (PENALTY vs AirplaneArmor).
- ABM: unique clone of THAAD ABM stats + CRUSH fuze (stock `THAAD_ABM_OBJECT` WATER/FALLING fuzes do 0% vs `BallisticMissileArmor`). `US_THAAD` files are not edited.

In-game play was not run here; this does not prove the crash is gone on a Windows install.
