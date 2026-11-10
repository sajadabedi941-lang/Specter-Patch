# Hide Arabic Alliance from the skirmish / multiplayer country combo

**Zero Hour was not run.** Engine-source evidence ≠ an in-game screenshot.

## Why release `remove-arabic-alliance` did not hide the country

That pack did install a real change: `PlayerTemplate FactionGLA` in
`Data\INI\PlayerTemplate.ini` (loose + inside `_SPEC_DATA_ONE.big`) set

- `PlayableSide = No`
- `OldFaction = No`

and left `StartingBuilding = GLACommandCenter`.

The country dropdown does not use `PlayableSide`.

Zero Hour source `GeneralsMD/Code/GameEngine/Source/GameNetwork/GUIUtil.cpp`,
function `PopulatePlayerTemplateComboBox` (also called from
`SkirmishGameOptionsMenu.cpp` and the LAN / GameSpy slot lists):

1. Walk every `PlayerTemplate` in `ThePlayerTemplateStore`.
2. **Skip if `getStartingBuilding().isEmpty()`.** This is the actual
   playable-country filter. Civilian and Observer are hidden because they
   have no `StartingBuilding`, not because `PlayableSide = No`.
3. If the "original factions" checkbox is on, skip `OldFaction = No`.
   Default skirmish does not use that filter, so `OldFaction = No` alone
   left Arabic Alliance in the full list.
4. Deduplicate by `Side`. First remaining `Side = GLA` wins the row.
5. The visible text is `TheGameText->fetch("SIDE:" + side)`, **not**
   `DisplayName` / `INI:FactionGLA`.

`GameLogic.cpp` `populateRandomSideAndColor` and
`SkirmishPreferences::getPreferredFaction` use the same
`StartingBuilding` test.

So even a correctly copied previous `PlayerTemplate.ini` still listed
the country. Static checks that only looked at `PlayableSide` could not
catch that.

## Which file and which string the menu actually uses

| Step | Path / symbol | Evidence |
| --- | --- | --- |
| Load | `GameEngine.cpp` `initSubsystem(ThePlayerTemplateStore, …, "Data\\INI\\Default\\PlayerTemplate.ini", "Data\\INI\\PlayerTemplate.ini")` | Two files only. No `loadDirectory`. `PlayerTemplate_SpecterPatch.ini` is **not** loaded by this store. |
| Merge | `SubsystemInterfaceList::initSubsystem` | `INI_LOAD_OVERWRITE` on those two paths. Default PT in live DATA is a header with **zero** `PlayerTemplate` blocks, so it cannot restore GLA. |
| Open | `FileSystem::openFile` | Loose `Data\INI\PlayerTemplate.ini` first; if missing, first BIG that owns the path (`overwrite = FALSE`). `INIZH.big` sorts before `_SPEC_DATA_ONE.big`. |
| Combo row | `PlayerTemplate FactionGLA` | Only template with `Side = GLA`. SpecterPatch has Egypt/Israel only, neither `Side = GLA`. |
| Combo label | CSF `SIDE:GLA` | Decoded from live `Data\English\generals.csf`: **Arabic Alliance**. `INI:FactionGLA` is the same string but is `DisplayName` (load screen), not the dropdown. CSF was **not** edited; hiding the row is the fix. |

SPECTER already ships a loose `Data\INI\PlayerTemplate.ini`. Replacing
only `_SPEC_DATA_ONE.big` never changes the combo, because the loose
file wins. The previous installer *did* copy the loose file; the live
file still had `StartingBuilding = GLACommandCenter`, so the country
remained.

## Fix in this pack (only `PlayerTemplate.ini`)

`PlayerTemplate FactionGLA` is kept (maps/scripts that name `FactionGLA`
still resolve). Inside the block:

| Field | Previous pack | This pack | Why |
| --- | --- | --- | --- |
| `StartingBuilding` | `GLACommandCenter` | commented out (empty) | This is the field `PopulatePlayerTemplateComboBox` actually tests. |
| `PlayableSide` | `No` | `No` | Unused by the combo; left No. |
| `OldFaction` | `No` | `No` | Only affects the original-factions filter. |
| `Side` | `GLA` | `GLA` | Kept for map/script compatibility. |
| `DisplayName` | `INI:FactionGLA` | unchanged | Load-screen label; not the combo. |

No other combo-visible template has `Side = GLA`, so `SIDE:GLA` cannot
reappear from Iraq / Saudi Arabia / UAE / Syria / Libya (those sides
are `Iraq`, `SaudiArabia`, `UAE`, `Syria`, `Libya`).

## Unchanged on purpose

- Iraq, Saudi Arabia, UAE, Syria, Libya: same bytes as source, still
  `PlayableSide = Yes` and still have `StartingBuilding`.
- `CommandSet.ini` / `CommandButton.ini` SHA match `vietnam-radar-minimap`
  / `remove-arabic-alliance` (Shahed Fire + cost 8000 + Vietnam radar).
- `Weapon.ini`, `SpecterRadarUavs.ini`, Vietnam radar object, ART, `0_`
  overlays, `generals.csf`.
- ArabicArmy objects and `…\Arabic Alliance\` object folder (Egypt's
  dozer still builds some of them).

## SHA-256

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `AA_COMBO_HIDE_INSTALL.zip` | 307043782 | `3b7a05a1dc56bdcdc22ed198bd8d366604759daea8de6cc973c682f6ce6ce944` |
| `_SPEC_DATA_ONE.big` | 374075601 | `00a9bbe5b4ff9236df67d9835e6039aebab4d72650e5ff722facb56854006a46` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `PlayerTemplate.ini` | 43929 | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |

Loose `PlayerTemplate.ini` must be installed at `Data\INI\PlayerTemplate.ini`.
The installer refuses to finish unless that file contains
`SPECTER_PATCH AA_COMBO_HIDE`.
