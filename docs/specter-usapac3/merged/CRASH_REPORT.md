# CommandSet.ini crash — AmericaCommandCenterCommandSet

Zero Hour was not run. Packed-archive / INI parse audit.

## Crash site

```
Data/INI/CommandSet.ini
CommandSet AmericaCommandCenterCommandSet
```

Packed live file (CRLF): **line 2570**.

## Original vs patched CommandSet block

Original unified `_SPEC_DATA_ONE.big` `CommandSet.ini`
(`a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87`, 14,278 lines):

```
2570 CommandSet AmericaCommandCenterCommandSet
2571   1  = Command_ConstructAmericaDozer
2572  12  = Command_ConstructAmericaVehicleUH60
2573  13  = Command_ConstructAmericaVehicleM2A3BuskIIIMech
2574  14 = Command_Sell
2575  15 = Command_ConstructSpecterAI_CZDropMarker
2576  16 = Command_ConstrucAmericaDronesMq9AI
2577  17 = Command_ConstructAmericaHelicopterCh47F_AI
2578  18 = Command_ConstructAmericaDroneMQ4AI
2579 End
```

Patched file (same path, `f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223`, 14,279 lines).
Byte-identical to original **except one inserted line**:

```
2570 CommandSet AmericaCommandCenterCommandSet
2571   1  = Command_ConstructAmericaDozer
2572   6  = Command_ConstructUSAPAC3          <-- inserted
2573  12  = Command_ConstructAmericaVehicleUH60
... unchanged through End at 2580
```

No braces. SAGE CommandSet uses `End`. Slot count: original 8 assignments, patched 9. Order of previous slots unchanged.

Every original slot's button exists in `CommandButton.ini`:

| Slot | Button | CommandButton.ini line |
|---:|---|---:|
| 1 | `Command_ConstructAmericaDozer` | 3090 |
| 12 | `Command_ConstructAmericaVehicleUH60` | 3330 |
| 13 | `Command_ConstructAmericaVehicleM2A3BuskIIIMech` | 3431 |
| 14 | `Command_Sell` | 1310 |
| 15 | `Command_ConstructSpecterAI_CZDropMarker` | 14086 |
| 16 | `Command_ConstrucAmericaDronesMq9AI` | 3563 |
| 17 | `Command_ConstructAmericaHelicopterCh47F_AI` | 3322 |
| 18 | `Command_ConstructAmericaDroneMQ4AI` | 3604 |
| **6** | `Command_ConstructUSAPAC3` | **missing** (crash) |

## Why it crashed

`Command_ConstructUSAPAC3` was **not** in `CommandButton.ini`.
It lived only in `CommandButton_USAPAC3.ini` (`Object = USAPAC3`, valid).

ZH parses `CommandSet.ini` / `CommandButton.ini` before unique-path INI
from the DATA BIG. The launcher also copied loose `Data\INI\CommandSet.ini`,
so that parse happens with the leftover/unified `CommandButton.ini` that
has no USAPAC3 button. Lookup of `Command_ConstructUSAPAC3` during
`AmericaCommandCenterCommandSet` → init crash.

Copying the **full** `CommandSet.ini` did not strip other CC slots; the
file is original Specter CommandSet.ini plus that one line. The
incompatibility is the unresolved button name, not lost THAAD/Patriot/NASAMS
slots (those are not on this CommandSet).

`AmericaCommandCenterCommandSet` is defined once, only in `CommandSet.ini`.

## Fix

1. Keep slot 6 on `AmericaCommandCenterCommandSet` (CommandSet.ini unchanged).
2. Append `CommandButton Command_ConstructUSAPAC3` / `Object = USAPAC3` to
   packed `CommandButton.ini` (once).
3. Remove `CommandButton_USAPAC3.ini` from DATA so the name is not defined twice.
4. Launcher copies both loose `CommandSet.ini` and `CommandButton.ini`.
