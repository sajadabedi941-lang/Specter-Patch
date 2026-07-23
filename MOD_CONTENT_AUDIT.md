# MOD_CONTENT_AUDIT.md — Specter Ultimate Warfare Expansion

**Date:** 2026-07-23  
**Rule:** Overlay-only under `patch/`. Vendor archives (`Data.zip`, `_SPEC_*`, `Specter_Data*`, `.big`) are **never** modified.  
**Naval:** Audited but **not imported** (Specter Patch NO NAVAL policy).

---

## 1. Archive inventory

| Archive | Volumes present | Status | Recoverable content |
|---------|-----------------|--------|---------------------|
| **mod.zip** (+ z01–z22, z25–z28) | 27 of 29 | **INCOMPLETE** — missing **mod.z23**, **mod.z24** | 7z lists + extracts most `Data/INI/*` (264–292 INI files recovered). Full solid extract reports `ERROR = Missing volume : mod.z23`. |
| **Peace Mission Beta Ver 1.0.zip** (+ z01–z32) | 33/33 | **COMPLETE** | Loose `Data/` (cursors, scripts, waterplane, CSF, Language.ini). Unit/art payload is inside `.big` packs (not loose INI). |
| **payload.rar** | 1/1 | COMPLETE (RAR5) | Mostly opaque `.bin` payloads. `Science_GeneralStar_Addon.ini` already imported into patch earlier. |
| **Data.zip / _SPEC_ART_ONE / _SPEC_DATA_ONE / Specter_Data** | Present | **VENDOR — DO NOT MODIFY** | Specter baseline; patch overlays only. |

### Missing volumes (blocker for full mod art extract)

```
MISSING: mod.z23
MISSING: mod.z24
```

Until these are uploaded, W3D/texture volumes that live across the multi-volume span cannot be fully reconstituted. Overlay integration uses **Specter art assets** with unique `Patch_*` Object IDs.

---

## 2. mod.zip — content summary (extracted INI)

Recovered under `/tmp/mod_extract` for audit (not copied into vendor trees).

| Category | Count / notes |
|----------|----------------|
| **Object definitions** | **3322** `Object` blocks across Object INIs |
| **Weapons** | **1599** in `Data/INI/Weapon.ini` (~722 air/missile-related) |
| **CommandButton** | **1916** |
| **CommandSet** | **873** |
| **Science** | **260** |
| **Upgrade** | **123** |
| **Top-level INI** | Weapon, Armor, FXList, Locomotor, SoundEffects, Science, Upgrade, CommandButton/Set, ParticleSystem, PlayerTemplate, etc. (37 files) |
| **Audio (listed)** | ~1273 `.wav` paths in archive listing |
| **Models/Textures (listed)** | ~1421 asset paths (wav/tga/dds); W3D not fully recoverable without z23/z24 |

### Faction Object folders (INI file counts)

| Folder | INI files | Role |
|--------|-----------|------|
| EastEuropeAlliance_Ukraine | 33 | Aircraft, airfield, drones, vehicles, AN-70/225, defence |
| EurasianUnion_Russia | 19 | Aircraft, airfield, airships, EMP, vehicles, carrier* |
| EuropeanUnion_Germany | 17 | Aircraft, airfield, vehicles |
| EuropeanUnion_France | 17 | Helicopters, helipad, holograms, underground HQ |
| America_USA / America_Alliance | 14 each | Aircraft, airfield, strategy, vehicles |
| GLA_Rogue / GLA_Pyrat | 17 / 15 | Rogue/Pyrat generals |
| AsianAlliance_Japan | 3 | Barracks, CC, vehicles |
| EastAsianUnion_China | 1 | Vehicle pack |
| Optimize / Render Effect | 15 / 3 | Perf / FX helpers |
| Root generals packs | 45 | AirforceGeneral, HelicopterGeneral, Missile, TankGeneral, WeaponObjects, ChinaAir, SpecPlane, AircarrierPlanes*, etc. |

\*Naval/carrier content present in source — **excluded from Specter import**.

---

## 3. Category audit (mod Objects)

Approximate role buckets from Object ID + path heuristics (some spill into “Other” / WeaponObjects):

