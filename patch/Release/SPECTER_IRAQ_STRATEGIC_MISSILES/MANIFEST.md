# SPECTER Iraqi Strategic Missile Family — Manifest

Authority: live s `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big` only.
Static validation only. Not an in-game runtime test.

## Donor and identity

| Missile | Object | TEL donor W3D | Missile donor W3D | Private TEL tex | Private MSL tex | Scale | PScale | Cost | Time | Dmg | Rad | Range | Reload ms | Weapon | Projectile | Button |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AL-HUSSEIN | Iraq_AlHussein_New | Irq_9P117 | Irq_R11_M | IQ_AlHusseinTEL.tga | IQ_AlHusseinMSL.tga | 1.30 | 1.28 | 6000 | 45 | 2500 | 110 | 1600 | 110000 | Weapon_Iraq_AlHussein_New | Projectile_Iraq_AlHussein_New | Command_ConstructIraq_AlHussein_New |
| AL-HIJARAH | Iraq_AlHijarah_New | Irq_9P117 | Irq_R11_M | IQ_AlHijarahTEL.tga | IQ_AlHijarahMSL.tga | 1.25 | 1.22 | 6500 | 48 | 2200 | 90 | 1720 | 95000 | Weapon_Iraq_AlHijarah_New | Projectile_Iraq_AlHijarah_New | Command_ConstructIraq_AlHijarah_New |
| AL-ABBAS | Iraq_AlAbbas_New | Irq_Abbas_L | Irq_AbbasM | IQ_AlAbbasTEL.tga | IQ_AlAbbasMSL.tga | 1.40 | 1.38 | 7000 | 52 | 1800 | 85 | 2200 | 100000 | Weapon_Iraq_AlAbbas_New | Projectile_Iraq_AlAbbas_New | Command_ConstructIraq_AlAbbas_New |
| BADR-2000 | Iraq_Badr2000_New | RUS_9K720K | Hwasong7 | IQ_Badr2000TEL.tga | IQ_Badr2000MSL.tga | 1.42 | 1.40 | 8500 | 60 | 2800 | 120 | 2100 | 130000 | Weapon_Iraq_Badr2000_New | Projectile_Iraq_Badr2000_New | Command_ConstructIraq_Badr2000_New |
| AL-SAMOUD | Iraq_AlSamoud_New | Irq_Sarab7 | Irq_R11_M | IQ_AlSamoudTEL.tga | IQ_AlSamoudMSL.tga | 0.80 | 0.82 | 3000 | 28 | 800 | 40 | 480 | 45000 | Weapon_Iraq_AlSamoud_New | Projectile_Iraq_AlSamoud_New | Command_ConstructIraq_AlSamoud_New |
| ABABIL-100 | Iraq_Ababil100_New | Irq_Lamiaa | Irq_Alraad2M | IQ_Ababil100TEL.tga | IQ_Ababil100MSL.tga | 0.75 | 0.76 | 2500 | 24 | 500 | 32 | 420 | 32000 | Weapon_Iraq_Ababil100_New | Projectile_Iraq_Ababil100_New | Command_ConstructIraq_Ababil100_New |
| TAMMUZ-1 | Iraq_Tammuz1_New | Iraq_Alhusain_L | Iraq_Alhusain_M | IQ_Tammuz1TEL.tga | IQ_Tammuz1MSL.tga | 1.60 | 1.55 | 12000 | 75 | 4000 | 150 | 2900 | 160000 | Weapon_Iraq_Tammuz1_New | Projectile_Iraq_Tammuz1_New | Command_ConstructIraq_Tammuz1_New |
| AL-ABID | Iraq_AlAbid_New | RUS_RS24 | RUS_RS24M | IQ_AlAbidTEL.tga | IQ_AlAbidMSL.tga | 1.70 | 1.68 | 15000 | 90 | 5500 | 180 | 3900 | 190000 | Weapon_Iraq_AlAbid_New | Projectile_Iraq_AlAbid_New | Command_ConstructIraq_AlAbid_New |

## Shared command / production

- CommandSet (TELs): `Iraq_StrategicMissileNewCommandSet`
- CommandSet (factory): `Iraq_MissileFactoryCommandSet`
- Factory object: `Iraq_MissileFactory`
- Factory button (core CommandButton.ini): `Command_ConstructIraq_MissileFactory`
- VT72B slot 14: Missile Factory (Worker Clear Mines unchanged)

## Wreck / damage notes

- **AL-HUSSEIN**: cloned Irq_9P117D / Irq_9P117R
- **AL-HIJARAH**: cloned Irq_9P117D / Irq_9P117R
- **AL-ABBAS**: cloned Irq_Abbas_L_D / Irq_Abbas_L_R
- **BADR-2000**: no dedicated R W3D; damaged/wreck use cloned RUS_9K720KD
- **AL-SAMOUD**: cloned Irq_Sarab7R; damaged uses painted Irq_Sarab7 (donor has no D W3D)
- **ABABIL-100**: Irq_Lamiaa has no D/R W3D; damaged/wreck reuse painted clones of Irq_Lamiaa
- **TAMMUZ-1**: Iraq_Alhusain_L has no D/R W3D in live ART; damaged/wreck reuse darkened clones
- **AL-ABID**: cloned RUS_RS24_D / RUS_RS24_R

## Honest geometry limits

- Al-Hussein / Al-Hijarah share cloned `Irq_9P117` + `Irq_R11_M` (Scale + private paint distinguish them).
- Al-Samoud uses the same `Irq_R11_M` donor at 0.82 on a cloned `Irq_Sarab7` TEL.
- Al-Abid (`RUS_RS24M`) and Tammuz-1 (`Iraq_Alhusain_M`) share the `irq_projectiles_c` mesh family; distinction is TEL, Scale, and stage-band paint.
- Badr-2000 two-stage look uses `Hwasong7` (closest live two-stage missile W3D). No Iraqi Condor-II mesh exists in s.
- Tammuz-1 / Al-Abid gameplay numbers are SPECTER balance, not historical combat statistics.

## SHA256

- `_SPEC_DATA_ONE.big` 366430287 SHA256=ae5772f500329dad76a0bdf1339a8d9b767317708275f8bc9f2f3c7d0bab7315
- `_SPEC_ART_ONE.big` 1302315536 SHA256=5b96933007ddcffc633af4089adf64eae1576b5e83cb44707ff8fb27e10c95ab
- `SPECTER_IRAQ_STRATEGIC_MISSILES.zip` 1668746067 SHA256=35c329051cbf37096290b400d7cc62ea0f3e7350eb9bd06a6de669a4695c4959
