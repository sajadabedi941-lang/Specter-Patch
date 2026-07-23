# FULL_INI_INTEGRITY_REPORT

**Specter Ultimate Warfare Expansion — Full INI Integrity Repair**

**Date:** 2026-07-23 05:03 UTC  
**Scope:** `patch/Data/INI/Object/Specter/` (all countries + PatchSystems)  
**Verdict: PASS** (0 fatal issues remaining)

---

## Policy

- Scanned **all** Object INIs under Specter (not a single unit)
- All countries and units preserved (no deletions)
- Overlay-only repairs; original Specter archives untouched
- Stock allowlists loaded from `Specter_Data.zip` extracted INIs + patch INI

---

## Scan coverage

| Check | Result |
|-------|--------|
| INI parsing / block End balance | PASS |
| Duplicate Object names | PASS (0) |
| Duplicate ModuleTags within Objects | PASS (0) |
| Missing ModuleTags on Draw/Behavior/Body | PASS (0) |
| WeaponSet → Weapon references | PASS |
| CommandSet references | PASS |
| Empty CommandSet assignments | **FIXED** then PASS |
| Prerequisites Object refs | PASS |
| Multi-object Prerequisite lines (parser-invalid) | **FIXED** then PASS |
| Cross-country Object Prerequisites | PASS (0) |
| Cross-faction Upgrade TriggeredBy | PASS (0) |
| Side= mismatches (faction-prefixed objects) | PASS (0) |
| Locomotor references | PASS |
| Broken Draw/Behavior structure | PASS |

---

## Issues found and fixed in this repair

### 1. Empty `CommandSet =` (commented-out value) — 11 files
PowerPlant buildings had `CommandSet = ;Iraq_DroneCenterCommandSet` which the ZH parser treats as an empty CommandSet.

**Fix:** Assign `{Side}_PowerPlantCommandSet` for each faction PowerPlant.

### 2. Invalid multi-name Prerequisite lines — 40+ sites
Lines like `Object = AmericaAirfield AmericaAirfield_T` or `Object = IraqMilitaryAirfield Egypt_Airfield_T` are invalid (one Object per Prerequisite line) and/or cross-faction.

**Fix:** Collapse to a single faction-local building (`{Side}_AdvancedAirBase`, `{Side}_WarFactory_T`, `{Side}_MIC`, etc.).

### 3. Missing Science stubs — 3
`SCIENCE_BritainStealthJet`, `SCIENCE_JapanStealthJet`, `SCIENCE_UAEStealthJet` referenced but not defined in patch/stock INI extract.

**Fix:** Added `patch/Data/INI/Science_FullIntegrityFixes.ini`.

---

## Repair statistics

| Metric | Count |
|--------|-------|
| Specter Object INI files scanned | 1258 |
| Object definitions indexed | 2333 |
| Files modified in this repair | 39 |
| Files newly added in this repair | 1 |
| `FULL-INI-REPAIR` markers written | 67 |
| Fatal issues remaining | **0** |

---

## Modified / new files (this clean repair patch)

### New
- `patch/Data/INI/Science_FullIntegrityFixes.ini`

### Modified
- `patch/Data/INI/Object/Specter/Egyptian Armed Forces/Airforce/Egypt_Mig29M2.ini`
- `patch/Data/INI/Object/Specter/Egyptian Armed Forces/Airforce/Egypt_Rafale.ini`
- `patch/Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_MIC.ini`
- `patch/Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_MIC.ini`
- `patch/Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Israel Defense Forces/Buildings/Israel_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Israel Defense Forces/Buildings/Israel_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_MIC.ini`
- `patch/Data/INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_MIC.ini`
- `patch/Data/INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_MIC.ini`
- `patch/Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_RadarStation.ini`
- `patch/Data/INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_MIC.ini`
- `patch/Data/INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_MIC.ini`
- `patch/Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_Akinci.ini`
- `patch/Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_F16Block70.ini`
- `patch/Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_F16V.ini`
- `patch/Data/INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_MIC.ini`
- `patch/Data/INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_MIC.ini`
- `patch/Data/INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_RadarStation.ini`
- `patch/Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_MIC.ini`
- `patch/Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_RadarStation.ini`
- `patch/Data/INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_MIC.ini`
- `patch/Data/INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_PowerPlant.ini`
- `patch/Data/INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_RadarStation.ini`

---

## Package

`patch/Release/Specter_INI_REPAIR_PATCH.zip`

Contains **only** the fixed/new `Data/INI` overlay files from this repair (no vendor archives, no unchanged stock).

**Install:** extract and merge `Data/` into `<GameRoot>/Data/`.

---

## Verification

- Post-repair integrity scan: **0 fatals**
- `sync_audit.py`: **PASS**

**END REPORT — PASS**
