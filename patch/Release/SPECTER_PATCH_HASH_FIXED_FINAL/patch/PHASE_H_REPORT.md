# Phase H Report — Complete National Military Identity + Advanced Weapon Integration

**Scope:** LAND / AIR / MISSILE / DRONE / DEFENSE only. No naval. Patch-only.

**Audits:** ID collisions = **0**. `sync_audit.py` = **PASS**. Naval keyword scan = **clean**.

---

## 1. Global aircraft expansion

### Added
| Object | Unique weapon | Notes |
|--------|---------------|-------|
| `Patch_America_F15EX` | `America_Weapon_AMRAAM_F15EX` | Elite fighter; AAB USA |
| `Patch_America_F16V` | `America_Weapon_AIM120C_F16V` | Distinct from F-16C |
| `Patch_Pakistan_J10C` | `Pakistan_Weapon_PL15_J10C` | Pakistan-operated J-10C identity |

### Deepened (shared Western weapons replaced)
| Object | Unique weapon |
|--------|---------------|
| `Patch_Russia_Mig31` | `Russia_Weapon_R37_Mig31` |
| `Patch_Russia_Tu160` | `Russia_Weapon_Kh102_Tu160` |
| `Patch_Russia_Tu22M3` | `Russia_Weapon_Kh32_Tu22M3` |
| `Patch_China_J16` | `China_Weapon_PL15_J16` |
| `Patch_China_H6` | `China_Weapon_CJ10_H6` |

### Already present (retained)
F-22, F-35, B-21, Su-57/75/35, Tu-160/22M3, J-20/35/10/16, KAAN, F-16 Blk70, Kizilelma, Anka, TB2/Akinci, Tejas/Mk2, Su-30MKI, Rafale, JF-17 BlkIII, F-35J, F-2, Eurofighter/Typhoon, Gripen, EW/AWACS/tankers.

---

## 2. Hypersonic / strategic missile tree

| Object | Weapon | Identity |
|--------|--------|----------|
| `China_DF17TEL` | `China_Weapon_DF17` (wired) | Hypersonic glide |
| `China_DF26TEL` | `China_Weapon_DF26` | Longer-range theater |
| `Russia_ZirconBattery` | `Russia_Weapon_Zircon` | Faster than Kinzhal |
| `Russia_AvangardTEL` | `Russia_Weapon_Avangard` | Strategic; limit 1 |
| `America_ARRWTEL` | `America_Weapon_ARRW` | Air-breathing hypersonic class |
| `America_PGSTEL` | `America_Weapon_PGS` | Prompt Global Strike class; limit 1 |
| `Iran_FattahTEL` | `Iran_Weapon_Fattah` | Distinct from Fateh/Sejjil/Khorramshahr |
| `India_BrahMosIITEL` | `India_Weapon_BrahMosII` | Hypersonic BrahMos successor |

Prior TELs retained: Kinzhal, Iskander, DF-21, PrSM, Tomahawk, Tayfun, Agni, Shaheen, Ababeel, Type12, Iranian ballistic family.

Each missile: unique damage, speed, range, reload, cost, projectile.

---

## 3. Air defense expansion

| Object | Weapon |
|--------|--------|
| `Russia_AD_S500` | `Russia_Weapon_S500` |
| `China_AD_HQ9` | `China_Weapon_HQ9` |
| `China_AD_HQ22` | `China_Weapon_HQ22` |
| `Iran_AD_Bavar373` | `Iran_Weapon_Bavar373` |
| `Iran_AD_Khordad15` | `Iran_Weapon_Khordad15` |
| `Iran_AD_Majid` | `Iran_Weapon_Majid` |
| `Israel_AD_Barak8` | `Israel_Weapon_Barak8` |
| `Japan_AD_Type03` | `Japan_Weapon_Type03` |
| `India_AD_Barak8` | `India_Weapon_Barak8` |

Prior: Patriot, THAAD, S-400, Buk, NASAMS, Hawk, Akash, Sky Sabre, SAMP/T, IRIS-T, Pantsir, C-RAM, Iron Dome, HISAR/Siper, AntiDrone.

---

## 4. Drone warfare

Signature drones retained with Phase H suicide-doctrine deepen on Shahed-136 / Shahed Heavy (mood/vision). Full tree: recon/combat/loitering/stealth/heavy across factions + TB2/Akinci/Kizilelma/MQ-9/RQ-180/Wing Loong/Orion/S-70.

---

## 5. Building / HQ identity

Faction Military HQ remains StartingBuilding for expansion sides. Stock overlays:
- USA → **National Defense Command**
- Russia → **Strategic Military Command**
- China → **PLA Command Center**
- NK → **Supreme Command HQ**

Unique VisionRange per stock HQ. Expansion HQ DisplayNames already unique (Phase F).

---

## 6. General Stars

MIC CommandSets remain sell-only (no strategic research). Tech/nuclear/doctrines live on Science Rank menus.

---

## 7. Nuclear system

Unified NuclearStrategic sciences for: USA, Russia, China, India, Pakistan, France, Britain, North Korea.

- NK: cost 0, no prerequisite (start unlocked)
- Others: Rank8, cost 5
- Unique SpecialPower ReloadTime / RadiusCursorRadius per stock nation
- Unique nuclear weapons + projectiles per nuclear nation (different damage/radius/cooldown)
- Non-nuclear FOAB remains `IsGrantable = No`

---

## 8. Balance / sync

- Strategic TELs: `Patch_StrategicLauncher` (Avangard/PGS type limit 1)
- AD: `Patch_AirDefense`
- Elite aircraft: `Patch_EliteAircraft`
- Country balance + build limits + SYNC_MANIFEST refreshed
