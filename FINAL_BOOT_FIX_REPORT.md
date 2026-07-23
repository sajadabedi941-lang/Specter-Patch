# FINAL_BOOT_FIX_REPORT

**Goal:** Zero INI parse errors before main menu.  
**Scope:** Complete validation + boot cleanup under `patch/Data/INI/Object/Specter/` (1260 INIs).  
**Policy:** No countries, units, aircraft, tanks, buildings, or upgrades removed. Overlay-only definition fixes.  
**Date:** 2026-07-23

---

## Root cause of endless INI parse errors

Eleven faction PowerPlant files contained:

```ini
CommandSet = ;Iraq_DroneCenterCommandSet
```

In Generals ZH, `;` starts a comment, so the **CommandSet value is empty**. Structure load then fails CommandSet lookup and cascades into endless parse/lookup errors before the main menu.

Also fixed **47** multi-object `Prerequisites` lines (`Object = A B …`). ZH expects a **single** prerequisite object token.

---

## Fixes applied (58 actions / 40 files)

### 1. Empty CommandSet → faction PowerPlantCommandSet (11)

| Object | Fixed CommandSet |
|---|---|
| UAE_PowerPlant | UAE_PowerPlantCommandSet |
| Syria_PowerPlant | Syria_PowerPlantCommandSet |
| India_PowerPlant | India_PowerPlantCommandSet |
| SouthAfrica_PowerPlant | SouthAfrica_PowerPlantCommandSet |
| Egypt_PowerPlant | Egypt_PowerPlantCommandSet |
| Israel_PowerPlant | Israel_PowerPlantCommandSet |
| Libya_PowerPlant | Libya_PowerPlantCommandSet |
| Pakistan_PowerPlant | Pakistan_PowerPlantCommandSet |
| SaudiArabia_PowerPlant | SaudiArabia_PowerPlantCommandSet |
| Ukraine_PowerPlant | Ukraine_PowerPlantCommandSet |
| Vietnam_PowerPlant | Vietnam_PowerPlantCommandSet |

### 2. Multi-object Prerequisites → single valid Object= (47)

- Faction MIC / RadarStation / Air units: prefer local `*_Airfield_T`, `*_WarFactory_T`, `*_AdvancedAirBase`
- Boss_* units: map to `Boss_WarFactory` / `Boss_Barracks` / `Boss_CommandCenter`
- Turkey F-16 / Akıncı and Egypt Rafale / MiG-29M2: faction-local AdvancedAirBase

---

## Validation

| Check | Result |
|---|---|
| Scan all `Object/Specter/**/*.ini` | 1260 files / 2371 objects |
| Invalid Object names | 0 |
| Duplicate Object definitions (patch) | 0 |
| Broken `from` inheritance | 0 |
| Missing / extra `End` (Object End-stack) | **0** |
| Empty critical fields (`CommandSet`/`Side`/…) | **0** |
| Multi-token Prerequisites | **0** |
| Startup load-order simulation (1437 patch INIs, sorted) | Object/Specter **PASS** |
| `python3 patch/tools/economy/sync_audit.py` | **PASS** (0 errors) |

---

## Package

- **`patch/Release/FINAL_BOOT_FIX_PATCH.zip`**
- Plain: `patch/Release/FINAL_BOOT_FIX_PATCH_Data/`
- Tool: `patch/tools/boot_cleanup.py` (re-runnable)

**SHA256:** `dc00f345f65f21785def104f3aadfc7848379378e2cbdab982ec54b2fb0f4adc`

### Install

1. Install Specter + Ultimate Warfare overlay.  
2. Merge this patch `Data/INI` on top.  
3. Do not modify vendor archives.

---

## BOOT CLEANUP: PASS

Zero Object/Specter parse fatals remaining. Empty CommandSet boot cascade eliminated.
