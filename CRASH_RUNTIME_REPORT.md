# CRASH_RUNTIME_REPORT

**Status:** Predicted runtime crashes found (static skirmish load simulation).  
**Auto-fix:** Not applied (report only).  
**Date:** 2026-07-23

---

## 1. Live launch result

| Check | Result |
|---|---|
| Final patch present (`patch/`, integrity reports) | Yes |
| `generals.exe` / Wine in this environment | **No** |
| Real gameplay launch | **BLOCKED** |

This cloud agent cannot start Generals Zero Hour. All findings below are from a **static skirmish load simulation** against:

- Patch overlay: `patch/Data/INI/`
- Stock Specter INI: extracted from `Specter_Data.zip` → `Data/INI/**` (full path extract, 884 INIs)

Simulation walk:

`PlayerTemplate` → `StartingBuilding` → `CommandSet` → `CommandButton` → `Object` / `Upgrade` / `Science`  
(depth 2 into produced buildings; science bars + superweapon shortcuts)

---

## 2. Predicted crashes (exact)

### CRASH 1 — Boss faction cannot enter skirmish

| Field | Value |
|---|---|
| **Exact object name** | `Boss_CommandCenter` |
| **File path** | `Data/INI/PlayerTemplate.ini` (from `Specter_Data.zip`) |
| **Line number** | **276** (`StartingBuilding = Boss_CommandCenter`) |
| **Reason** | `Object Boss_CommandCenter` is **not defined** anywhere in Specter Object INI (full archive extract) or the patch. Skirmish spawn for `FactionBossGeneral` / Side `Boss` will fail when the engine tries to create the starting building. |
| **Also referenced at** | `Data/INI/CommandButton.ini` **line 9122** (`Boss_Command_ConstructChinaCommandCenter` → `Object = Boss_CommandCenter`) |
| **Related** | `Boss_ChinaCommandCenterCommandSet` exists in `CommandSet.ini` (line 5963), but the object itself does not. |

### CRASH 2 — Russia RS-24 science purchase targets missing object

| Field | Value |
|---|---|
| **Exact object name** | `Russia_RS24_Yars` |
| **File path** | `Data/INI/CommandButton.ini` (from `Specter_Data.zip`) |
| **Line number** | **12453** (`Object = Russia_RS24_Yars`) |
| **Button** | `Command_PurchaseScienceYars24` starts at **line 12450** |
| **Reason** | Button is on `SCIENCE_Russia_CommandSetRank1`. Object `Russia_RS24_Yars` does **not** exist. Only `Russia_RS24_Yars_AI` exists (`Data/INI/Object/Specter/Armed Forces Of Russian Federation/Wheeled/RS-24_Yars_AI.ini` line 11). Purchasing / resolving this science button can crash or fail object creation. |
| **Also referenced at** | `CommandButton.ini` **line 12638** (`Command_ConstructRussia_RS24_Yars`) |

### CRASH 3 — America upgrade definitions missing

| Field | Value |
|---|---|
| **Exact object name** | `Upgrade_AmericaSentryDroneGun` |
| **File path** | `Data/INI/CommandButton.ini` |
| **Line number** | **1386** (`Upgrade = Upgrade_AmericaSentryDroneGun`) |
| **Button** | `Command_UpgradeAmericaSentryDroneGun` at **line 1384** |
| **Reason** | No `Upgrade Upgrade_AmericaSentryDroneGun` definition in `Data/INI/Upgrade.ini` (or patch). `PLAYER_UPGRADE` button resolves a missing upgrade. |

| Field | Value |
|---|---|
| **Exact object name** | `Upgrade_AmericaDroneArmor` |
| **File path** | `Data/INI/CommandButton.ini` |
| **Line number** | **1405** |
| **Button** | `Command_UpgradeAmericaDroneArmor` at **line 1403** |
| **Reason** | Upgrade definition missing. Still referenced from `AmericaVehicle.ini` (`TriggeredBy` / `UpgradeCameo1`), so the upgrade ID is expected but never declared. |

