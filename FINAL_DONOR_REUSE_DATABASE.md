# FINAL_DONOR_REUSE_DATABASE

Baseline: live `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big` from global-donor-airforce-expansion-v1.
DONOR_ART is visual only. No donor Object/Weapon/CommandSet/gameplay INI was imported.

W3D dimensions are packed or extracted file sizes plus assigned Specter scale (normalized to fighter/UAV/transport class). Exact vertex AABB is not stored in the W3D name table; scale was chosen against known-good F-16 / Rafale / Su-35 / C-130 / MQ-9 references.

## Dotted aliases (must investigate)

### 01 EdaEurodyone.  (HAS DOT)
- Actual donor W3D: `Nat_Heron.W3D` / `Nat_HeronD.W3D` (packed). No Eurodrone-named W3D exists.
- Textures: `US_MQ9.dds` (referenced by Nat_Heron)
- W3D size: 57314 bytes. Scale 0.78 (MALE UAV, between MQ-9 0.70 and light fighter).
- Final identity: Eurodrone MALE RPAS
- Country: Germany
- Role: MALE recon + light precision strike. No A2A.
- New object: `GermanyUAVEuroMALE`
- Weapons: Paveway-style PGM x4 (`Germany_Weapon_EuroMALE_PGM`)
- Airbase: Germany Heavy, slot **8**
- Status: **CREATED_AS_REQUESTED**
- Notes: Distinct from live `GermanyDroneHeronTP` (`AVReaper`). NATO clone `GermanyDroneEurodrone` was not reused.

### 02 neuRonucan.  (HAS DOT)
- Actual donor W3D: `CHI_GJ11L.W3D` / `CHI_GJ11LD.W3D` (packed flying-wing). No nEUROn-named W3D.
- Textures: `PLA_GJ11.dds`
- W3D size: 84940 bytes (L variant; 9KB `CHI_GJ11.W3D` is a stub and was not used).
- Scale 0.72
- Final identity: Dassault nEUROn
- Country: France
- Role: stealth UCAV, 2 internal PGM, modest recon, no A2A
- New object: `FranceUCAVNeuron` (name unique vs existing NATO clone `FranceDroneNEURON`)
- Weapons: AASM/GBU x2
- Airbase: France Heavy, slot **5**
- Status: **CREATED_AS_REQUESTED**

### 03 Edafcas.  (HAS DOT)
- Inspected `AVStlDrone.W3D`: **2102 bytes stub**, not a playable aircraft.
- Inspected `CHAJ31HXNew.W3D`: manned J-31-class stealth fighter (assigned to J-35A).
- Chosen W3D: packed `LSFJ31.W3D` (J-31-class canard stealth). Documented as **FCAS NGF Demonstrator**, not a Remote Carrier UCAV, because the mesh is a manned stealth fighter silhouette.
- Textures: `LSFJ31.dds`
- W3D size: 92309. Scale 1.00
- Final identity: FCAS NGF Demonstrator
- Country: Germany (France fighter/heavy also had room; Germany Heavy had dedicated empty UAV/NGF slots)
- Role: limited A2A (Meteor x4) + 2 PGM, stealth, detector. Not a full fighter load.
- New object: `GermanyJetFCASNGF`
- Airbase: Germany Heavy, slot **9**
- Status: **CREATED_AS_REQUESTED** (identity chosen after silhouette audit)

### 04 Mirage 17.  (HAS DOT)
- W3D: packed `LSFFRF1.W3D` (same family as live Mirage F1CT). Silhouette is Mirage F1, not Mirage III.
- Textures: `LSFFRF1.dds`
- Size: 247943. Scale 0.85
- Final identity: Mirage F1CR
- Country: France
- Role: legacy recon / strike fighter
- New object: `FranceJetMirageF1CR`
- Weapons: medium x2, IR x2, bombs x4
- Airbase: France Fighter + Large, slot **11**
- Status: **CREATED_AS_REQUESTED**

