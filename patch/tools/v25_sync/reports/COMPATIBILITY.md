# V25 ↔ SPECTER compatibility (stage 1, no import)

- Generated: 2026-11-11 04:59 Asia/Tehran
- V25 Objects: **6207**
- SPECTER Objects: **5450**
- Object status: `{'unique_v25': 5374, 'collision_rename': 628, 'shared_identical': 205}`
- Incomplete dependency trees: **1501**
- Protected-kind collisions (unique Weapon/CommandSet/Armor/… names): **810** (occurrence count across objects is higher; originals stay)
- V25 ART stems: 5056
- SPECTER ART stems: 2747

## Buckets

- structure: 1899
- vehicle: 1540
- aircraft: 762
- other: 508
- projectile: 495
- infantry: 493
- combat: 316
- air_defense: 194

## Sides (V25 Object Side=)

- Civilian: 1124 → SPECTER `Civilian`
- America: 405 → SPECTER `America`
- China: 336 → SPECTER `China`
- Russia: 336 → SPECTER `Russia`
- Egypt: 194 → SPECTER `Egypt`
- India: 147 → SPECTER `India`
- GLA: 137 → SPECTER `GLA`
- Japan: 137 → SPECTER `Japan`
- Israel: 135 → SPECTER `Israel`
- Germany: 132 → SPECTER `Germany`
- Pakistan: 131 → SPECTER `Pakistan`
- NorthKorea: 130 → SPECTER `NorthKorea`
- Iraq: 128 → SPECTER `Iraq`
- France: 123 → SPECTER `France`
- Turkey: 123 → SPECTER `Turkey`
- SouthKorea: 118 → SPECTER `SouthKorea`
- Ukrania: 116 → SPECTER `Ukraine`
- AmericaLaserGeneral: 115 → SPECTER `UNMAPPED — independent add required`
- Iran: 99 → SPECTER `Iran`
- Poland: 98 → SPECTER `Poland`
- Italy: 95 → SPECTER `Italy`
- SaudiArabia: 95 → SPECTER `SaudiArabia`
- Algeria: 94 → SPECTER `Algeria`
- Syria: 90 → SPECTER `Syria`
- Sweden: 89 → SPECTER `Sweden`
- Serbia: 85 → SPECTER `Serbia`
- Korea: 71 → SPECTER `SouthKorea`
- Generic: 63 → SPECTER `UNMAPPED — independent add required`
- ALL: 51 → SPECTER `UNMAPPED — independent add required`
- Ukraine: 40 → SPECTER `Ukraine`
- Premium: 38 → SPECTER `Premium`
- GLAStealthGeneral: 36 → SPECTER `UNMAPPED — independent add required`
- GLAToxinGeneral: 34 → SPECTER `UNMAPPED — independent add required`
- Flag: 33 → SPECTER `UNMAPPED — independent add required`
- USA: 27 → SPECTER `UNMAPPED — independent add required`
- IranRebels: 23 → SPECTER `UNMAPPED — independent add required`
- CG: 14 → SPECTER `UNMAPPED — independent add required`
- Boss: 13 → SPECTER `UNMAPPED — independent add required`
- GLADemolitionGeneral: 12 → SPECTER `UNMAPPED — independent add required`
- Human: 11 → SPECTER `UNMAPPED — independent add required`
- UK: 9 → SPECTER `Britain`
- TaiWan: 8 → SPECTER `UNMAPPED — independent add required`
- All: 6 → SPECTER `UNMAPPED — independent add required`
- SouthAfrica: 5 → SPECTER `SouthAfrica`
- PremiumHull: 4 → SPECTER `UNMAPPED — independent add required`
- AmericaSuperWeaponGeneral: 3 → SPECTER `UNMAPPED — independent add required`
- ChinaInfantryGeneral: 3 → SPECTER `UNMAPPED — independent add required`
- Dead: 3 → SPECTER `UNMAPPED — independent add required`
- AmericaAirForceGeneral: 2 → SPECTER `UNMAPPED — independent add required`
- SDCivilian: 2 → SPECTER `UNMAPPED — independent add required`
- system: 2 → SPECTER `UNMAPPED — independent add required`
- CWCruT80UK: 1 → SPECTER `UNMAPPED — independent add required`
- Kazakhstan: 1 → SPECTER `UNMAPPED — independent add required`
- Vietnam: 1 → SPECTER `UNMAPPED — independent add required`
- lgeria: 1 → SPECTER `UNMAPPED — independent add required`

## Named-definition overlap

| Kind | V25 | SPECTER | unique V25 | shared | identical | rename |
|---|---:|---:|---:|---:|---:|---:|
| Object | 6207 | 5450 | 5375 | 832 | 205 | 627 |
| Weapon | 1488 | 3160 | 1119 | 369 | 233 | 136 |
| CommandSet | 1369 | 1299 | 883 | 486 | 261 | 225 |
| CommandButton | 3659 | 3839 | 2832 | 827 | 383 | 444 |
| Armor | 128 | 152 | 75 | 53 | 0 | 53 |
| Locomotor | 485 | 516 | 302 | 183 | 110 | 73 |
| ObjectCreationList | 1422 | 856 | 1128 | 294 | 194 | 100 |
| FXList | 576 | 564 | 147 | 429 | 420 | 9 |
| SpecialPower | 165 | 283 | 85 | 80 | 55 | 25 |
| Upgrade | 122 | 280 | 55 | 67 | 55 | 12 |
| ParticleSystem | 1436 | 1683 | 346 | 1090 | 670 | 420 |
| PlayerTemplate | 28 | 31 | 13 | 15 | 3 | 12 |

## Engine rules (future apply — not executed)

- Existing SPECTER Objects are never edited.
- Public `CommandSet.ini` / `CommandButton.ini` / `Weapon.ini` / `Armor.ini` / `Locomotor.ini` / `PlayerTemplate.ini` are blocked.
- Colliding names become `SD25_<name>` with full reference rewrite.
- Unique V25 names keep their name and go to `Data\INI\Object\SilentDeath\<Side>\`.
- If SPECTER lacks a system (CWC rider, deploy AI, unique bomb), the object is flagged `independent_add`, never dropped.
- New air defense must keep AntiAir/AntiMissile KindOf and weapons that already match SPECTER aircraft/missile Armor/DamageType, or add companion DamageType **only in unique INI**.
- Stage 1 writes **no** game BIG.