| Field | Value |
|---|---|
| **Exact object name** | `Upgrade_AmericaTOWMissile` |
| **File path** | `Data/INI/CommandButton.ini` |
| **Line number** | **1461** |
| **Button** | `Command_UpgradeAmericaTOWMissile` at **line 1459** |
| **Reason** | Upgrade definition is **commented out** in `Data/INI/Upgrade.ini` **line 90** (`;Upgrade Upgrade_AmericaTOWMissile`). Button still active → missing upgrade on purchase. |

---

## 3. Skirmish faction selection results

| Side | Status | StartingBuilding | CommandSet | Air | Tank/Veh | Inf | Struct | Upgrades | Super/Sci | Missing objs |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| America | PASS* | AmericaCommandCenter | AmericaCommandCenterCommandSet | 15 | 39 | 15 | 17 | 16 | 17 | 0 |
| AmericaAirForceGeneral | PASS | AirF_AmericaCommandCenter | AirF_AmericaCommandCenterCommandSet | 10 | 25 | 13 | 13 | 7 | 21 | 0 |
| Boss | **CRASH** | Boss_CommandCenter | — | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Britain | PASS | Britain_MilitaryHQ | Britain_MilitaryHQCommandSet | 12 | 27 | 8 | 9 | 9 | 20 | 0 |
| China | PASS | ChinaCommandCenter | ChinaCommandCenterCommandSet | 10 | 32 | 14 | 12 | 3 | 14 | 0 |
| Egypt | PASS | Egypt_MilitaryHQ | Egypt_MilitaryHQCommandSet | 22 | 61 | 32 | 27 | 23 | 29 | 0 |
| France | PASS | France_MilitaryHQ | France_MilitaryHQCommandSet | 11 | 26 | 9 | 9 | 9 | 20 | 0 |
| GLA | PASS | GLACommandCenter | GLACommandCenterCommandSet | 11 | 32 | 15 | 12 | 8 | 18 | 0 |
| Germany | PASS | Germany_MilitaryHQ | Germany_MilitaryHQCommandSet | 12 | 27 | 8 | 9 | 9 | 18 | 0 |
| India | PASS | India_MilitaryHQ | India_MilitaryHQCommandSet | 21 | 60 | 31 | 27 | 23 | 32 | 0 |
| Iran | PASS | IranCommandCenter | IranHQCommandSet | 9 | 34 | 26 | 14 | 4 | 15 | 0 |
| Iraq | PASS | Iraq_CommandCenter | Iraq_CommandCenterCommandSet | 3 | 18 | 13 | 16 | 9 | 11 | 0 |
| Israel | PASS | Israel_MilitaryHQ | Israel_MilitaryHQCommandSet | 11 | 14 | 0† | 1 | 0 | 9 | 0 |
| Italy | PASS | Italy_MilitaryHQ | Italy_MilitaryHQCommandSet | 11 | 24 | 8 | 9 | 9 | 18 | 0 |
| Japan | PASS | Japan_MilitaryHQ | Japan_MilitaryHQCommandSet | 12 | 28 | 9 | 9 | 10 | 20 | 0 |
| Libya | PASS | Libya_MilitaryHQ | Libya_MilitaryHQCommandSet | 19 | 58 | 31 | 27 | 21 | 28 | 0 |
| Nato | PASS | NatoCommandCenter | NatoCommandCenterCommandSet | 12 | 28 | 11 | 14 | 5 | 10 | 0 |
| NorthKorea | PASS | NorthKorea_CommandCenter | NorthKorea_CommandCenterCommandSet | 2 | 17 | 13 | 16 | 9 | 12 | 0 |
| Pakistan | PASS | Pakistan_MilitaryHQ | Pakistan_MilitaryHQCommandSet | 21 | 61 | 32 | 27 | 23 | 31 | 0 |
| Russia | **CRASH** | RussiaCommandCenter | RussiaCommandCenterCommandSet | 15 | 40 | 23 | 13 | 6 | 13 | 1 |
| SaudiArabia | PASS | SaudiArabia_MilitaryHQ | SaudiArabia_MilitaryHQCommandSet | 21 | 60 | 32 | 27 | 23 | 29 | 0 |
| SouthAfrica | PASS | SouthAfrica_MilitaryHQ | SouthAfrica_MilitaryHQCommandSet | 19 | 58 | 31 | 27 | 21 | 28 | 0 |
| SouthKorea | PASS | SouthKorea_MilitaryHQ | SouthKorea_MilitaryHQCommandSet | 12 | 25 | 7 | 9 | 9 | 18 | 0 |
| Sweden | PASS | Sweden_MilitaryHQ | Sweden_MilitaryHQCommandSet | 10 | 23 | 7 | 9 | 9 | 18 | 0 |
| Syria | PASS | Syria_MilitaryHQ | Syria_MilitaryHQCommandSet | 19 | 58 | 32 | 27 | 22 | 29 | 0 |
| Taiwan | PASS | Taiwan_MilitaryHQ | Taiwan_MilitaryHQCommandSet | 6 | 19 | 7 | 9 | 9 | 18 | 0 |
| Turkey | PASS | Turkey_MilitaryHQ | Turkey_MilitaryHQCommandSet | 16 | 38 | 16 | 13 | 16 | 21 | 0 |
| UAE | PASS | UAE_MilitaryHQ | UAE_MilitaryHQCommandSet | 20 | 60 | 32 | 27 | 23 | 29 | 0 |
| UN | PASS | UN_MilitaryHQ | UN_MilitaryHQCommandSet | 11 | 24 | 7 | 9 | 9 | 18 | 0 |
| Ukraine | PASS | Ukraine_MilitaryHQ | Ukraine_MilitaryHQCommandSet | 20 | 60 | 32 | 27 | 23 | 30 | 0 |
| Vietnam | PASS | Vietnam_MilitaryHQ | Vietnam_MilitaryHQCommandSet | 19 | 58 | 31 | 27 | 22 | 29 | 0 |