### 05 Edavulcan.  (HAS DOT)
- No Avro Vulcan W3D in DONOR_ART or packed ART.
- Live `BritainBomberVulcan` already uses `LSFUSAB52` (B-52 stand-in). No second fake Vulcan created.
- Status: **NOT_FOUND**

### 06 EDA tornado.  (HAS DOT)
- Inspected `LSFTornador.W3D`: 50206 bytes, texture `ChinaGear.dds` (2872 bytes). Unusable as a Tornado aircraft.
- Germany and Italy already have live Tornado ECR. Independent UK object created on the packed Tornado family mesh.
- W3D: `LSFTornado.W3D` / d / k
- Textures: `LSFTornado.dds`
- Scale 0.92
- Final identity: Tornado ECR
- Country: UK
- Role: SEAD / electronic attack / strike
- New object: `BritainAircraftTornadoECR` (unique vs NATO clone `BritainJetTornadoECR`)
- Weapons: anti-radar x4, IR x2, PGM x4, detector
- Airbase: UK Heavy, slot **12**
- Status: **CREATED_AS_REQUESTED**

### 07 Dassaultrafale.  (HAS DOT)
- W3D: donor `LSFIDRafale.W3D` / d / k (not previously packed)
- Textures: `LSFIDRafale.dds`
- Size: 252383. Scale 0.95
- Final identity: Rafale F4
- Country: France
- Role: modern multirole. Does not replace Rafale C/B/M.
- New object: `FranceJetRafaleF4`
- Weapons: Meteor x6, MICA x4, AASM x4
- Airbase: France Fighter + Large, slot **12**
- Status: **CREATED_AS_REQUESTED**

### 08 RQ_180.  (HAS DOT)
- No RQ-180 W3D in DONOR_ART.
- Closest flying-wing (`CHI_GJ11L`) assigned to nEUROn.
- USA Heavy and Fighter menus are full with unique aircraft (B-2 and B-2A are distinct variants, not placeholders).
- Status: **NOT_FOUND** (no mesh + no safe USA slot)

### 09 Turbo vampire.  (HAS DOT)
- No Vampire W3D in DONOR_ART or packed ART.
- Status: **NOT_FOUND**

### 10 OriohuAV.  (HAS DOT)
- Packed `RUS_Orion2.W3D`. Object `RussiaDronesOrion2` already exists.
- Russia Fighter and Heavy menus are full. Existing object not duplicated onto a new slot.
- Status: **DUPLICATE_REUSED** (existing Russia Orion; no new menu slot)

### 11 cargoplane.  (HAS DOT)
- W3D: donor `AVCargoPln.W3D` (174816) + `_D` + `_D1`. Four-engine high-wing turboprop, C-130 class (not A400M, not C-17).
- Textures: `AVCrago2.dds` (donor spelling)
- Helpers `AvCargoPln_A2.W3D` (1787) and `AVStlDrone` ignored.
- Final identity: C-130H
- Country: Japan (JASDF C-130 operator; FR/DE/IT/UK already have C-130 or A400M/C-17)
- Role: transport, no offensive weapons, 24 infantry/vehicle slots
- New object: `JapanJetC130H`
- Scale 1.05 transport class
- Airbase: Japan Heavy, slot **7**
- Status: **CREATED_AS_REQUESTED**

### 12 vampire.  (HAS DOT)
- Same missing Vampire mesh as Turbo vampire. No second variant.
- Status: **NOT_FOUND** / **DUPLICATE_REUSED** of 09 (no distinct mesh)

### 13 Shenygng.  (HAS DOT)
- W3D: donor `CHAJ31HXNew.W3D` (87554) stealth Shenyang/J-31-class fighter
- Textures: `CHA_J31A.dds` (W3D asks for CHA_J31A.tga)
- Scale 1.05
- Final identity: Shenyang J-35A
- Country: China
- Role: stealth air superiority / naval-capable fighter
- New object: `ChinaJetJ35A`
- Weapons: PL-15 x6, PL-10 x2, LS-6 x2
- Airbase: China Heavy, slot **12**
- Status: **CREATED_AS_REQUESTED**
- Distinct from live `ChinaJetJ31` (`LSFJ31`).