| Category | Approx. objects | Notable examples |
|----------|-----------------|------------------|
| **Fighters** | ~75+ | `AmericaJetRaptor`, `AmericaJetHAWK`, `AmericaVehicleJetF-35`, `Eurasian_RussiaJetPakFA`, `EEA_UkraineJetSU-Sokil`, `ChinaJetMIG`, `ChinaJetJ-10` |
| **Bombers** | ~27 | `Lazr_AmericaB3Bomber`, `AmericaJetB52`, `EEA_UkraineAircraftHeavyBomber`, `EU_GermanyJetBomber`, `Eurasian_RussiaJetTU160Strike` |
| **AWACS / AEW** | ~8 | `AmericaJetHAWKEY`, `EEA_UkrainePlaneAN-71` |
| **Transport** | ~21 | `AmericaVehicleChinook`, `AmericaJetCargoPlane`, `ChinaJetCargoPlane`, `GLAJetCargoPlane` |
| **Tankers** | ~3 | Mostly civilian tanker props (limited military tanker INI surface) |
| **Helicopters** | ~131 | `EU_FranceHelicopterCayova`, `EU_GermanyVehicleNH90`, `ChinaVehicleHelix`, Eurocopter / Osprey variants |
| **UAV / Drones** | ~52 | `EEA_UkrainePlaneBaykatar`, `EEA_UkraineDronecopter`, Scout/Spy/Battle/Sentry drones |
| **Missiles / Rockets** | ~450 | `Missile.ini` + WeaponObjects: Patriot, Tor-M, Raptor/F-35/F-18 missiles, Scud, cruise, ATGM |
| **Air defense** | ~55 | Patriot batteries, Avenger, Tor-related, Stinger, airfields-as-AD spill |
| **Tanks / armor** | ~220 | Crusader, Overlord, BattleMaster, Marauder, faction tanks |
| **Infantry / weapons** | ~232 | Rangers, Redguards, missile defenders, heroes |
| **Structures** | ~189 | CC, barracks, airfield, war factory, strategy, supply, firebases |
| **Effects / particles** | FXList.ini + ParticleSystem.ini + WeaponObjects FX helpers | Large FX catalog |
| **Sounds** | SoundEffects.ini + ~1273 wav | Jets, guns, missiles, voices |
| **Command / AI** | CommandButton/Set, Scripts (Peace), Eva/Speech | Full UI/AI surface in mod |
| **Upgrades / Tech** | Upgrade.ini (123), Science.ini (260) | General trees + faction sciences |
| **Models / Textures** | Art under English/Art; incomplete without z23/z24 | Overlay uses Specter models |

---

## 4. Peace Mission Beta Ver 1.0 — content summary

| Item | Status |
|------|--------|
| Volumes | **Complete** (zip + z01–z32) |
| Loose Data | Cursors (`.ani`), WaterPlane TGA sequence, Scripts (`.scb` / Scripts.ini), English/Chinese `generals.csf`, Language.ini, Movies (`.bik`) |
| `.big` packs | `00PMBeta994`–`999.big` (~1.5+ GB uncompressed total) — ZH-era art/data blobs |
| Loose unit INI | **None** (unit definitions live inside BIG, not exported here) |
| Integration note | Useful for optional cursors/scripts/waterplane overlays later; **not** the primary unit source. Air force expansion sourced from **mod.zip INI** roles. |

---

## 5. payload.rar

| Item | Status |
|------|--------|
| Format | RAR5 binary payloads (`art_add_*.bin`, `data_*.bin`, `payload_*.bin`, `commandset.bin`, `usa_system.bin`) |
| Readable INI | `Science_GeneralStar_Addon.ini` (already in `patch/Data/INI/`) |
| Integration | Keep as reference; do not unpack binaries into vendor archives |

---

## 6. Integration decisions (this patch turn)

### Imported as overlay (Air Force Expansion)

Unique `Patch_*` Objects + weapons + projectiles + AAB CommandSet slots. Specter art (`US_*`, `Irq_*`). Fixed timings for MP sync.

