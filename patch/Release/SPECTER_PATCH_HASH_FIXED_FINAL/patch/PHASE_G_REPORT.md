# Phase G Report — Deep Weapon / Platform / Country Identity

**Scope:** LAND / AIR / MISSILE / DRONE / DEFENSE only. No naval.

**Audits:** Object/Weapon/Upgrade/CommandButton/CommandSet/Science/SpecialPower collisions = **0**. `sync_audit.py` = **PASS**. Naval keyword scan on Phase G files = **clean**.

---

## 1. Advanced fighters (missing only)

| Object | Role | Unique weapon | Notes |
|--------|------|---------------|-------|
| `Patch_America_B21` | Strategic bomber | `America_Weapon_B21_JASSM` → `America_Projectile_B21_JASSM` | Limit 2 (elite aircraft link); AAB USA |
| `Patch_Russia_Su75` | Light 5th-gen | `Russia_Weapon_R77_Su75` → `Russia_Projectile_Su75_R77` | Distinct from Su-57; AAB Russia |
| `Turkey_F16Block70` | AESA fighter | `Turkey_Weapon_AIM120D_F16Block70` | Gated by `SCIENCE_Turkey_TechF16Block70` |
| `India_TejasMk2` | Indigenous fighter | `India_Weapon_AstraMk2_TejasMk2` | Gated by `SCIENCE_India_TechTejasMk2` |
| `Pakistan_JF17BlockIII` | PL-15E class | `Pakistan_Weapon_PL15E_JF17BlockIII` | Gated by `SCIENCE_Pakistan_TechJF17BlockIII` |

**Skipped (already present with unique loadouts):** F-22, F-35 variants, Su-57, S-70 Okhotnik, J-20, J-35, J-10C, KAAN, Kizilelma, Tejas, Su-30MKI, JF-17, F-35J, F-2, Rafale, Eurofighter/Typhoon, Gripen.

---

## 2. Country missile identity

Existing unique TELs/projectiles retained (not renamed duplicates):

Iran Khorramshahr / Sejjil / Fateh · Turkey Tayfun · India BrahMos / Agni · Pakistan Shaheen / Ababeel · China DF-21 · Russia Kinzhal / Iskander · USA Tomahawk / JASSM · Japan Type 12

**Phase G addition:**

| Object | Weapon | Projectile | Identity |
|--------|--------|------------|----------|
| `America_PrSMTEL` | `America_Weapon_PrSM` | `America_PrSM_Projectile` | PrSM: high damage, long range, long reload; HQ-buildable; strategic launcher limit |

---

## 3. Advanced air defense network

### Long range
| Object | Weapon | Range / reload identity |
|--------|--------|-------------------------|
| `America_AD_Patriot` | `America_Weapon_Patriot` | 650 / ClipReload 18000 |
| `America_AD_THAAD` | `America_Weapon_THAAD` | 800 / 24000 |
| `Russia_AD_S400` | `Russia_Weapon_S400` | 720 / 20000 |
| `Japan_AD_Patriot` | `Japan_Weapon_PatriotPAC3` | 660 / 18500 |
| `France_AD_SAMPT` | `France_Weapon_SAMPT` | 640 / 19000 |

### Medium
| Object | Weapon | Range / reload |
|--------|--------|----------------|
| `Russia_AD_Buk` | `Russia_Weapon_Buk` | 420 / 12000 |
| `America_AD_NASAMS` | `America_Weapon_NASAMS` | 380 / 10000 |
| `India_AD_Akash` | `India_Weapon_Akash` | 480 / 15000 |
| `Britain_AD_SkySabre` | `Britain_Weapon_SkySabre` | 500 / 14500 |
| `Germany_AD_IRIST` | `Germany_Weapon_IRISTSLM` | 470 / 13000 |
| `America_AD_Hawk` | `America_Weapon_Hawk` | 320 / 14000 |

### Short / anti-drone (prior phases, retained)
Pantsir · C-RAM · Iron Dome · AntiDrone EW batteries

Deploy-style long-range batteries use unique SECONDARY/TERTIARY weapons (no shared `S400R_Deploy` on Phase G named systems). Ground AD `AutoReloadsClip = Yes`.

Wired into faction War Factories / USA·Russia·China Military HQ production.

---

## 4. Drone warfare tree (identity deepen)

| Platform | Endurance / AI tuning |
|----------|----------------------|
| Turkey TB2 / Akıncı / Kızılalma | Distinct vision, RTB idle, ammo endurance, HP |
| Iran Shahed-136 / Shahed Heavy | Long endurance loitering profiles |
| USA MQ-9 Reaper | High vision, long RTB |
| China Wing Loong II | Medium-long endurance |
| Russia Orion / S-70 Okhotnik | Combat vs stealth-heavy split |

---

## 5. Ground elite vehicle identity

Unique tertiary ATGM weapons (damage / reload / speed differ):

Altay · Arjun · T-90S · Type 10 · Oplot · Al-Khalid · Leclerc · Leopard 2A8

Plus HP / vision identity per chassis.

---

## 6. General Star control

MIC CommandSets remain sell-only (no strategic upgrades).

New aircraft sciences on Rank3 General Star menus:

- `SCIENCE_India_TechTejasMk2`
- `SCIENCE_Turkey_TechF16Block70`
- `SCIENCE_Pakistan_TechJF17BlockIII` (existing)

---

## 7. Balance / limits

- Elite aircraft: `MaxSimultaneousLinkKey = Patch_EliteAircraft` (global 4; B-21 uses type limit 2)
- AD: `Patch_AirDefense`
- Strategic TELs: `Patch_StrategicLauncher`
- Powerful AD/missiles: high BuildCost, long ClipReloadTime

---

## Files touched (Phase G)

- `CommandButton_PhaseG_Identity.ini`, `FactionExpansion_PhaseG_Strings.txt`
- `Weapon_FactionExpansion.ini`, `Projectile_FactionExpansion_PhaseC.ini`
- `Aircraft_AAB_Global.ini` (B-21, Su-75)
- New AD / PrSM / fighter INIs under faction + PatchSystems folders
- CommandSets: AdvancedAirBase, FactionExpansion_Armies, Turkey
- Sciences: India, Turkey
- Elite tanks + signature drones
- `PHASE_G_REPORT.md`, `SYNC_MANIFEST.sha256`
