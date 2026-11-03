# USAPAC3 — cleanup and rebuild design (no new PAC-3 yet)

Zero Hour was **not** run. PAC-3 rebuild is **not started**. Previous GitHub
Releases were **not** deleted or rewritten.

Agreed rebuild specs (locked until you change them):

| Field | Value |
|---|---|
| Unit name | USAPAC3 |
| Country | America |
| Type | Ground missile air defense |
| Look | Real PAC-3 from New Donor |
| Gameplay structure | Healthy SPECTER ground AD (not a fighter) |
| Weapon baseline | Current SPECTER THAAD (`Object US_THAAD` / `S400R_Deploy` numbers cloned under new names) |
| Cost / time | 3876 / 18.6 s |
| Built from | AmericaCommandCenter / AmericaCommandCenterCommandSet **slot 6** |
| Science / Rank / Upgrade / Prerequisite | none |

---

## 1. Cleanup of the failed implementation

### 1.1 What was USAPAC3-specific (removed from **active** SPECTER)

| Path | Why removed |
|---|---|
| `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini` | `Object USAPAC3` — spawn-crash unit |
| `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3_Projectile.ini` | `Object USAPAC3_Projectile` |
| `Data\INI\Weapon_USAPAC3.ini` | `Weapon USAPAC3_Weapon` |
| `Data\INI\CommandSet_ZZZZ_USAPAC3.ini` | `USAPAC3CommandSet*` + overlay HQ slot 6 |
| `Data\INI\MappedImages\HandCreated\USAPAC3_Images.INI` | UI `MappedImage USAPAC3` |
| `Data\English\FactionExpansion_USAPAC3_Strings.txt` | unique-path strings |
| `CommandButton Command_ConstructUSAPAC3` in `CommandButton.ini` | UNIT_BUILD → USAPAC3 |
| America CC `6 = Command_ConstructUSAPAC3` | added by us; original CC had **no slot 6** |
| Overlay HQ `America_MilitaryHQCommandSet` slot 6 USAPAC3 | not live CC; restored NASAMS |
| ART TWO `UsaPac3Car*.W3D`, `UsaPac3F*.W3D`, `pac3mis_m.W3D` | New Donor meshes used only by USAPAC3 |
| ART TWO `usaPAC3TRUCKmap*`, `ampac3map*`, `pac3missilemap`, `USAPAC3.tga`, `USAPAC3TB.tga` | textures only those W3Ds referenced |

Loose overlay copies of the same files were **moved** (not deleted) to:

`docs/specter-usapac3/archive/failed-impl/`

Experiment docs (`docs/specter-usapac3/abtest/`, DIAGNOSIS_SPAWN*.md, backup W3Ds) stay.

### 1.2 What was **not** removed (shared / other units)

| Path / object | Reason |
|---|---|
| `Art\W3D\ABPatriot.W3D` | pre-existing; uses `ABNPatriot02` |
| `Art\Textures\ABNPatriot02.dds` / `_d.tga` | shared with `ABPatriot.W3D` |
| `Art\W3D\pac3_sudarb.W3D` | pre-existing; other textures (`Patriothisuaarb.tga` …) |
| `Object US_THAAD` (`US_M1120.ini`) | live American TEL |
| `Object AmericaMobileSamSiteMIM104F` | live Patriot truck |
| Overlay `America_AD_THAAD` / `_Patriot` / `_NASAMS` (not in packed DATA) | untouched source |
| Other countries’ AD | untouched |
| `Data\English\generals.csf` | may still contain unused `OBJECT:USAPAC3` labels; editing CSF risks the whole string table |

America Command Center **structure restored**, not redesigned: slot 6 line removed; slots 1, 12–18 unchanged.

### 1.3 Static validation

`STATIC_OK` via `docs/specter-usapac3/validate_cleanup.py`.

