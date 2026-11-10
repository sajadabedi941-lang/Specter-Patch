# Israel: replace Strategy Center with existing Global Store

**Zero Hour was not run.** Static INI / BIG validation is not an in-game
screenshot.

## Live Israel construction menu

| Step | Value |
| --- | --- |
| PlayerTemplate | `FactionAmericaAirForceGeneral` |
| StartingUnit0 | `AirF_AmericaVehicleDozer` |
| Object Side | Israel |
| CommandSet | `AirF_AmericaDozerCommandSet` |
| ControlBar file | `Data\INI\CommandSet.ini` only |

`IsraelDozerCommandSet` already had slot 2 =
`Command_ConstructIsrael_GlobalStore`, but the starting dozer does not
use that set. The button art on the Strategy Center construct command
was already `Button_GlobalMarket`, so the menu looked like Global Store
and built Industry Planet.

## Fix (Israel only)

`AirF_AmericaDozerCommandSet` slot 2:

| Before | After |
| --- | --- |
| `AirF_Command_ConstructAmericaStrategyCenter` | `Command_ConstructIsrael_GlobalStore` |

Existing chain (unchanged bytes):

- `Command_ConstructIsrael_GlobalStore` → `Israel_GlobalStore`
- `ButtonImage = Button_GlobalMarket` (same TGA as Germany)
- `Israel_GlobalStore` → `Iraq_MICCommandSet`, `Side = Israel`,
  `BuildCost = 7000`, empty `Prerequisites`
- MappedImage `Button_GlobalMarket` → `Button_GlobalMarket.tga`
  (keep `0_SPECTER_GlobalStoreCameos.big`)

Three extra `CommandSet_*` copies that redefined the same AirF dozer
set still had Strategy Center. They are updated so a last-win overlay
cannot restore it. ControlBar still loads only `CommandSet.ini`.

## Unchanged on purpose

- Other countries' Global Store construct slots (USA slot 2, Germany
  slot 2, and the rest)
- `IsraelDozerCommandSet` (already GS)
- `CommandButton.ini`, `PlayerTemplate.ini` (AA combo hide kept)
- `Weapon.ini`, Shahed Fire, Shahed cost 8000, Vietnam radar
  `TriggeredBy = Upgrade_AmericaRadar`
- ART originals and `0_` overlays
- Units, economy, radar menus, prices

USA still has Strategy Center on `AmericaDozerCommandSet` slot 15.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `df81c16bfbfc4c1b666056e3e9c2ce0a8237fa68e3d90fa54f0f499c05d95b46` |
| `CommandSet.ini` | `1fdbc74c096077fa871708d7fe87a2b1a09de6efc8202ccbb502adb59793a85c` |
| `CommandButton.ini` | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `PlayerTemplate.ini` | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |
| `ISRAEL_GS_INSTALL.zip` | `90109d9ea4c0e7c2657e939bd4b251045f6b69eeadee9c013709c96c8f21380e` |