## Appearance-only aliases (no dot)

| Alias | Actual W3D | Final identity | Country | Status |
| --- | --- | --- | --- | --- |
| Typhon | `LSFEUEF2000` (packed, existing Typhoons) | existing DE/IT/UK Typhoon | DE/IT/UK | USED_AS_VISUAL_DONOR (existing; no extra clone) |
| F_16 / F_16 | `LSFF16C` / `LSFKF16` | Turkey F-16C / OZGUR already live | Turkey | USED_AS_VISUAL_DONOR (prior pass) |
| Jh_7A | `CHI_JH7A2` | existing China JH-7A2 | China | USED_AS_VISUAL_DONOR (existing) |
| J_31 | `LSFJ31` + `CHAJ31HXNew` | FCAS NGF (DE) + J-35A (CN) | DE/CN | USED_AS_VISUAL_DONOR |
| J_10 | `ChJ10B` / `CHI_J10C` | China J-10B existing; Pakistan J-10CE new | CN/PK | USED_AS_VISUAL_DONOR |
| J_20 | `CHI_J20B` / `LSFJ20` | existing J-20 / J-20C | China | USED_AS_VISUAL_DONOR (existing) |
| J_16 / J16 | packed Flanker-family J-16 | existing China J-16 path | China | USED_AS_VISUAL_DONOR (existing) |
| F_35 | `ENF35A` / `LSFUSAF35A` / `US_F35A` | existing UK/IT/DE F-35 | UK/IT/DE | USED_AS_VISUAL_DONOR (existing) |
| F_18E | Super Hornet family packed | USA menus full; no Australia faction | USA | USED_AS_VISUAL_DONOR / no safe extra operator |
| Mirage2000 | `FraMirage2000` / `LSFMirage2000` | existing France 2000 / 2000-5F | France | USED_AS_VISUAL_DONOR (existing) |
| Mig31 | packed MiG-31 | Japan clone already on fighter; no extra | - | USED_AS_VISUAL_DONOR (existing odd Japan slot left untouched) |
| su35 / Su35flanker | `LSFSU35.W3D` | Iran Su-35 | Iran | USED_AS_VISUAL_DONOR |
| mirg35 | packed MiG-29/35 family | Russia already has MiG-35; not cloned | Russia | DUPLICATE_REUSED |
| Su34 | `RUS_SU34` | Russia already has Su-34 | Russia | USED_AS_VISUAL_DONOR (existing) |
| Su25 | `Irn_Su25` / `LSFIRSu25` | Iran already has SU25K on fighter | Iran | DUPLICATE_REUSED (not added to Heavy) |
| sqt50Rakfa | `qsnt50.W3D` (packed) | Italy GCAP demonstrator | Italy | USED_AS_VISUAL_DONOR |
| Mig21 / Mig21 fishing | `LSFIDMig21.W3D` | Iran MiG-21bis (Fishbed) | Iran | USED_AS_VISUAL_DONOR |
| J10fireba | `CHI_J10C.W3D` | Pakistan J-10CE | Pakistan | USED_AS_VISUAL_DONOR |

Extra packed HALE mesh `US_RQ-4.W3D` used as Japan RQ-4 (unarmed recon) because RQ-180 had no mesh and USA Heavy is full.

## Duplicates / stubs not used as extra units

- `AVStlDrone.W3D` (2102) helper stub
- `AvCargoPln_A2.W3D` (1787) helper
- `LSFTornador.W3D` + `ChinaGear.dds` unusable
- `CHI_GJ11.W3D` 9KB stub; L variant used instead
- Vampire x2 identical missing mesh
- Russia Orion already exists
- Su-25 already on Iran fighter

## Missing / broken

- Avro Vulcan mesh: NOT_FOUND
- de Havilland Vampire mesh: NOT_FOUND
- RQ-180 mesh: NOT_FOUND
- Dedicated Eurodrone / nEUROn / FCAS named meshes: NOT_FOUND (stand-ins documented above)
