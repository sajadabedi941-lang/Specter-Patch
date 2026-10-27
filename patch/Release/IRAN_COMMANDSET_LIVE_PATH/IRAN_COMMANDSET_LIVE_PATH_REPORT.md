# Iran empty command panel — live CommandSet.ini path

**Zero Hour on this VM was not run.** `generals.exe` and `INIZH.big` are not in this environment. In-game panel visibility is **not** claimed.

PRs **#706–#709 are not treated as fixed.** This pack does **not** replace `_SPEC_DATA_ONE.big`.

## 1. Release #709 BIG (exact file)

| | |
| --- | --- |
| Path | `patch/Release/IRAN_COMMANDSET_INI_FIRE/_SPEC_DATA_ONE.big` |
| Size | 374 011 625 |
| SHA-256 | `46aab7d5c9433471a545935e2f922949d85130de287e44da3d13772a18c604cc` |
| GitHub Release | `iran-commandset-ini-fire` asset digest **matches** |
| Entries | 3576, no duplicate paths |

`Data\INI\CommandSet.ini` **is** in that BIG (offset 317786517, 452817 bytes, SHA-256 `5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac`). CRLF, no NUL.

Four Iran Fire sets are at EOF of **that same file**, not only in extras:

| Index in file | Name | Byte offset |
| ---: | --- | ---: |
| 477 | `IranWarfactoryCommandSet` | 219190 |
| 1150 | `IranMissileFireCommandSet` | 452225 |
| 1151 | `IranMissileTELFireCommandSet` | 452371 |
| 1152 | `IranKhorramshahrFireCommandSet` | 452520 |
| 1153 | `IranShahed136FireCommandSet` | 452671 |

`CommandSet_ZZZZ_ZzzIranMissileFire.ini` in #709 is comments only. Unique Fire names are **not** in extra files.

## 2. Line-by-line: factory set vs missile sets (same file)

War Factory (works in-game) — one space before `=`, construct buttons, slot 15 unused on ControlBar 1–14:

```
CommandSet IranWarfactoryCommandSet
  1 = Command_ConstructIranTankKarrar
  ...
  14 = Command_Sell
  15 = Command_ConstructIranVehicleKhormshar_AI
End
```

Missile Fire (appended) — two spaces on slot 1, same layout as working `GenericMainbBattleTankCommandSet` (`  3  =`):

```
CommandSet IranMissileFireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
```

`Scud_B_CommandSet` in the same file uses `  1 = Command_FireMainWeapon` (one space). Slot format is not the empty-bar cause: both one-space and two-space forms are used by sets whose bars work (Karrar / factory).

Join before the append is a closed `End` then a blank line. 1153 unique names in `CommandSet.ini`; no duplicates in that file.

## 3. How the engine actually reads CommandSet.ini

This VM does **not** have `generals.exe`. The following is EA’s published Zero Hour source (`electronicarts/CnC_Generals_Zero_Hour`), not a dump of the user’s binary.

**ControlBar loads one hardcoded path** (`ControlBar.cpp` `ControlBar::init`):

```
ini.load("Data\\INI\\Default\\CommandButton.ini", INI_LOAD_OVERWRITE, NULL);
ini.load("Data\\INI\\CommandButton.ini", INI_LOAD_OVERWRITE, NULL);
ini.load("Data\\INI\\CommandSet.ini", INI_LOAD_OVERWRITE, NULL);
```

There is no `loadDirectory` of `CommandSet_*.ini`. Extra files in `_SPEC_DATA_ONE.big` (`CommandSet_IranMissiles.ini`, `CommandSet_ZZZZ_ZzzIranMissileFire.ini`, …) are **not** the ControlBar CommandSet table.

**Missing name ⇒ every button hidden** (`ControlBarCommand.cpp` `populateCommand`):

```
commandSet = TheControlBar->findCommandSet(obj->getCommandSetString());
if (commandSet == NULL) {
  // hide all the buttons
  return;
}
```

That is the empty panel.

**Which physical file is `Data\INI\CommandSet.ini`?**

`FileSystem::openFile`: open **loose** `Data\INI\CommandSet.ini` first; only if that fails, open the archive copy.

Among archives (`Win32BIGFileSystem::init` → `loadBigFilesFromDirectory("", "*.big")` with `overwrite = FALSE` default in `ArchiveFileSystem.h`): the **first** BIG in case-insensitive sorted order (`FilenameList = std::set<AsciiString, rts::less_than_nocase>`) that contains that path keeps it. Later BIGs do not replace it.

Typical game-folder sort:

`0_SPECTER_*.big` → `INIZH.big` → `_SPEC_ART_*.big` → `_SPEC_DATA_ONE.big`

`INIZH.big` is always present in a real Zero Hour folder and contains `Data\INI\CommandSet.ini`. It is registered **before** `_SPEC_DATA_ONE.big`. The CommandSet.ini that #709 edited inside the DATA BIG is therefore **not** the file ControlBar opens, unless a still-earlier `0_` BIG or a loose file already owns that path.

Repo docs disagree with each other (`SPECTER_BASELINE_REPORT.md` says later-wins / INIZH after `_SPEC`; RS-24 reports say first-win / INIZH before `_SPEC`). The published engine source is first-win for archive paths (`overwrite = FALSE`). This VM still cannot dump **the user’s** `INIZH.big` to list whether `IranWarfactoryCommandSet` is inside it.

`Launch_Specter.bat` copies only `_SPEC_DATA_ONE.big` and `_SPEC_ART_ONE.big`. It does not copy `INIZH.big` and does not write loose `Data\INI\CommandSet.ini`.

