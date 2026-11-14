# America Patriot PAC-3 crash isolation (static)

Game play was not run here. This is a static isolation of the countdown crash.

## Isolation: CC button vs Object vs starting buildings

Pre-PAC-3 live `CommandSet.ini` / `CommandButton.ini` vs this pack:

- `CommandSet.ini`: one added line, America CC slot 10 = `Command_ConstructAmericaVehiclePatriotPAC3`
- `CommandButton.ini`: live file is a prefix; only the unique construct button is appended
- `PlayerTemplate.ini` America start is unchanged: `AmericaCommandCenter`, `AmericaVehicleDozer`, `AmericaSystemSpecialPowerShortcut`
- `Object AmericaCommandCenter` still uses `AmericaCommandCenterCommandSet`

America countdown creates the Command Center. Slot 10 `UNIT_BUILD` instantiates `AmericaVehiclePatriotPAC3` (also `KindOf PRELOAD`). CommandSet/Button syntax is not the payload. Starting buildings are not the payload. The Object template is.

## Isolation: Object vs live same-model truck

Live CC slot 6 already builds `USAPAC3` (`UsaPac3Car`, `TIRE01`–`TIRE08`, `TrackMarks`, `Dust`, second draw `UsaPac3Car_w` / `TIRE09`–`TIRE10`, `AttachToBoneInAnotherModule = CORE`). America starts with that unit on the bar.

`ModuleTag_TracksDraw` exists in live INI **only** on `USAPAC3.ini`. That object uses `ChinaVehicleDozerLocomotor` (`Appearance = TREADS`, no `HasSuspension`).

Live 8-wheel `Generic8x8Locomotor` (`HasSuspension = Yes`) trucks use **one** `W3DTruckDraw` with eight tire bones:

- `US_THAAD` / `US_M1120`
- `AmericaMobileSamSiteMIM104F`

No live object pairs `Generic8x8Locomotor` with USAPAC3's 2-bone attached `UsaPac3Car_w` draw.

PR #789 is that unique pair. That is the defective Drawable module.

## Single fix

Removed `Draw = W3DTruckDraw ModuleTag_TracksDraw` (`UsaPac3Car_w`, `TIRE09`/`TIRE10`, `AttachToBoneInAnotherModule = CORE`).

Left unchanged: `W3DTruckDraw` `UsaPac3Car` with `TIRE01`–`TIRE08`, `TrackMarks`/`Dust`, `Generic8x8Locomotor`, `AIUpdateInterface` (no deploy), THAAD AA/ABM clones, America CC slot 10, slots 1 and 6.

In-game crash is not claimed fixed.
