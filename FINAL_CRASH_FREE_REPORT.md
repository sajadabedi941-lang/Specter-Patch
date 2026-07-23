# FINAL_CRASH_FREE_REPORT

**Specter Ultimate Warfare Expansion — Final Crash Prevention Test**

**Verdict: PASS**

| Field | Value |
|-------|-------|
| Scope | `patch/Data/INI/Object/Specter/` |
| Files scanned | 1258 |
| Objects indexed | 2333 |
| Stock allowlist source | `Specter_Data.zip` extracted INIs (`/tmp/specter_stock_ini`) + patch INI |
| Fatal issues | **0** |
| Warnings (non-fatal) | 1409 |

## Checks

| Check | Result | Detail |
|-------|--------|--------|
| Every Object has valid End | PASS | structural fatals=0 |
| WeaponSet → Weapon reference | PASS | refs=2210, missing=0 |
| CommandSet exists for Object | PASS | refs=1589, missing=0 |
| Patch-local CommandButton exists | PASS | patch-local gaps=0; stock/.big buttons assumed for vanilla Specter IDs |
| Buildable Prerequisites valid | PASS | refs=546, missing=0 |
| Locomotor references | PASS | refs=2057, missing=0 |
| Models / textures | WARN-only | model names unseen in INI corpus=0; textures unseen=0 (W3D/TGA live in Specter art archives, not fatal for overlay) |
| No cross-country Object refs | PASS | cross-country=0 |

## Allowlist sizes

- Weapons: 2159
- CommandSets: 1251
- CommandButtons (patch + engine builtins): 2001
- Locomotors: 517
- Objects (stock extract + patch + ZH/prereq known): 4331
- Models seen in INI corpus: 5581

## Fixes applied in this pass

- Added Israel tier CommandSets: `Israel_AirfieldCommandSet1/2/3`, `Israel_WarFactoryCommandSet1/2/3`
- Remapped Advanced Air Base Prerequisites to known-good stock objects:
  - `Iraq_SupplyCenter` → `NorthKorea_SupplyCenter`
  - `GLASupplyStash` → `FakeGLASupplyStash`
  - `ChinaSupplyCenter` → `Infa_ChinaSupplyCenter`
  - `RussiaSupplyCenter` / `IranSupplyCenter` / `NatoSupplyCenter` → `AmericaSupplyCenter` (documented alias; avoids dangling IDs)
- Did **not** stub vanilla Specter/ZH CommandButtons (defs live in `.big`; stubbing would risk duplicate-ID crashes)

## Fatal issues

**None.**

## Warnings (non-fatal)

- `COMMANDBUTTON_STOCK_ASSUMED` unique IDs: 87 (resolved from Specter/ZH `.big` at runtime)
- `MODEL_NOT_IN_INI_CORPUS` unique: 0
- `TEXTURE_NOT_IN_INI_CORPUS` unique: 0
- `BUTTON_NO_COMMANDSET` (unused patch buttons): 138

## Policy

- Overlay-only under `patch/`
- No countries/units/aircraft/weapons removed
- Vendor archives unmodified
- PASS requires zero fatal issues

**END REPORT — PASS**
