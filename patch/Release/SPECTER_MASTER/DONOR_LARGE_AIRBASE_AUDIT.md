# Donor Large Airbase — Factual Audit Report

**Date:** 2026-08-16  
**Branch:** `cursor/egypt-playable-faction-4b13` (patch work preserved; not reverted)  
**Scope:** Audit only. **No Egypt / Pakistan / other-faction / BIG rebuild changes in this step.**

---

## 0. Multipart archive verification

| Step | Result |
|------|--------|
| `git fetch --all --prune` | OK |
| `origin/main` parts `DONOR_Art.part001.rar` … `DONOR_Art.part069.rar` | **69 / 69** (complete; none missing) |
| Local access without touching feature-branch work | `git archive origin/main` → `/tmp/donor_art_rar/` |
| Extract | `unrar x DONOR_Art.part001.rar` only → `/tmp/donor_art_extract/` (All OK) |
| Extracted inventory | `Art/w3d` **12161** W3D; `Art/Textures` **10883** textures (~3.6G) |

Feature branch Specter patch work was **not** overwritten or reverted.

---

## 1. Egypt current baseline (do not change yet)

| Field | Value |
|-------|--------|
| Object | `Egypt_Airfield_T` |
| Source INI | `Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_Airfield_T.ini` |
| W3D | `Irq_Airfield` (in SPEC ART; **not** in DONOR_Art multipart) |
| Parking | **NumRows=1 × NumCols=4 → 4 aircraft** |
| Bones | Runway1–4 Parking/ParkHan/Prep + Start/End; HeliPark01 |
| Geometry | BOX Major **142.0** × Minor **90.0** × Height 25 |
| Verdict | Current small/standard Egypt airfield |

`Egypt_AdvancedAirBase` is disabled stub (comment-only).  
Prior wrong patch `Egypt_LargeAirBase` / `US_AirField` (6-slot) remains **rejected** — not the donor “large runway” target.

---

## 2. Named donor DATA candidate: `AmericaLargeAirfield`

| Field | Value |
|-------|--------|
| Object | `AmericaLargeAirfield` |
| Source INI | TEOD `Data\INI\Object\FactionBuilding.ini` (full dump: `/tmp/teod_donor/AmericaLargeAirfield_FULL.ini`) |
| Primary W3D family | **`ABArFrcCmd2`** (+ `_D/_E/_S/_DS/_ES`, `_A7`, `_A8`) |
| Shared anim W3Ds | `ABArFrcCmd_A4*`, `_A5*`, `_A6*`, `_A9`, `_AB*` |
| Parking | **NumRows=2 × NumCols=1 → 2 aircraft** |
| Bones | Runway1 only: Parking1–2, ParkHan, Prep1–2, Start1, End1 (**no Runway2**) |
| Geometry | Major **112.0** × Minor **74.0** |
| Prerequisite | `TacticalStrategyCenter` |
| UI | `CONTROLBAR:ConstructLargeAirfield` / `Russia_LargeAirfieldCommandSet` |

### ART completeness (DONOR_Art extract + TEOD_W3D.big + SPEC ART)

| Asset | Present? |
|-------|----------|
| `ABArFrcCmd2.W3D` and all `ABArFrcCmd2_*` variants | **MISSING everywhere** |
| Shared `ABArFrcCmd_A4/A5/A6/A9/AB*` | Present in DONOR_Art |
| Dedicated `ABArFrcCmd2` textures | Unknown / none attributable (mesh absent) |

### Comparison vs Egypt

| Metric | Egypt | AmericaLargeAirfield |
|--------|-------|----------------------|
| Capacity | **4** | **2** (smaller) |
| Footprint (Major×Minor) | **142×90** | **112×74** (smaller) |
| Dual runway bones | 4 starts | 1 start |

**Verdict: NOT importable.** Named “Large” in TEOD DATA, but mesh family **`ABArFrcCmd2` is absent** from the complete 69-part donor ART. Even if meshes appeared, INI capacity/footprint are **not larger** than Egypt’s current airfield. **No fake Scale / NumRows / substituted W3D.**

---

## 3. Related TEOD airfield objects (full chain checked)

### 3a. `AmericaAirfield` (TEOD USA — **not** Specter `US_AirField`)

| Field | Value |
|-------|--------|
| Object | `AmericaAirfield` |
| Source | TEOD `Data\INI\Object\USA\Structures\Airfield.ini` |
| W3D family | **`ABArFrcCmd`** (33 models referenced) |
| Parking | **2×2 = 4** |
| Bones | Dual runway (Runway1–2 Parking/Prep/Start/End) + HeliPark01 |
| Geometry | **140×85** |
| ART in DONOR_Art | **Complete** — all 33 W3Ds present; base textures resolve (`.tga` → `.dds` OK) |