## 4. Is adding CommandSets to the DATA BIG’s CommandSet.ini enough?

**No.** ControlBar never opens that archive copy while `INIZH.big` (or a loose `Data\INI\CommandSet.ini`) already owns the path. Extra unique-path CommandSet files are not loaded by `ControlBar::init` at all. That matches:

| Pack | Where unique Fire CS names lived | In-game |
| --- | --- | --- |
| #708 | extra `CommandSet_*.ini` only | empty panel |
| #709 | EOF of DATA `CommandSet.ini` | empty panel |

Duplicate CommandSet **names** in a second loaded file throw `INI_INVALID_DATA` (`parseCommandSetDefinition`) unless `INI_LOAD_CREATE_OVERRIDES`. ControlBar loads CommandSet.ini once, so trailing **new** names in the file that is actually opened would parse. They never reach that parser if that file is INIZH’s copy without those names.

## 5. Object → CommandSet (all 19) vs a working Iran unit

First-win Objects inside the #709 DATA BIG (KindOf `SELECTABLE CAN_ATTACK VEHICLE` — not the empty-bar cause):

| Object | CommandSet | In DATA `CommandSet.ini` | Extra file | Live table (engine path above) |
| --- | --- | --- | --- | --- |
| Fateh-313, Fattah, Fattah2, ZolfagharM, DezfulPenetrator, BM-21, Hoveyzeh, Hormuz, Qader, Qiam, Emad, Khalij, Dezful, Khorram, Kheibar, Ghadr, Simorgh | `IranMissileFireCommandSet` | yes (EOF) | no | **not loaded** |
| `IranVehicleKhormshar` | `IranKhorramshahrFireCommandSet` | yes (EOF) | no | **not loaded** |
| `IranVehicleShahedLauncher` | `IranShahed136FireCommandSet` | yes (EOF) | no | **not loaded** |
| `IranWarFactory` | `IranWarfactoryCommandSet` | yes (index 477) | no | **loaded** (same name lives in the INIZH/loose CommandSet.ini the factory bar already uses) |
| `IranTankKarrar` | `GenericMainbBattleTankCommandSet` | yes (index 684) | no | **loaded** (stock SPECTER name) |

Presence in the extracted DATA file is not proof of load. The factory/Karrar bars work because those **names** are in the CommandSet.ini ControlBar actually opens. The four Fire names exist only at the end of the DATA copy, which ControlBar does not open.

## 6. Cause (short)

ControlBar reads only `Data\INI\CommandSet.ini`. Loose files beat BIGs. Among BIGs the first archive wins that path; `INIZH.big` sorts before `_SPEC_DATA_ONE.big`. #709 put the four Fire CommandSets in the DATA BIG’s CommandSet.ini, so they never entered the live table. Unique extra files used in #708 are not loaded by ControlBar at all. `findCommandSet` returns NULL and hides every button.

`INIZH.big` / `generals.exe` / the game-folder `*.big` list / a pre-existing loose `Data\INI\CommandSet.ini` were **not** on this VM and are still required if this overlay does not change the in-game bar (see below).

## 7. Smallest fix (after the cause above)

Do **not** ship a fifth `_SPEC_DATA_ONE.big`. Keep the installed #709 DATA BIG (Objects already point at the four names). Put those names into the file ControlBar actually opens:

**Primary:** loose `Data\INI\CommandSet.ini` next to `generals.exe` (LocalFileSystem wins over every BIG). This file is the #709 DATA `CommandSet.ini` (1153 sets: factory + Karrar + the four Fire names). It is the SPECTER CommandSet.ini plus four blocks at EOF.

**Optional:** `0_SPECTER_IranCommandSet.big` containing only that same path, so it sorts before `INIZH.big` if no loose file exists. If an earlier `0_SPECTER_*.big` already contains `CommandSet.ini`, the loose file is still required. Those `0_` BIGs are not on this VM.

Static-only. Not an in-game Zero Hour confirmation.

## Install

Keep `_SPEC_DATA_ONE.big` from Release `iran-commandset-ini-fire` (SHA `46aab7d5…`). Do not run two DATA BIGs.

1. In the Zero Hour folder (the folder that contains `generals.exe`) create `Data\INI\` if needed.
2. Copy this `CommandSet.ini` to `Data\INI\CommandSet.ini`.
3. SHA-256 of that loose file must be `5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac`.
4. Optional: copy `0_SPECTER_IranCommandSet.big` next to `generals.exe` only if you cannot use a loose INI.

If a loose `Data\INI\CommandSet.ini` already exists, replace it with this file (or merge the four `CommandSet Iran*FireCommandSet` blocks into it). The old loose file would keep winning and would still lack the four names.

## If the panel is still empty after this overlay

Send these from the real game folder (this VM still does not have them):

1. `INIZH.big` (the one next to `generals.exe`)
2. Directory listing of every `*.big` in that folder
3. Whether `Data\INI\CommandSet.ini` exists **before** install; if yes, that file
4. `0_SPECTER_CountrySupplyIncome.big` and `0_SPECTER_NatoSpainDisplay.big` if present (to see if they already own `CommandSet.ini`)

## This Release

| File | Size | SHA-256 |
| --- | ---: | --- |
| `CommandSet.ini` | 452 817 | `5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac` |
| `0_SPECTER_IranCommandSet.big` | 452 865 | `274c4a52c1e79d440914f709d98639fc017b29d81f96e7e9d20a620b53466ed4` |
