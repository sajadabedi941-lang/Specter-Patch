# America crash after Patriot Stage 1 — root cause hunt

Crash is **not claimed fixed**. America countdown was not playtested here.

User playtest of PR #791 Stage 1: after deleting
`Data/INI/Object/Specter/United States Of America/AirDefense/AmericaVehiclePatriotPAC3.ini`
and removing CC slot 10, America still crashes. The Patriot Object is **not** a confirmed direct cause.

Original `/tmp/ss2/SPECTER FINAL (GeneralsMode.com)` was not modified. PAC-3 was not re-added. No BIGs changed.

## 1. Pre-#787 vs PRs #787–#791

Parent of #787 is `d2cc5196` (tunnel loaders). Every file in #787–#791 lives under:

- `patch/tools/ss2_usa_patriot_pac3/`
- `patch/Release/SPECTER_SS2_USA_PATRIOT_PAC3/`

No `PlayerTemplate.ini`, Command Center, Dozer, SpecialPower, or OCL file in the game tree is in those diffs.

Game-installable ZIP members only:

| File | Role |
|---|---|
| `Data/INI/CommandSet.ini` | full replace of live CS |
| `Data/INI/CommandButton.ini` | full replace of live CB |
| `Data/INI/Object/.../AmericaVehiclePatriotPAC3.ini` | new Object |

Pre-#787 CommandSet used as the pack backup is byte-identical to live CS
`593f541674b5917715a189c2aedf462c079233bbd4e21a11f24299b85ab32240`.

## 2. Independent change groups inside #787–#791

| ID | Change | #787 | #788–#790 | User Stage 1 |
|---|---|---|---|---|
| A | America CC slot 10 `Command_ConstructAmericaVehiclePatriotPAC3` | added | kept | removed; crash remains |
| B | Extra `CommandSet AmericaVehiclePatriotPAC3CommandSet` at EOF | added | **removed** | n/a on #788+ |
| C | Appended `CommandButton Command_ConstructAmericaVehiclePatriotPAC3` | added | comment-only tweak | unknown unless STAGE1 ZIP restored CB |
| D | New Object INI | added | rewritten | deleted; crash remains |

A+D removed and crash remains → those two are not sufficient.

If the Stage 1 restore ZIP was used, A+B+C+D are all gone (live CS/CB restored byte-for-byte) and the crash still belongs **outside** #787–#791.

## 3. America start chain (live Loose Data, not in #787–#791)

`PlayerTemplate FactionAmerica`:

- `StartingBuilding = AmericaCommandCenter`
- `StartingUnit0 = AmericaVehicleDozer`
- `StartingUnit1 = AmericaSystemSpecialPowerShortcut`
- `SpecialPowerShortcutCommandSet = SpecialPowerShortcutUSA`

Those objects exist. CC CommandSet buttons 1,6,12–18 all resolve to existing CommandButtons and Objects. No duplicate CommandSet names.

Last-win: `Data/INI/Object/zzzz_SPECTER_CountryScans.ini` redefines `Object AmericaCommandCenter` and adds:

```
Behavior = OCLSpecialPower ModuleTag_AmericaCountryScan
  SpecialPowerTemplate = SpecialPowerAmericaCountryScan
  OCL                  = SUPERWEAPON_AmericaCountryScan
```

Loose `SpecialPower.ini` and `ObjectCreationList.ini` do **not** define those names.

They exist only inside `0_SPECTER_NoGeneralSpySatellite.big` (`SpecialPower.ini` / `ObjectCreationList.ini`). Loose files of the same names typically first-win, so the BIG copies are not used. That leaves the last-win America Command Center pointing at a missing SpecialPower/OCL.

This is a static suspect for an America-only spawn crash. It is **not** in PRs #787–#791 and is **not** in-game proven.

## 4. Isolated copies / real tests

Trees under `/tmp/ss2-tests/` (original untouched): `clean`, `with-patriot`, `stripped`.

Wine 9.0 loads `generals.exe` then exits 0 (llvmpipe, no window). No America faction screen, no countdown. Groups A–D could not be playtested here.

Recorded real test (user): A+D removed → crash remains.

Not run: C-only leftover button; Country Scan SpecialPower/OCL gap.

## 5. Proven vs unknown

Proven:

- #787–#791 do not edit America CC/Dozer/PlayerTemplate/SpecialPower/OCL sources.
- CS/CB delta vs pre-#787 is only groups A–C (B gone after #788).
- User: deleting Object D and slot 10 A does not stop the crash.

Unknown / not proven:

- Leftover CommandButton C if CS/CB were not fully restored.
- Missing Loose `SpecialPowerAmericaCountryScan` / `SUPERWEAPON_AmericaCountryScan` on last-win America CC.
- Other Loose Data on the user’s install that is not in #787–#791.

No patch was applied to original SPECTER. No crash-fix ZIP.