**Verdict:** Genuine complete normal USA airfield asset set. Capacity **equals** Egypt (4), footprint **slightly smaller** than Egypt. **Not a “large” upgrade.**

### 3b. `Russia_LAirF` (TEOD “large” Russia airfield)

| Field | Value |
|-------|--------|
| Object | `Russia_LAirF` |
| Source | TEOD `Data\INI\Object\Russia\Structures\Airfields.ini` |
| W3D family | **`RU-LAirfield`** (+ `_D/_E/_S/_DS/_ES`, `D1`, `D2`, shared `RU-Airfield_A4/A6`) |
| Parking | **2×1 = 2** |
| Geometry | **132×52** |
| ART | **`RU-LAirfield*` MISSING** from DONOR_Art; also **0** hits in `!TEOD_W3D.big` (only normal `RU-Airfield*` exists there) |

**Verdict: INCOMPLETE.** Cannot import.

### 3c. `Russia_AirF` / `ChinaAirfield` / `GLAAirfield`

| Object | Model | Cap | Geom | DONOR_Art |
|--------|-------|-----|------|-----------|
| `Russia_AirF` | `RU-Airfield` | 2×2=4 | 122×63 | Not in DONOR_Art (in TEOD_W3D) |
| `ChinaAirfield` | `NBAirfield` | 2×2=4 | 83×76 | Complete family in DONOR_Art |
| `GLAAirfield` | `GLA-Airfield` | 2×1=2 | 102×36 | In TEOD_W3D, not DONOR_Art |

None are larger than Egypt in capacity or footprint.

### 3d. `AmericaAircraftCarrier`

Naval carrier (`PSAirCarrier*`), not a land airbase. Out of scope for Egypt airfield replacement.

---

## 4. Orphan ART meshes (bones only — **no Object INI**)

Searched TEOD INI + SPEC DATA for `TheAirPort`, `HXUSABigAirPort`, `HXBigAir`, `HXNewBigAir`: **0 object definitions.**

| W3D | Parking-like bones | Textures | Damage/night/rubble family | DATA Object |
|-----|--------------------|----------|----------------------------|-------------|
| `TheAirPort.W3D` | Runway1–4 × Parking1–5 (**20** park slots worth) | `CJJCWUJUN` (dds present) | **None** (single file) | **None** |
| `HXUSABigAirPort.W3D` | Dual RW × Parking1–3 (**6**) | `CJJCWUJUN` | **None** | **None** |
| `HXNewBigAir.W3D` | Dual RW × 2 park | `GSJCTT` | **None** | **None** |
| `HXBigAir.W3D` | Single RW × 3 park | `GSJCTT` | **None** | **None** |

**Verdict:** Interesting meshes, but **not a genuine complete airbase asset set**. Wiring them would require inventing Object/Draw/Parking INI and fabricating missing `_D/_E/_S` variants — **forbidden by task rules.**

Civilian `CBAirport` / `CBAIRPORT2` families exist with full damage variants but are **non-faction civilian airports** (no ParkingPlaceBehavior / runway production bones in TEOD Object defs).

---

## 5. AIRNGR

`AIRNGR*` / `AIRNGRL_SKN` in DONOR_Art are **infantry skin/anim** assets, not airbase buildings. **Do not treat as airfield.**

---

## 6. Specter in-tree 6-slot airfields (context only — not donor large-runway)

Already in SPEC ART/DATA (not from DONOR_Art multipart):

| Object examples | Model | Cap |
|-----------------|-------|-----|
| Specter `AmericaAirfield` / `NatoAirfield` | `US_AirField` | 1×6=6 |
| `RussiaAirfield` / `ChinaAirfield` / `ArabicArmy_Airfield` | faction skins | 1×6=6 |
| `IranAirfield` | `iran_airfield` | 3×2=6 |

`US_AirField` mesh has 6 parking + 6 starts; **smaller geometry (112×74) than Egypt**. Previously proposed as `Egypt_LargeAirBase` and **explicitly rejected** as not the donor large runway.

---

## 7. Candidate scorecard

