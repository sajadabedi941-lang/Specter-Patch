# Orphan Large Airport Mesh Audit (Direct W3D Inspection)

**Date:** 2026-08-16  
**Scope:** Audit only — **no Egypt / Pakistan / faction / BIG changes**  
**Method:** Westwood W3D chunk parse (MSB size flag, payload-after-header), pivot structs (60 bytes), mesh header + vertex bboxes, texture chunk + donor resolve.

---

## Sources searched

| Source | TheAirPort / HXUSABigAirPort |
|--------|------------------------------|
| DONOR_Art extract (`/tmp/donor_art_extract/Art/w3d`) | **Present** |
| W3DZH.big (`/tmp/zh_art`) | Absent |
| !TEOD_W3D.big / !TEOD_Textures.big | Absent |
| SPEC `_SPEC_ART_ONE.big` | Absent |
| TexturesZH.big / W3DEnglishZH.big / OOPMBeta | **Not present** in workspace |
| TEOD / SPEC INI Object defs | **Zero** hits for exact names |

Sibling HX airport package in DONOR_Art only: `HXBigAir.W3D`, `HXNewBigAir.W3D`, `HXUSABigAirPort.W3D` (no `*_D`/`*_E` siblings).

---

## Direct W3D facts

### TheAirPort.W3D

| Field | Value |
|-------|--------|
| Path | `/tmp/donor_art_extract/Art/w3d/TheAirPort.W3D` |
| Size | **58603** bytes |
| Hierarchy | `THEAIRPORT` — **81** pivots |
| Meshes | `CYLINDER01` (main, 432 tris) + FIRE/SMOKE/SPARK FX (10) |
| Vertex/header bbox extent | **258.5 × 465.6 × 64.9** → XY area **120,368** |
| Functional pivot AABB (runway/park bones) | **448.7 × 205.0** → XY area **92,002** |
| RunwayStart→End lengths | R1 **155.4**, R2 **158.4**, R3 **177.4**, R4 **174.3** |
| Parking bones | **20** (`RUNWAY1–4` × `PARKING1–5`) |
| ParkHan / Prep | 20 / 20 |
| RunwayStart / RunwayEnd | **4 / 4** |
| Heli | `HELIPARK01` present |
| Texture | `CJJCWUJUN.tga` → **donor `CJJCWUJUN.dds` (174904)** — complete |
| Generals airfield bones | **Yes** (Parking + Prep + ParkHan + Start + End) |
| Structural read | Large apron/runway plane (`CYLINDER01`); FX sockets for damage smoke/fire; no named TOWER/HANGAR submesh |

### HXUSABigAirPort.W3D

| Field | Value |
|-------|--------|
| Path | `/tmp/donor_art_extract/Art/w3d/HXUSABigAirPort.W3D` |
| Size | **101513** bytes |
| Hierarchy | `HXUSABIGAIRPORT` — **37** pivots |
| Meshes | 14 (`OBJECT01/02` long strips ~400u, towers `OBJECT08/09/021/041`, hangar-like `OBJECT03–06`, apron `OBJECT07`, `SMOKE01`) |
| Vertex/header bbox extent | **244.5 × 466.5 × 85.6** → XY area **114,059** |
| Functional pivot AABB | **287.4 × 204.7** → XY area **58,812** |
| RunwayStart→End lengths | R1 **286.3**, R2 **286.9** |
| Parking bones | **6** (`RUNWAY1–2` × `PARKING1–3`) |
| ParkHan / Prep | 6 / 6 |
| RunwayStart / RunwayEnd | **2 / 2** |
| Texture | `CJJCWUJUN.tga` → **donor `CJJCWUJUN.dds`** — complete |
| Generals airfield bones | **Yes** |
| Structural read | Dual long runways + multiple building blocks + smoke socket |

### Related siblings (same HX package)

| W3D | Park | Max RW len | Pivot XY | Vertex XY | vs Egypt |
|-----|------|------------|----------|-----------|----------|
| `HXNewBigAir.W3D` | 4 | 218.5 | 55,734 | **175,488** | Larger mesh; same park count |
| `HXBigAir.W3D` | 3 | 99.8 | 28,463 | 111,105 | **Not** larger operationally |

---

## Comparison vs Egypt current (`Irq_Airfield`)

Egypt baseline (SPEC ART `Irq_Airfield.W3D`, used by `Egypt_Airfield_T`):

| Metric | Egypt / Irq | TheAirPort | HXUSABigAirPort | US_AirField |
|--------|-------------|------------|-----------------|-------------|
| Vertex XY area | **78,079** | **120,368 (+54%)** | **114,059 (+46%)** | 15,283 (−80%) |
| Pivot AABB XY | **42,607** | **92,002 (+116%)** | **58,812 (+38%)** | 23,612 (−45%) |
| Parking bones | **4** | **20** | **6** | 6 |
| Runway count (Start/End pairs) | 4 | **4** | **2** | 6 |
| Max Start→End length | **219.1** | 177.4 (−19%) | **286.9 (+31%)** | 128.9 (−41%) |
| Textures for mesh | complete (SPEC) | complete (donor) | complete (donor) | complete (SPEC) |

