# USAPAC3 missing from America's Command Center — root cause

Zero Hour was not run. This is a packed-archive / INI path audit of the
live unified DATA (`_SPEC_DATA_ONE.big`) plus ControlBar load rules.

`_SPECTER_PATCH_FINAL.big` being absent does not fix the button. That
overlay never owned the CommandSet attached to the Command Center the
player actually opens.

## 1. Live America Command Center object and CommandSet

| Step | Winner | Value |
|---|---|---|
| `PlayerTemplate FactionAmerica` | `Data\INI\PlayerTemplate.ini` in `_SPEC_DATA_ONE.big` | `StartingBuilding = AmericaCommandCenter` |
| Object | `Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini` | `Object AmericaCommandCenter` |
| Object `CommandSet =` | same file | `AmericaCommandCenterCommandSet` |
| CommandSet definition | `Data\INI\CommandSet.ini` | slots 1, 12–18 only (before this fix) |

`Object America_MilitaryHQ` is **not** in live DATA.
`MilitaryHQ_StockFactions.ini` is **not** in live DATA.
`PlayerTemplate_SpecterPatch.ini` does not redefine FactionAmerica.

## 2. BIG load order and who owns CommandSet.ini

Zero Hour loads every `*.big` next to `generals.exe` (case-insensitive
sort). Same archive path: first owner wins. Loose `Data\` beats every BIG.

ControlBar **first-wins** `Data\INI\CommandSet.ini` and
`Data\INI\CommandButton.ini`. Unified install copies those two files
loose, with the same bytes as packed DATA.

| Archive / file | Role |
|---|---|
| `0_SPECTER_*.big` | TGA overlays only |
| `_SPEC_ART_ONE.big` | textures / terrain (canonical 2,145,283,309 B) |
| `_SPEC_ART_TWO.big` | W3D + USAPAC3 art |
| `_SPEC_DATA_ONE.big` | live DATA / INI |
| loose `Data\INI\CommandSet.ini` | **wins AmericaCommandCenterCommandSet** |

`CommandSet_FactionExpansion_Armies.ini` is a **different path**. It does
not replace `CommandSet.ini`. After PATCH_FINAL is gone, the merged DATA
copy of FactionExpansion is the only owner of that unique path — and it
only defines `America_MilitaryHQCommandSet`, which no live America CC uses.

## 3. Button, object, art

All present in the merged SPEC archives. None of these was the missing
button:

| Item | Status |
|---|---|
| `CommandButton Command_ConstructUSAPAC3` | `CommandButton_USAPAC3.ini` — `Object = USAPAC3`, `ButtonImage = USAPAC3` |
| `Object USAPAC3` | unique name, `Side = America`, `BuildCost = 3876`, `BuildTime = 18.6` |
| Prerequisites | `Science = SCIENCE_Rank3` (same as THAAD; locks until 3-star, does not hide the slot) |
| MappedImage `USAPAC3` | `USAPAC3TB.tga` |
| ART TWO | 16 New Donor files including `UsaPac3Car.W3D` and `USAPAC3TB.tga` |

## 4. Slot 6 was on the wrong CommandSet

Before this fix, `AmericaCommandCenterCommandSet` (the live CC) had:

```
1  = Command_ConstructAmericaDozer
12 = Command_ConstructAmericaVehicleUH60
13 = Command_ConstructAmericaVehicleM2A3BuskIIIMech
14 = Command_Sell
15–18 = AI-only (ControlBar slots 15–18 are invisible)
```

Slot 6 was empty. `Command_ConstructUSAPAC3` was only on
`America_MilitaryHQCommandSet` slot 6 (FactionExpansion + ZZZZ). That
CommandSet is never referenced by `AmericaCommandCenter`.

Existence of USAPAC3 in *a* CommandSet is not enough. Slot 6 must be on
the CommandSet attached to the active America Command Center.

## 5. Conflicting / duplicate definitions

| Name | Files in live DATA | Winner for America's CC |
|---|---|---|
| `AmericaCommandCenterCommandSet` | `CommandSet.ini` only | that block |
| `America_MilitaryHQCommandSet` | FactionExpansion then ZZZZ (duplicate) | unused — no MilitaryHQ object |
| `Command_ConstructUSAPAC3` | `CommandButton_USAPAC3.ini` only | unique, valid |
| `Object USAPAC3` | `USAPAC3.ini` only | unique, valid |

Redefining `AmericaCommandCenterCommandSet` in a second file
(`CommandSet_ZZZZ_*.ini`) would duplicate a CommandSet name already in
`CommandSet.ini`. That is the documented crash pattern. The fix edits
the existing block in `CommandSet.ini` in place.

## 6. Fix applied (this change only)

1. Packed `Data\INI\CommandSet.ini` — add
   `6 = Command_ConstructUSAPAC3` to `AmericaCommandCenterCommandSet`.
   Slots 1, 12–18 unchanged. No other CommandSet edited.
2. Ship that same `CommandSet.ini` loose and copy it to
   `Data\INI\CommandSet.ini` from Launch/Install so ControlBar first-win
   matches packed DATA.
3. Overlay `patch/Data/INI/CommandSet.ini` gets the same slot-6 line so
   the repo source matches intent. That overlay file is **not** the live
   450,860-byte CommandSet.ini.

THAAD, static Patriot, NASAMS, other countries, and other CC slots were
not modified.