| Source mod Object | Overlay Object | Role |
|-------------------|----------------|------|
| AmericaJetAurora | `Patch_America_Aurora` | Strike |
| AmericaJetHAWK | `Patch_America_StealthHawk` | Stealth fighter |
| AmericaJetSpectreGunship | `Patch_America_AC130Spectre` | Gunship |
| AmericaJetHAWKEY | `Patch_America_E2C` | AWACS |
| Lazr_AmericaB3Bomber | `Patch_America_B3` | Strategic bomber |
| Eurasian_RussiaJetPakFAStriker | `Patch_Russia_Su57Strike` | Strike fighter |
| EEA_UkraineJetSU-Sokil | `Patch_Ukraine_Sokil` | Fighter |
| EEA_UkrainePlaneAN-71 | `Patch_Ukraine_AN71` | AWACS |
| EEA_UkraineDronecopter | `Patch_Ukraine_Dronecopter` | Armed UAV |
| EU_GermanyJetBomber | `Patch_Germany_JetBomber` | Bomber |
| EU_FranceHelicopterCayova | `Patch_France_Cayova` | Attack helo |
| ChinaJetJ-10 | `Patch_China_J10Strike` | Precision strike |
| TorMMissile / TORMissileWeapon | `Russia_AD_TorM` + `Patch_Weapon_TorM` | SHORAD |

### Explicitly not imported

- **Naval / air-carrier / corvette** planes (`AircarrierPlanes.ini`, carrier helos)
- **Stock Object ID clones** (would collide with Specter / break MP)
- **Raw mod Weapon.ini wholesale** (ID collisions; selective `Patch_Weapon_*` only)
- **Peace Mission .big** contents (no safe overlay path without BIG tooling + art pipeline)
- **Incomplete mod W3D** (blocked by missing z23/z24)

### Preserved Specter systems

- Turkey faction tree + Phase G/H/I air slots  
- Advanced Air Base + 16-pad runway contract (`Scale 1.60`)  
- Heavy aircraft scale table (bomber 0.72 / AWACS 0.78 / transport 0.76 / CH-47 0.82)  
- Installer (`Install_SpecterPatch` / `Run_SpecterPatch` / backup_map fix)  
- Country packs, MilitaryHQ, drones, missiles, General Star sciences  

---

## 7. Patch file map (new)

```
MOD_CONTENT_AUDIT.md
patch/Data/INI/Object/Specter/PatchSystems/AirForceExpansion/
  AIR_FORCE_EXPANSION.txt
  Aircraft_AirForceExpansion.ini
  Projectiles/Projectiles_AirForceExpansion.ini
patch/Data/INI/Object/Specter/PatchSystems/AirDefense/Russia_AD_TorM.ini
patch/Data/INI/Weapon_AirForceExpansion.ini
patch/Data/INI/CommandButton_AirForceExpansion.ini
patch/Data/INI/CommandSet_AdvancedAirBase.ini          (slots extended)
patch/Data/English/AirForceExpansion_Strings.txt
```

---

## 8. Multiplayer / sync

- Unique Object / Weapon / CommandButton IDs (`Patch_*` / `Russia_AD_TorM`)  
- Fixed `DelayBetweenShots`, `ClipReloadTime`, `WeaponSpeed`, missile `FuelLifetime`  
- No `Random*` lifetime spreads in new content  
- LinkKeys: `Patch_EliteAircraft`, `Patch_EWAircraft`, `Patch_UAV`, `Patch_AirDefense`  
- Gate: `python3 patch/tools/economy/sync_audit.py` → PASS; regenerate `SYNC_MANIFEST.sha256`

---

## 9. Follow-ups (when missing volumes arrive)

1. Upload **mod.z23** + **mod.z24**  
2. Re-extract Art/W3D; optionally map true models onto `Patch_*` Draw blocks  
3. Optional Peace Mission BIG unpack for cursors-only / script overlays  
4. Ground tank / infantry selective import (same unique-ID overlay rules)  

---

## 10. Verdict

| Area | Audit | Integration |
|------|-------|-------------|
| Aircraft / fighters / bombers / AWACS / helo / UAV | COMPLETE (mod INI) | Air Force Expansion overlay **IMPLEMENTED** |
| Missiles / Tor-M AD | COMPLETE (mod INI) | Selective weapons + Tor-M AD **IMPLEMENTED** |
| Tanks / infantry / structures | CATALOGUED | Deferred (air-first turn; query truncated at AIR FORCE EXP) |
| Effects / sounds / models | PARTIAL (INI + listing; art gap z23/z24) | Reuse Specter FX/audio/models |
| Peace Mission units | MISSING as loose INI | Documented; BIG not unpacked into patch |
| Multiplayer safety | REQUIRED | sync_audit + unique IDs |
