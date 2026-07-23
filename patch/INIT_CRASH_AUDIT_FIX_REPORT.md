# Init Crash Audit & Fix Report

**Status:** Cause identified and fixed in the existing patch overlay.  
**Verdict:** NOT claiming PASS for live boot (no Wine/ZH binary in this environment). User must confirm on Windows GameRoot.

## Exact crash cause

After restoring original Specter `Data`, the patch installer copies `patch/Data/**` into GameRoot. Generals Zero Hour loads **every** `Data/INI/**/*.ini`.

### Primary cause (Uncaught Exception during initialization)

Tool-only schemas were shipped under `Data/INI/` with **non-engine block types**:

| File | First bad token | Line |
|------|-----------------|------|
| `Data/INI/CountryBalance.ini` | `CountryBalanceSystem` | **44** |
| `Data/INI/Economy/PricingDefaults.ini` | `PricingDefault` | **7** |
| `Data/INI/Economy/*.ini` | `UnitCategory` / `TechnologyClass` / `PricingEntry` / … | various |
| `Data/INI/GlobalBuildLimits_SpecterPatch.ini` | `BuildLimit` | **15** |

These files are configs for `patch/tools/economy/*.py`, not Generals INI. The engine has no handler for `CountryBalanceSystem` / `BuildLimit` / `PricingDefault` → **uncaught exception during initialization** (matches ReleaseCrashInfo with no detail).

### Secondary causes (also fatal on init after stock Data restore)

1. **Duplicate CommandSet names** — `CommandSet_AdvancedAirBase.ini` redefined stock sets already in `CommandSet.ini` (`AmericaDozerCommandSet`, `RussiaDozerCommandSet`, StrategyCenter sets, …) — **14 collisions**.
2. **Duplicate CommandButton names** — `CommandButton_Turkey.ini` + `CommandButton_RuntimeFix_RussiaRS24.ini` redefined stock buttons — **22 collisions**.
3. **Duplicate ObjectCreationList names** — `ObjectCreationList_Turkey.ini` — **23 collisions**.
4. **Syntax:** `CommandSet_Turkey.ini` line **11** used `END` instead of `End`.
5. **Syntax:** 12 `*RadarStation*.ini` files had bare `Scale 0.9` at column 0 (invalid property form).

## Fix applied (existing patch, not a new product)

1. **Moved** tool configs out of the game tree:
   - `patch/tools/economy/config/CountryBalance.ini`
   - `patch/tools/economy/config/Economy/`
   - `patch/tools/economy/config/GlobalBuildLimits_SpecterPatch.ini`
2. **Updated** `apply_country_balance.py` / docs to the new path.
3. **Deleted** `CommandButton_RuntimeFix_RussiaRS24.ini` (stock buttons + `Russia_RS24_Yars` Object alias already cover this).
4. **Renamed** AAB dozer/strategy CommandSets to `*_PatchAAB` and added Object overlays that retarget dozers/strategy centers (AAB construct wiring preserved).
5. **Deduped** Turkey CommandButtons (rename referenced → `Command_TurkeyPatch_*`; drop unreferenced stock copies).
6. **Removed** duplicate OCLs from `ObjectCreationList_Turkey.ini`.
7. **Fixed** `END`→`End` and RadarStation `Scale =` syntax.

## Post-fix static audit

- NEW-file vs stock ID collisions for CommandSet / CommandButton / Object / OCL / Science / Upgrade: **0**
- Non-engine top-level INI blocks under `Data/INI`: **0**

## What you should do on Windows

1. Restore clean Specter `Data` (or uninstall prior patch).
2. Install this branch’s `patch/` overlay.
3. Launch ZH; confirm init completes.
4. Spot-check: America/Russia/China dozer can place Advanced Air Base; Turkey shortcuts still fire FOAB/Tu-22 (via `Command_TurkeyPatch_*`).