| Artifact | SHA-256 | Size |
|---|---|---:|
| `_SPEC_DATA_ONE.big` (cleaned) | `3527ea062da9ab27c9902665238398ae0f29d985b6d342617449784a51bdda1a` | 374081161 |
| `_SPEC_ART_TWO.big` (cleaned) | `2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38` | 308844919 |
| `CommandSet.ini` | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` | |
| `CommandButton.ini` | `d012daf5578f468da904e25008cc0f186de320f0b3ae6349fe4e8c2d3a6f4b36` | |

INGAME_ZH: not executed. Cleanup is not claimed crash-verified in-game.

Previous tags `specter-usapac3-spawnfix`, `spawnfix2`, `spawnfix3`, `abtest-b` remain on GitHub.

---

## 2. Successful F-117 transfer method

**Object:** `AmericaJetF117Clean`  
**Visual donor:** TEOD `AVStealth` / `AVStealth_D` + `avstealth*.dds` (`New folder.zip` / `!TEOD_*`)  
**Gameplay skeleton:** live SPECTER `AmericaJetF-16C_AG` (JetAI, locomotor, weapons) — **not** the TEOD stealth-fighter object wholesale.

### Commits

| Hash | What it did |
|---|---|
| `c73d814b` (2026-08-10) | Add `AmericaJetF117Clean`; copy AVStealth W3D/DDS as-is; clone F-16C_AG gameplay; strip TEOD science/SpecialPower/HelixContain |
| `106c62e2` (2026-08-18) | Large Air Base slot 13 = `Command_ConstructAmericaJetF117` |
| `ff16212a` pattern (B-21, same lesson) | define CommandButton **before** CommandSet parse |
| `a4308cdf` / `36f1eb78` | Scale-only tweaks (`0.9` then `1.04`) |

### How the model was made ZH-safe

- **No W3D re-export.** Binaries copied as-is into ART.
- **INI “clean object”:** `W3DModelDraw` with Default + `_D` damage; hide unused burner subobjects; do **not** enable TEOD locomotor or laser-missile Draw.
- Crash prevention was **parse-order and module stripping**, not mesh conversion.
- Production: dedicated CommandButton + CommandSet slot (or retarget an existing button).

### Donor vs SPECTER

| | TEOD stealth fighter | SPECTER F-117 |
|---|---|---|
| Mesh/textures | AVStealth* | same files |
| AI / loco | TEOD | F-16C_AG jet |
| Powers / science | present | removed |
| Draw extras | laser-missile upgrade Draw | omitted |

**Reusable for PAC-3:** clean-object pipeline, ART copy, gameplay from a **working SPECTER unit**, strip donor behaviors. **Not reusable:** JetAI, aircraft KindOf, afterburner states.

---

## 3. Successful B-21 transfer method

**Object:** `AmericaJetB21Clean` (airfield) vs Phase-G name-only `Patch_America_B21` (`US_B1R` stand-in).  
**Visual donor:** TEOD `AVB21_A` / `AVB21_A_D` + `B-21*.dds` from `!TEOD_W3D.big` / `!TEOD_Textures.big` / `B21_Rider.ini`.  
**Gameplay skeleton:** SPECTER B-1R then B-2/B-52 (`D30-F6_JetLocomotor`, jet death OCLs).

### Commits

| Hash | What it did |
|---|---|
| `c6f6f48a` / `4001fa7f` | Clone `AmericaJetB1R` gameplay as B-21 |
| `4d2dbb21` / `84cd3c84` | Find real Raider art in TEOD; evidence manifest |
| `73a18291` | Paste TEOD Draw onto `AmericaJetB21Clean`; pack AVB21 W3D/DDS |
| `ff16212a` | Early CommandButton so CommandSet does not crash |
| `eb1f8c74` | Later aircraft use “B-21 method” explicitly |

### How the model was made ZH-safe

- Extract W3D/DDS from donor BIG **as-is**. No documented retarget/re-export.
- Copy **Draw block only** from `B21_Rider.ini`.
- **Do not import** `B21RiderLocomotor`, `OCL_B21Death*`, TEOD CommandSets, TEOD geometry 20×30 (parking crash risk).
- Keep SPECTER geometry/AI.

### Donor vs SPECTER

| | TEOD B21_Rider | SPECTER AmericaJetB21Clean |
|---|---|---|
| Draw/W3D | AVB21 state machine | copied Draw |
| Locomotor | B21RiderLocomotor | SPECTER jet loco |
| Death OCL | OCL_B21* | Aurora/B-2 chain |
| Geometry | 20 / 30 | SPECTER 14 / 7 |

**Reusable for PAC-3:** forensics → extract ART → MappedImages → Draw-only swap onto a **proven SPECTER object** → independent weapon/projectile names → pack BIG → CommandButton defined in `CommandButton.ini` before CommandSet names it.

---

## 4. Ground AD pattern to clone (not a fighter)

**Chosen live unit:** `Object US_THAAD`  
**File:** `Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini`  
**Why:** packed in active DATA; American deployable TEL; same class as PAC-3 (truck, pack/unpack, SAM). Overlay `America_AD_THAAD` is **not** in packed DATA and must not be the parent.

Secondary reference (simpler truck, no deploy anim): `AmericaMobileSamSiteMIM104F` (`US_M1075`).

### US_THAAD spawn path (working)

- `Draw = W3DTruckDraw` (one module)
- Models `US_M1120` / `US_M1120D` / `US_M1120_A` / `US_M1120_AD` (mesh ver **0x50000**)
- Packed anim has **real channels**; deployed `US_M1120_A` has **no ANIMATION chunk**
- `Locomotor = Generic8x8Locomotor` (`HasSuspension = Yes`)
- `Behavior = DeployStyleAIUpdate` (no Turret{} in Draw)
- `Weapon` SECONDARY+TERTIARY only (`S400R_Deploy` / `_ABM`)
- `KindOf` includes `CAN_ATTACK VEHICLE`
- Geometry BOX 45×12×16, Physics Mass 400

### Fighter vs ground (do not copy F-117/B-21 structure onto PAC-3)

| | F-117 / B-21 | US_THAAD (use this) |
|---|---|---|
| Draw | `W3DModelDraw` | `W3DTruckDraw` |
| AI | `JetAIUpdate` | `DeployStyleAIUpdate` |
| Loco | jet + taxi | `Generic8x8Locomotor` |
| KindOf | `AIRCRAFT` | `VEHICLE` |
| Anim states | JETEXHAUST / AFTERBURNER | PACKING / UNPACKING / DEPLOYED |
| Bones | ENGINE, WINGTIP | TIRE01–08, chassis |

---

## 5. Why the previous USAPAC3 likely crashed (hypotheses, not proven in-game here)

Failed in-game: spawnfix, spawnfix2, spawnfix3, and experiment B were all reported still crashing **or** B was not yet confirmed by this environment. Do not treat any single module as proven.

Likely classes of mismatch vs the F-117/B-21 **and** US_THAAD methods:

1. **Donor W3D used as if it were a SPECTER TEL.** New Donor `UsaPac3Car` / `UsaPac3F` are mesh **0x40002**, 52 meshes, empty or near-empty animation headers. Live TELs are **0x50000** with real channels or **no** anim blob. F-117/B-21 copied TEOD meshes that already matched ZH aircraft Draw; PAC-3 copied a ground mesh that was never shown to spawn as a truck.
2. **Gameplay was cloned from overlay `America_AD_THAAD`**, which is **not** in live DATA. F-117/B-21 cloned **packed live** jets (`AmericaJetF-16C_AG`, `AmericaJetB1R`).
3. **Draw was a hybrid** (second truck Draw, attach-to-CORE, PRISTINE flags, empty F clip, then partial removals) instead of a single known-good Draw pasted onto a known-good object.
4. **W3DModelDraw preloads every ConditionState model at create.** Extra New Donor models (`UsaPac3F`, `UsaPac3Car_w`) were on the spawn path even when “packed”.
5. Experiment B (US_M1120 Draw + rest of Object USAPAC3) was built so a **future in-game test** can split Draw vs other modules. That result is **not** available here.

---

## 6. Proposed structure for the future PAC-3 (after your approval)

Follow B-21/F-117 **process**, US_THAAD **object class**:

1. Keep a Specter-safe object whose **entire** non-art side matches `US_THAAD` (Draw type, loco, AI, weapons cloned to new names, geometry, physics).
2. Only then attach New Donor look:
   - either re-export/convert `UsaPac3Car` / `UsaPac3F` to the same W3D layout as `US_M1120` / `US_M1120_A` (v5 mesh, real anim or **no** anim chunk on deployed),
   - or start with `US_M1120` Draw (known spawn) and swap models one file at a time after an in-game spawn succeeds.
3. New names only: `Object USAPAC3`, `Weapon USAPAC3_Weapon`, `Object USAPAC3_Projectile`.
4. CommandButton in **packed/loose `CommandButton.ini` first**, then slot 6 on `AmericaCommandCenterCommandSet`.
5. No Science/Rank/Upgrade/Prerequisite.
6. Do not invent radar/intercept systems. Use existing SAM weapon flags (`AntiAirborneVehicle`, `AntiBallisticMissile`) as THAAD does.
7. Do not import New Donor Object/INI/locomotor/OCL.
8. ART TWO for W3D if ART ONE is full; do not overwrite shared `ABNPatriot02` / `pac3_sudarb`.
9. Every step in-game: spawn first, then deploy, then fire. Static OK ≠ in-game OK.

---

## 7. Files to create or change in the **future** rebuild (not this PR)

- `Data\INI\Object\...\USAPAC3.ini` (new clean object)
- `Data\INI\Weapon_USAPAC3.ini` / projectile INI (new names, THAAD numbers)
- `CommandButton.ini` — append `Command_ConstructUSAPAC3` only
- `CommandSet.ini` — **only** `AmericaCommandCenterCommandSet` slot 6
- MappedImages + CSF labels
- ART TWO: converted/verified PAC-3 W3D + unique textures (not shared patriot files)
- `_SPEC_DATA_ONE.big` / `_SPEC_ART_TWO.big` pack scripts + validator

---

## 8. Files that must **not** change in the rebuild

- `Object US_THAAD` / `US_M1120.ini`
- Patriot `AmericaMobileSamSiteMIM104F` / MIM104 objects
- NASAMS objects and `Command_ConstructAmerica_AD_NASAMS`
- Other countries’ AD
- America Command Center except slot 6
- `Art\W3D\ABPatriot.W3D`, `pac3_sudarb.W3D`, shared `ABNPatriot02` unless proven unused
- `_SPEC_ART_ONE.big` (full; do not force PAC-3 into it)
- Multiplayer/determinism-facing global INI (Weapon.ini stock, Armor.ini, Locomotor.ini definitions of `Generic8x8Locomotor`)
- Previous GitHub Release tags

---

## Still needs in-game testing (not done)

- Whether cleaned SPECTER boots and America CC opens without slot 6
- Experiment B result (Draw vs Object) — ZIP still on tag `specter-usapac3-abtest-b`
- Any future PAC-3 spawn, deploy, and fire
