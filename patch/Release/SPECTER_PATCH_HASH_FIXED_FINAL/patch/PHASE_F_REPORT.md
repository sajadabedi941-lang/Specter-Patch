# Specter Patch — Phase F Report

## Scope
LAND + AIR + MISSILE + DRONE + DEFENSE + STRATEGIC WEAPONS  
**NO NAVAL CONTENT**

## Systems Delivered

### 1. Command Center Removal → Advanced Military HQ
- All expansion PlayerTemplates start with `Country_MilitaryHQ`
- Unique HQ names (National Defense Command, Integrated Defence HQ, Strategic Defense Center, etc.)
- Legacy CommandCenter soft-retired
- Stock overlays: America/Russia/China/NorthKorea MilitaryHQ objects

### 2. Advanced Air Base Global
- Worker build lists: **Airfield removed**, **AAB retained** as primary air facility
- 16-pad AAB system from prior phases remains

### 3. Air Defense Network
- Per-country **SHORAD / SAM / MD** units (60 Objects)
- Unique weapons + projectiles (range/speed/reload/FX/sound)

### 4. Drone Warfare
- 24+ country drones (combat / recon / loitering / Kızılelma)
- Wired into AAB / production CommandSets

### 5. Missile Warfare
- Prior ballistic/cruise/AAM/ATGM/ADSAM retained
- AD-tier missiles + nuclear reentry projectiles added

### 6. General Star Rework
- **215** upgrade buttons moved from MIC → SCIENCE Rank menus
- MIC CommandSets cleared of research upgrades

### 7. Unified Nuclear System
- Nuclear countries only: USA, Russia, China, India, Pakistan, France, Britain, North Korea
- Single `*_NuclearStrategic` science/power/weapon family
- **North Korea**: cost-0 starting nuclear science
- Non-nuclear FOAB/Nukes: **IsGrantable = No** + removed from General Star menus

### 8. Elite Infantry
- Country elite forces (Maroon Berets, SSO, SSG, Para SF, SAS, KSK, etc.)

## Audits
- Object/Weapon/Upgrade/CommandButton/CommandSet/Science/SpecialPower: **0 collisions**
- `sync_audit.py`: **PASS**
- Naval scan: **clean**

## Next (Phase G) recommendations
1. Wire nuclear shortcut powers into SpecialPower shortcut bars with country FX/OCL payloads
2. Stock-faction PlayerTemplate StartingBuilding overrides (America/Russia/China/NK → MilitaryHQ)
3. Full removal of legacy Airfield Object buildability (Prerequisites Impossible)
4. Deeper drone AI behaviors (loitering suicide scripts)
5. Country-unique AD model art beyond shared Turkey templates