| # | Candidate | Object→W3D chain | All W3Ds | Textures | Variants | Cap vs Egypt | Footprint vs Egypt | Genuine large? | Importable now? |
|---|-----------|------------------|----------|---------|----------|--------------|--------------------|----------------|-----------------|
| A | `AmericaLargeAirfield` / `ABArFrcCmd2` | Yes (TEOD) | **No** | N/A | **No** | **2 < 4** | Smaller | Name only; mesh missing | **No** |
| B | TEOD `AmericaAirfield` / `ABArFrcCmd` | Yes | Yes | Yes | Yes | 4 = 4 | Slightly smaller | No (standard) | Complete but **not larger** |
| C | `Russia_LAirF` / `RU-LAirfield` | Yes (TEOD) | **No** | N/A | **No** | 2 < 4 | Smaller | Incomplete | **No** |
| D | `NBAirfield` / China | Yes | Yes | Yes | Yes | 4 = 4 | Smaller | No | Not larger |
| E | `TheAirPort` / `HXUSABig*` | **No INI** | Partial single mesh | Partial | **No** | Unknown (no INI) | Unknown | Orphan ART | **No** |
| F | Specter `US_AirField` | Yes (SPEC) | In SPEC ART | In SPEC | Minimal/single model | 6 > 4 | Smaller box | More slots, not donor large runway | Rejected by prior order |

---

## 8. Best genuine large airbase — conclusion

**No confirmed complete donor asset set qualifies as a genuine large airbase upgrade over Egypt’s current `Irq_Airfield` (4-slot, 142×90).**

- The DATA name that matched prior investigation (`AmericaLargeAirfield` → `ABArFrcCmd2`) is a **hard ART blocker**: primary W3D family absent from the full 69-part DONOR_Art (and from TEOD_W3D / SPEC ART).
- That same object is also **smaller in parking and footprint** than Egypt’s current airfield — so even a complete mesh drop would not meet “genuinely larger” without separate evidence of a longer heavy-aircraft strip (unverifiable without the mesh).
- The only **complete** donor USA airfield family in ART+DATA is **`ABArFrcCmd` / TEOD `AmericaAirfield`**, which is a **standard 4-slot** airfield, not a large upgrade.
- High-bone orphan meshes (`TheAirPort`, `HXUSABigAirPort`) are **not** backed by Object definitions or construction/damage variants.

**Egypt must not be modified until a complete verified set exists.**

---

## 9. Egypt-only integration plan (blocked — provisional)

*Do not execute until blocker cleared. Pakistan and all other factions remain untouched. Do not rebuild master BIGs until verified.*

### Blocker to clear (required before any Egypt edit)

1. Obtain and verify the missing **`ABArFrcCmd2*.W3D`** set (at minimum: base, `_D`, `_E`, `_S`, `_DS`, `_ES`, `_A7`, `_A8`) **or** supply a different donor Object whose full Draw→W3D→texture→variant chain exists and is factually larger than Egypt.
2. Re-run this audit’s completeness matrix (exact filenames only; no guesses).
3. Confirm parking bones in mesh match INI `ExtraPublicBone` / `NumRows`×`NumCols` with no invented capacity.

### If / when a complete larger set is confirmed (Egypt-only)

1. **DATA only first (preferred if ART already in SPEC):** clone Egypt builder button/CommandSet from `Egypt_Airfield_T` → new Egypt object; keep Egypt aircraft roster / CommandSet production list; remap Draw modules to verified donor models; set ParkingPlaceBehavior from donor INI facts only.
2. **ART:** import only missing W3Ds/textures into ART workspace; do not touch other factions’ airfield models.
3. **Dozer / ControlBar:** Egypt construct button only; no Pakistan/Iran/Israel/Iraq/NK/USA/Russia/China CommandSet changes.
4. **Verify:** Egypt builds larger airfield; other factions’ airfield objects/hashes unchanged; parking/taxi bones work in-game.
5. **Packaging rule:** rebuild and ZIP **only** `_SPEC_DATA_ONE.big` and/or `_SPEC_ART_ONE.big` that actually changed — never the whole mod.

### Explicit non-actions

- No Scale hacks, no fake NumRows/NumCols, no substituting `US_AirField` / `Irq_Airfield` / `AIRNGR` / unrelated W3Ds.
- No inventing INI for `TheAirPort` / `HXUSABigAirPort` without a real donor Object definition and full variant set.
- No master BIG rebuild in this audit turn.

---

## 10. Artifact locations (local VM)

| Item | Path |
|------|------|
| RAR parts (from origin/main) | `/tmp/donor_art_rar/DONOR_Art.part*.rar` |
| Extracted donor ART | `/tmp/donor_art_extract/Art/{w3d,Textures}` |
| TEOD DATA BIG | `/tmp/teod_donor/!TEOD_INI.big` |
| AmericaLargeAirfield dump | `/tmp/teod_donor/AmericaLargeAirfield_FULL.ini` |
| Russia L/normal airfield dumps | `/tmp/teod_donor/Russia_LAirF.ini`, `Russia_AirF.ini` |