### Answer: physically larger than Egypt?

| Mesh | Physically larger? | Evidence |
|------|--------------------|----------|
| **TheAirPort** | **YES** | Vertex footprint +54%; parking-bone AABB +116%; **5× parking** (20 vs 4); 4 full runway bone sets |
| **HXUSABigAirPort** | **YES** | Vertex footprint +46%; pivot AABB +38%; **longer dual runways** (+31% vs Egypt max); 6 vs 4 parking |
| US_AirField | More slots only | **Smaller** mesh/pivot footprint and **shorter** strips than Egypt |
| ABArFrcCmd2 | N/A | **Still missing** from all ART sources |

Individual Egypt strips are longer than TheAirPort’s strips, but TheAirPort’s **overall facility** (mesh + parking layout) is substantially larger. HXUSABigAirPort wins on **runway length**.

---

## INI / text reference trace

Exact `TheAirPort` / `HXUSABigAirPort` / `HXNewBigAir` / `HXBigAir`:

- TEOD INI / SPEC DATA / W3DZH / TEOD W3D / SPEC ART: **no Object / CommandButton / map hits**
- Only prior audit markdown in this repo

Partial `BigAir*` TEOD hits are **`GenericBigAirplaneDeathWatercheckW`** (aircraft death FX), unrelated.

These are **orphan ART assets** (likely map/mod extras), not stock faction buildings.

---

## VIABLE LARGE AIRBASE ART marks

| Candidate | VIABLE LARGE AIRBASE ART? | Why |
|-----------|---------------------------|-----|
| **TheAirPort** | **YES** | Largest parking + large footprint + complete texture + Generals bones |
| **HXUSABigAirPort** | **YES** | Longest dual runways + larger footprint + complete texture + Generals bones |
| HXNewBigAir | Partial | Large mesh, only 4 parking (Egypt-parity capacity) |
| HXBigAir | No | Smaller operational layout |
| ABArFrcCmd2 | No | Mesh family absent |
| AmericaAirfield / US_AirField | Not “large geometry” | 6 slots but **physically smaller** than Egypt |
| Egypt Irq_Airfield | Baseline | — |

Damage/`*_D`/`*_E` absence is **not** a reject criterion here (FX sockets already on both orphans; Object INI can be authored later).

---

## Final candidate table

| Candidate | Source | Dimensions (vertex XY / pivot XY) | Runway bones | Parking bones | Textures complete | Physically larger than Egypt | Usable | Reason |
|-----------|--------|-----------------------------------|--------------|---------------|-------------------|------------------------------|--------|--------|
| **TheAirPort** | DONOR_Art only | 120k / 92k | Start/End ×4; max strip 177 | **20** | Yes (`CJJCWUJUN.dds`) | **YES** | **YES** | Largest facility + full Generals bones; needs Egypt Object INI |
| **HXUSABigAirPort** | DONOR_Art only | 114k / 59k | Start/End ×2; max strip **287** | **6** | Yes (`CJJCWUJUN.dds`) | **YES** | **YES** | Longest dual runways; needs Egypt Object INI |
| ABArFrcCmd2 | TEOD DATA only | — | (INI claims Runway1 only) | INI 2 | N/A | Unknown / INI smaller | **NO** | Primary W3Ds missing everywhere |
| AmericaAirfield / US_AirField | SPEC ART | 15k / 24k | Start/End ×6; max 129 | 6 | Yes (SPEC) | **NO** (smaller geometry) | Yes as normal 6-slot | Not the large runway mesh |
| Egypt current / Irq_Airfield | SPEC ART | 78k / 43k | Start/End ×4; max **219** | 4 | Yes | baseline | Yes | Current small/standard Egypt field |

---

## Conclusion

### B) FOUND LARGE AIRPORT MESH BUT NEEDS CUSTOM OBJECT WIRING: `TheAirPort.W3D`

Primary pick for real large airbase **geometry + parking capacity**.

Strong alternate for **longest dual runway**: `HXUSABigAirPort.W3D` (same status: viable ART, custom Egypt-only Object later).

**Not C** — both orphans were inspected directly and are measurably larger than Egypt with usable Generals runway/parking bones and complete textures.

**Not A** — no stock donor Object INI exists; Egypt wiring would be a later Egypt-only implementation step (still not done in this audit).

### Egypt integration (plan only — do not execute yet)

1. Author Egypt-only Object using `TheAirPort` (or `HXUSABigAirPort`) Draw=`W3DModelDraw` Model=`TheAirPort` / `HXUSABigAirPort`.
2. Declare `ExtraPublicBone` for every Parking/ParkHan/Prep/Start/End (+ Heli if used).
3. Set `ParkingPlaceBehavior` NumRows/NumCols from **real bone counts** (e.g. TheAirPort → reflect 20 slots without inventing beyond bones).
4. Import W3D + `CJJCWUJUN.dds` into ART if not already in SPEC.
5. Keep Pakistan and all other factions untouched.
6. Rebuild/ZIP **only** changed `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big` when implementing.

No BIG/ZIP produced this turn (audit-only).
