# Specter Patch — Phase C+D Report

## Scope
Land / Air / Missile / Technology only. **No naval content.**

## Phase C (doctrine identity)
- Per-country military doctrines (sciences + purchase buttons)
- 140+ unique projectiles with guidance profiles
- Per-country weapon families (MLRS, TankAP, ATGM, ADSAM, AAM, Ballistic)
- Infantry/vehicle identity DisplayNames
- Elite airframe tuning (KAAN, Tejas, JF-17, F-15SA, F-35, Rafale, etc.)
- Europe/Gulf PreferredColor separation

## Phase D (advanced combat systems)
- **20 elite MBTs** (Altay, Challenger 2, Leclerc, Ariete, Arjun, T-90S, Type 10, Al-Khalid, M1A2S, T-84 Oplot, etc.) wired into WarFactories
- **Cruise missile category** (20 weapons + projectiles; SOM/Babur/Neptune specials)
- **Turkey full ground weapon suite** added to expansion weapons
- **50 tech-tree sciences** + **50 signature upgrades** + **50 doctrine-gated SpecialPowers**
- **130 AAB aircraft** dual loadouts (AAM + ATGM)
- Ground doctrine stat differentiation on base MBTs
- `CountryDoctrine_PhaseCD.ini` identity reference

## Audits
- Object/Weapon/Upgrade/CommandButton/CommandSet/Science/SpecialPower collisions: **0**
- `sync_audit.py`: **PASS**
- Naval keyword scan: **clean**

## Next phase (E) recommendations
1. Wire SpecialPower shortcut CommandButtons + OCL payloads for tech powers
2. Country-unique FX/audio packs (beyond shared Specter assets)
3. Infantry elite variants with doctrine prerequisites
4. Aircraft loadout upgrade trees (AAM/AGM/precision) as researchable WeaponSet swaps
5. Deeper Europe rotary-wing identity (Italy helicopters)
