# FINAL_RUNTIME_FIX_REPORT

**Status:** PASS — runtime crash sources from `CRASH_RUNTIME_REPORT.md` fixed (overlay only).  
**Auto-fix:** Applied under `patch/` only (vendor archives untouched).  
**sync_audit.py:** **PASS** (errors=0; vendor `Data.zip` warn only).  
**Package:** `patch/Release/FINAL_RUNTIME_FIX_PATCH.zip`  
**SHA256:** `ba5ffbe202960de8207aa13ff61a592a71b1bb61d2e5dd11906ac65534dfa454`  
**Date:** 2026-07-23

---

## Rules followed

- Did **not** delete units, factions, aircraft, tanks, or buildings.
- Did **not** remove features (Boss army retained; Russia RS-24 retained; America upgrades restored).
- Fixed broken references / wrong Object names / missing Upgrades / missing CommandSet wiring via **additive patch INI**.

---

## Crash → root cause → fix

### 1. `Boss_CommandCenter` (skirmish enter)

| | |
|---|---|
| **Reported** | `PlayerTemplate.ini:276` `StartingBuilding = Boss_CommandCenter` |
| **Root cause** | Specter ships Boss `PlayerTemplate` / `CommandButton` / `CommandSet` entries, but **no `Object Boss_*` definitions** in loose INI (vanilla ZH kept Boss objects in packaged data). Starting unit `Boss_VehicleDozer` was also undefined. |
| **Fix** | Added `Boss_Faction_Objects.ini` with **37** `Boss_*` objects (Side=`Boss`), aliasing existing Specter units/buildings and wiring Boss CommandSets where they exist. |
| **Key mappings** | `Boss_CommandCenter` ← `ChinaCommandCenter` + `Boss_ChinaCommandCenterCommandSet`; `Boss_VehicleDozer` ← `ChinaVehicleDozer` + `Boss_AmericaDozerCommandSet`; remaining Boss build/train list objects similarly aliased (MIG→`ChinaJetJ10C`, Helix→`ChinaHelicopterZ18A`, Overlord→`ChinaTankBattleMaster`, Nuke silo→`ChinaDF5NuclearMissileSilo`, etc.). |

### 2. `Russia_RS24_Yars` (science / construct)

| | |
|---|---|
| **Reported** | `CommandButton.ini:12453` `Object = Russia_RS24_Yars` |
| **Root cause** | **Wrong Object name.** Player unit is already defined as `RussiaVehicleRS24` in `RS-24_Yars.ini`. Buttons/science used `Russia_RS24_Yars`; only `Russia_RS24_Yars_AI` existed under that naming family. |
| **Fix** | (a) Overlay `CommandButton_RuntimeFix_RussiaRS24.ini` retargets `Command_PurchaseScienceYars24` and `Command_ConstructRussia_RS24_Yars` → `RussiaVehicleRS24`. (b) Alias object `Russia_RS24_Yars` (= copy of `RussiaVehicleRS24`, Side=`Russia`) so any leftover refs still resolve. **Unit kept.** |

### 3. America upgrades missing

| Upgrade | Root cause | Fix |
|---|---|---|
| `Upgrade_AmericaSentryDroneGun` | Button exists; Upgrade block never defined | Added in `Upgrade_RuntimeFix_America.ini` (PLAYER) |
| `Upgrade_AmericaDroneArmor` | Button + `AmericaVehicle` `TriggeredBy` refs; Upgrade never defined | Added (PLAYER) |
| `Upgrade_AmericaTOWMissile` | Button active; stock `Upgrade.ini` definition **commented out** | Restored active PLAYER upgrade in patch |

---

## Files in FINAL_RUNTIME_FIX_PATCH

```
Data/INI/CommandButton_RuntimeFix_RussiaRS24.ini
Data/INI/Upgrade_RuntimeFix_America.ini
Data/INI/Object/Specter/PatchSystems/RuntimeFix/Boss_Faction_Objects.ini
Data/INI/Object/Specter/PatchSystems/RuntimeFix/Russia_RS24_Yars_Alias.ini
INSTALL_ORDER.txt
CHANGED_RUNTIME_FIX_FILES.txt
```

Plain folder: `patch/Release/FINAL_RUNTIME_FIX_PATCH_Data/`  
List: `patch/Release/CHANGED_RUNTIME_FIX_FILES.txt`

---

## Verification

| Check | Result |
|---|---|
| `Boss_CommandCenter` / `Boss_VehicleDozer` defined | Yes |
| All 37 referenced `Boss_*` construct/train objects defined | Yes |
| `RussiaVehicleRS24` button targets + `Russia_RS24_Yars` alias | Yes |
| Three America upgrades defined | Yes |
| Countries / aircraft / tanks / buildings removed | **No** |
| `python3 patch/tools/economy/sync_audit.py` | **PASS** (0 errors) |
| `generate_sync_manifest.py` | Regenerated `patch/SYNC_MANIFEST.sha256` |

---

## Notes

- Live Generals ZH still cannot be launched in this Linux environment; validation is static (object/upgrade presence + sync audit) on top of the prior skirmish load simulation.
- Boss aliases use Specter-modern stand-ins where classic ZH names (`ChinaJetMIG`, `ChinaVehicleHelix`, `ChinaTankOverlord`) are absent from Specter INI — features remain buildable under Boss CommandSets.
- `PatchBaseCost` markers applied via `apply_country_balance.py` for sync idempotency.
