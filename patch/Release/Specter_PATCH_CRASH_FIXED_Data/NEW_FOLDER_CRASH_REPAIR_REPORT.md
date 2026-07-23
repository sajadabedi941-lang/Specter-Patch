# New folder.zip — crash repair report

## Verdict

Repaired and applied **56** files from `New folder.zip` into the correct Specter
`Data/INI/Object/Specter/...` paths. Package: `patch/Release/Specter_PATCH_CRASH_FIXED.zip`.

Static audit after apply: **PASS** (0 Object/CommandSet/ModuleTag dups, 0 empty CommandSet,
0 END/Scale syntax defects, 0 missing CommandSet refs in repaired set).

## Exact crash cause

These INIs are valid faction content, but when installed as a **flat** dump into
`GameRoot\Data\INI\<filename>.ini` they **re-define the same Object names** already
present under `Data\INI\Object\Specter\...`, which triggers:

`Reason: Uncaught Exception during initialization`

Worst cases:
- `AbbasLauncher.ini` defines **Turkey_*** objects but shares a filename with UAE;
  flat/root install or wrong-folder overwrite causes duplicate Objects.
- `SpecialForces.ini` same issue (Turkey content vs UAE same filename).
- All other listed files likewise duplicate their Specter-tree Object IDs if copied flat.

## Repair actions (every file)

| File | Error fixed | Applied to |
|------|-------------|------------|
| `AIR_FORCE_EXPANSION.txt` | Docs only; path validated | `Data/INI/Object/Specter/PatchSystems/AirForceExpansion/AIR_FORCE_EXPANSION.txt` |
| `AbbasLauncher.ini` | Turkey objects mis-routable to UAE path / flat duplicate Object Turkey_Alhussaien | `Data/INI/Object/Specter/Turkey Armed Forces/Wheeled/AbbasLauncher.ini` |
| `Airborne.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Infantry/Airborne.ini` |
| `Aircraft_AAB_Global.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini` |
| `Aircraft_AirForceExpansion.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/PatchSystems/AirForceExpansion/Aircraft_AirForceExpansion.ini` |
| `Britain_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/British Armed Forces/Drones/Britain_CombatDrone.ini` |
| `Britain_F35B.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/British Armed Forces/Airforce/Britain_F35B.ini` |
| `Egypt_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini` |
| `Egypt_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_MilitaryHQ.ini` |
| `France_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/French Armed Forces/Drones/France_CombatDrone.ini` |
| `Germany_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/German Armed Forces/Drones/Germany_CombatDrone.ini` |
| `India_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Indian Armed Forces/Drones/India_CombatDrone.ini` |
| `India_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_CommandCenter.ini` |
| `India_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_MilitaryHQ.ini` |
| `India_TejasMk2.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Indian Armed Forces/Airforce/India_TejasMk2.ini` |
| `Israel_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Israel Defense Forces/Buildings/Israel_CommandCenter.ini` |
| `Israel_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Israel Defense Forces/Buildings/Israel_MilitaryHQ.ini` |
| `Italy_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Italian Armed Forces/Drones/Italy_CombatDrone.ini` |
| `Japan_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Japan Self-Defense Forces/Drones/Japan_CombatDrone.ini` |
| `Japan_MQ9.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Japan Self-Defense Forces/Airforce/Japan_MQ9.ini` |
| `Karrar-2.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Wheeled/Karrar-2.ini` |
| `Lamiaa.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Wheeled/Lamiaa.ini` |
| `Libya_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_CommandCenter.ini` |
| `Libya_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_MilitaryHQ.ini` |
| `MilitaryHQ_StockFactions.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/PatchSystems/MilitaryHQ/MilitaryHQ_StockFactions.ini` |
| `Pakistan_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_CommandCenter.ini` |
| `Pakistan_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_MilitaryHQ.ini` |
| `Russia_AD_TorM.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/PatchSystems/AirDefense/Russia_AD_TorM.ini` |
| `SaudiArabia_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Saudi Arabian Armed Forces/Drones/SaudiArabia_CombatDrone.ini` |
| `SaudiArabia_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_CommandCenter.ini` |
| `SaudiArabia_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_MilitaryHQ.ini` |
| `SouthAfrica_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_CommandCenter.ini` |
| `SouthAfrica_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_MilitaryHQ.ini` |
| `SouthKorea_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Republic of Korea Armed Forces/Drones/SouthKorea_CombatDrone.ini` |
| `SpecialForces.ini` | Turkey SpecialForces mis-routable to UAE path / flat duplicate Objects | `Data/INI/Object/Specter/Turkey Armed Forces/Infantry/SpecialForces.ini` |
| `Sweden_CombatDrone.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Swedish Armed Forces/Drones/Sweden_CombatDrone.ini` |
| `Syria_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_CommandCenter.ini` |
| `Syria_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_MilitaryHQ.ini` |
| `Turkey_AWACS.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_AWACS.ini` |
| `Turkey_Akinci.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_Akinci.ini` |
| `Turkey_Bora.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Wheeled/Turkey_Bora.ini` |
| `Turkey_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_CommandCenter.ini` |
| `Turkey_EliteMaroonBerets.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Infantry/Turkey_EliteMaroonBerets.ini` |
| `Turkey_F16Block70.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_F16Block70.ini` |
| `Turkey_Kizilelma.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Drones/Turkey_Kizilelma.ini` |
| `Turkey_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_MilitaryHQ.ini` |
| `Turkey_TB2.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_TB2.ini` |
| `Turkey_Tu-22M3.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_Tu-22M3.ini` |
| `Turkey_WeaponObjects.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Turkey Armed Forces/Turkey_WeaponObjects.ini` |
| `UAE_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_CommandCenter.ini` |
| `UAE_MQ9.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/United Arab Emirates/Airforce/UAE_MQ9.ini` |
| `UAE_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_MilitaryHQ.ini` |
| `Ukraine_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_CommandCenter.ini` |
| `Ukraine_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_MilitaryHQ.ini` |
| `Vietnam_CommandCenter.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_CommandCenter.ini` |
| `Vietnam_MilitaryHQ.ini` | Flat/root duplicate Object risk; synced to faction-correct path | `Data/INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_MilitaryHQ.ini` |

## Syntax scan results (all 55 INIs)

- Missing END / unclosed Object (final End check): **none**
- Duplicate Object names within file: **none**
- Duplicate ModuleTags (active lines): **none**
- Empty CommandSet= / empty Prerequisites Object=: **none**
- Missing CommandSet / SpecialPower / Weapon refs (vs Specter stock+patch): **none**
- Literal `END` / bare `Scale`: **none**

## Install package

`Specter_PATCH_CRASH_FIXED.zip` runs `Install_Fix.bat` which:
1. Deletes flat `Data\INI\<leaf>.ini` copies for every repaired filename
2. Deletes leftover tool schemas (`CountryBalance.ini`, `Economy\`, `GlobalBuildLimits_SpecterPatch.ini`)
3. Merges repaired files into the correct `Object\Specter\...` tree