\* America HQ/unit graph loads; upgrade buttons in Crash 3 still unresolved.  
† Israel walk reached aircraft/vehicles from HQ + Advanced Air Base; no `KindOf` INFANTRY hits in depth-2 simulation (not flagged as missing object).

**Summary:** 31 playable templates · **29 PASS** · **2 CRASH** (Boss spawn, Russia RS-24 object) · **5** total predicted crash records including America upgrades.

---

## 4. Command Centers

- **59** Command Center / Military HQ objects indexed in patch + stock.
- **All 59** have a resolvable `CommandSet` in text INI.
- Patch faction HQs (`*_MilitaryHQ`) load their first construct rows and recurse into Barracks / War Factory / Air Base / MIC production sets without missing construct targets in this simulation.

---

## 5. Category checks (aircraft / tanks / infantry / upgrades / super weapons)

| Check | Result |
|---|---|
| First buildable from HQ/CC | Resolved for all PASS factions (construct buttons → existing Objects) |
| Aircraft | Present for all PASS factions (counts in table) |
| Tanks / vehicles | Present for all PASS factions |
| Infantry | Present for all PASS factions except Israel depth-2 note above |
| Upgrades | Resolved except America trio in Crash 3 |
| Super weapons / sciences | Shortcut + science bars walked; **Russia `Russia_RS24_Yars`** fails (Crash 2) |

---

## 6. What was not run

- No in-engine skirmish click-through (no Windows binary / Wine).
- No map load, pathfinding, or model/W3D crash detection.
- Stock buttons/objects that exist only inside opaque `.big` payloads (if any) were not binary-scanned beyond the Specter_Data INI extract.

---

## 7. Next step (not done)

Per instructions: **do not auto-fix**. Suggested fixes when authorized:

1. Define `Object Boss_CommandCenter` (or retarget Boss `StartingBuilding` / construct button to an existing Boss/China CC object and matching CommandSet).
2. Add `Object Russia_RS24_Yars` or retarget science/construct buttons to `Russia_RS24_Yars_AI` / a real player object.
3. Uncomment or restore `Upgrade_AmericaTOWMissile`, and add missing `Upgrade_AmericaSentryDroneGun` / `Upgrade_AmericaDroneArmor` definitions (or remove the buttons).
