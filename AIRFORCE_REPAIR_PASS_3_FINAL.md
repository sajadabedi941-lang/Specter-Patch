# AIRFORCE REPAIR PASS 3 FINAL
Surgical repair on airforce-runway-visual-repair-v2 packed BIGs.
USA / Russia / China live CommandSets byte-identical.
Cursor cannot launch Zero Hour. Runtime-sensitive lines are STATIC PASS.

## GERMANY

### E-3 AWACS
- Object: GermanyAircraftE3
- visual: US_E3G (was stub E3)
- role: AWACS detector + SAR scan, ZERO offensive weapons
- scale: 0.90 (unchanged)
- weapons: none
- airbase: Germany Heavy slot 3
- buildable: YES
- static movement: JetAI NeedsRunway=Yes ReturnToBaseIdleTime=10000 CommandSet=E3G_CommandSet Detector+scan present
- scan: SuperweaponNatoAWACS + Superweapon_ANAPY2_SARSCANMODE radius 3600

### NH90
- Object: GermanyHelicopterNH90
- visual: LSFGENH90
- role: medium transport helicopter
- airbase: Germany Heavy slot 7 / Helicopter base
- buildable: YES
- static movement: JetAI NeedsRunway=No ChinookLocomotor Mass=50 Physics present

### CH-53
- Object: GermanyHelicopterCH53
- visual: LSFRUMi171
- role: heavy helicopter transport (TransportContain 14)
- airbase: Germany Heavy slot 8
- buildable: YES
- static movement: JetAI NeedsRunway=No ChinookLocomotor Mass=80 independent of NH90

### Eurodrone MALE
- Object: GermanyUAVEuroMALE
- visual: Nat_Heron (kept)
- role: recon / PGM UAV
- weapons: Germany_Weapon_EuroMALE_PGM (unchanged)
- airbase: Germany Heavy slot 5
- buildable: YES
- static movement: NeedsRunway=Yes KeepsParkingSpaceWhenAirborne=Yes (was NeedsRunway=No)

### Heron TP
- Object: GermanyDroneHeronTP
- visual: AVReaper (kept)
- role: runway UAV / Brimstone
- airbase: Germany Heavy slot 4
- buildable: YES
- static movement: NeedsRunway=Yes KeepsParkingSpaceWhenAirborne=Yes (was NeedsRunway=No)

### Alpha Jet
- Object: GermanyJetAlphaJet
- visual: qsnt50 (was AVHawk)
- role: light attack / trainer (weapons unchanged)
- airbase: Germany Fighter/Large slot 10
- buildable: YES

### Tornado IDS Strike Bomber
- Object: GermanyJetTornadoIDS (existing; not invented B-2)
- visual: LSFTornado (kept)
- role: heavy tactical strike / bomber
- weapons: PRIMARY Germany_Weapon_Taurus x2 (Kh59MK2_Object); SECONDARY GermanyJetTornadoIDS_WpnBombHvy x6 (GBU24_GuidedBombObject, PreAttackDelay 2800, DelayBetweenShots 2200); TERTIARY GermanyJetTornadoIDS_WpnIR2 x2 (AIM-9X_Object)
- airbase: Germany Fighter/Large slot 7 (existing safe slot; Rally/Sell/AWACS untouched)
- buildable: YES
- NO nuclear weapon

## SYRIA

### MiG-21bis
- Object: SyriaJetMig21
- visual: UVMig-21
- scale: 0.82 -> 0.94
- airbase: Syria Airfield slot 5
- buildable: YES

### Mirage F1BA
- Object: Syria_MirageF1_Bq (no object named F1BA)
- lock removed: Prerequisites Object=Syria_RadarStation only
- cost/time kept: 1492 / 20.2s
- weapons/visual kept
- airbase: Syria Airfield slot 2
- buildable: YES (BUILDABLE_FROM_CORRECT_SYRIAN_AIRBASE)

### MiG-21MF
- Object: SyriaJetMig21MF
- visual: UVMig-21
- scale: 0.80 -> 0.96 (independent of bis)
- airbase: slot 6
- buildable: YES

### Su-25K
- Object: Syria_Su-25K
- visual: RUS_SU25T (was Irq_Su25k)
- role: ground-attack (weapons kept)
- airbase: slot 10
- buildable: YES

### L-39ZA
- Object: SyriaJetL39
- visual: AGMZRT501 (was AVHawk)
- role: trainer / light attack
- airbase: slot 12
- buildable: YES

## INDIA

### MiG-21 Bison
- Object: IndiaJetMig21Bison
- visual: LSFIDMig21
- scale: 0.84 -> 0.90 (below Su-30MKI 0.92)
- airbase: India Airfield slot 8
- buildable: YES

### MiG-29A
- Object: India_Mig-29A
- visual: LSFruMiG29 (was Irq_Mig29A)
- role/weapons kept (4x_R27_MRBVR_Mig29A)
- airbase: slot 2
- buildable: YES

### Tejas Mk1A
- Object: IndiaJetTejas (India_Tejas does not exist in packed DATA)
- visual: NVJ31
- scale: 0.86 -> 0.90
- airbase: slot 11
- buildable: YES

## UAE

### Hawk 102
- Object: UAEJetHawk102
- visual: UV_Turbo (was AVHawk)
- role kept
- airbase: UAE Airfield slot 11
- buildable: YES

## SAUDI ARABIA

### Lightning F.53
- Object: SaudiJetLightning (not F-35)
- visual: AVLightn kept
- scale: 0.86 -> 1.02
- airbase: slot 11
- buildable: YES

### Hawk 65
- Object: SaudiJetHawk65
- visual: AVHawk kept
- scale: 0.80 -> 0.82 (trainer, not F-15)
- airbase: slot 10
- buildable: YES

### F-5E Tiger II
- Object: SaudiJetF5E
- visual: AVHawk kept (usable)
- scale: 0.78 -> 0.88
- airbase: slot 12
- buildable: YES

## PAKISTAN

### Mirage ROSE III
- Object: PakistanJetMirageROSE
- visual: UVMirage
- scale: 0.90 -> 1.06
- airbase: slot 11
- buildable: YES

### F-7PG
- Object: PakistanJetF7PG
- visual: LSFPKJ7
- scale: 0.86 -> 0.96
- airbase: slot 7
- buildable: YES

### F-7P
- Object: PakistanJetF7P
- visual: LSFJ7
- scale: 0.84 -> 0.94 (independent of F-7PG)
- airbase: slot 8
- buildable: YES

### F-16C Block 52
- Object: Pakistan_F16Blk52
- visual: US_F16CJ_blk52 kept
- fire fix: default 3-slot WeaponSet using packed AMLU weapons (AIM-120-style x4, AIM-9-style x2, bombs x4); WeaponLaunchBone Weapon01/Weapon02; NeedsRunway=Yes; empty Prerequisites stripped; OutOfAmmoDamage 0%
- USA F-16 untouched
- airbase: Pakistan Airfield slot 2
- buildable: YES
- PAKISTAN_F16C_BLOCK52_FIRE_STATIC = PASS

## BUILD LOCK AUDIT

- Syria_MirageF1_Bq: RadarStation prerequisite removed. No Science/Rank/Upgrade gate remained.
- Pakistan_F16Blk52: empty Prerequisites block removed (commented AmericaAirfield).
- Other units in this pass: no unexpected Science/Rank/Upgrade locks on the live objects.
- Country airbase producer prerequisites were not stripped from legitimate airbase buildings.

## PROTECTED HASHES

- AmericaAirfieldCommandSet: f4a896d6012324869846c37ce8ecf64a8ca02cfa9bc0ae1fc7127ef8292ba660 (unchanged YES)
- America_LargeAirBaseCommandSet: 9045e025345dfb25d57ec19ec69361f7782be017f28ac44be598cba5b6c9c3b1 (unchanged YES)
- America_HeavyAirBaseCommandSet: edb4436a870f2a7b4595b3f5a5be3a1b27769702848b59d36663a80294b0c2e3 (unchanged YES)
- RussiaAirfieldCommandSet: 574bfe4c65d49deff7bf3624d22bcb6e4570ed99871e74379a8b78f8cbfa6eb1 (unchanged YES)
- Russia_LargeAirBaseCommandSet: 20cf43d97715d4eb8a40a25617ea8562125b3f3b2b966a503d733a34bf0117ac (unchanged YES)
- Russia_HeavyAirBaseCommandSet: 4d98bbc64f76cf2beba2c7e8f9448b9f2e0f4cef382e6e77b75009fbfdf1ca2f (unchanged YES)
- PLAAirfieldCommandSet: 522862c4d7e9e5568ed44bd3377da95632e3afe8725d24694b4c5d2d90b9dadb (unchanged YES)
- China_LargeAirBaseCommandSet: afdecf56f3b8e16fd59e79ef76bc99a439fae12d78ff3c68604dc7172261806e (unchanged YES)
- China_HeavyAirBaseCommandSet: 2fc489c13960283dac231a9aa611ac72c40443e6236686e03804cb3a07a61c90 (unchanged YES)

## PACK

- DATA SHA256: `aecdbfee8cff133114fe69c4ea816d3c6c2427aefb06b083db7ecc7dfa9fc75d`
- ART SHA256: `2255a132b5e68bc69d941bc7d5fa1dcb617c323db47bd502bef89af96eb4289e`
- ART is the pass-2 ART archive (no new W3D import required; all selected meshes already packed).
- BIG_REEXTRACT confirmed patched objects in extracted canonical INIs.

## REQUIRED PASS MATRIX

GERMANY_E3_AWACS = PASS
GERMANY_E3_ZERO_WEAPONS = PASS

GERMANY_NH90_FLIGHT_STATIC = PASS
GERMANY_CH53_FLIGHT_STATIC = PASS

GERMANY_EURODRONE_TAKEOFF_STATIC = PASS
GERMANY_EURODRONE_LANDING_STATIC = PASS

GERMANY_HERON_TP_TAKEOFF_STATIC = PASS
GERMANY_HERON_TP_LANDING_STATIC = PASS

GERMANY_ALPHAJET_NEW_VISUAL = PASS
GERMANY_TORNADO_IDS_STRIKE_BOMBER = PASS

SYRIA_MIG21BIS_SCALE = PASS
SYRIA_MIRAGE_F1BA_BUILDABLE = PASS
SYRIA_MIG21MF_SCALE = PASS
SYRIA_SU25K_NEW_VISUAL = PASS
SYRIA_L39ZA_NEW_VISUAL = PASS

INDIA_MIG21_BISON_SCALE = PASS
INDIA_MIG29A_NEW_VISUAL = PASS
INDIA_TEJAS_MK1A_SCALE = PASS

UAE_HAWK102_NEW_VISUAL = PASS

SAUDI_LIGHTNING_F53_SCALE = PASS
SAUDI_HAWK65_SCALE = PASS
SAUDI_F5E_SCALE = PASS

PAKISTAN_MIRAGE_ROSE3_SCALE = PASS
PAKISTAN_F7PG_SCALE = PASS
PAKISTAN_F7P_SCALE = PASS
PAKISTAN_F16_BLOCK52_FIRE_STATIC = PASS

VISUAL_DIVERSITY = PASS
SCALE_AUDIT = PASS
AWACS_STANDARDIZATION = PASS
WEAPON_REFERENCE_AUDIT = PASS

DUPLICATE_OBJECT_AUDIT = PASS
DUPLICATE_WEAPON_AUDIT = PASS
DUPLICATE_COMMANDBUTTON_AUDIT = PASS
DUPLICATE_COMMANDSET_AUDIT = PASS

INVALID_ANIMATION_AUDIT = PASS
W3D_EXISTENCE_AUDIT = PASS
TEXTURE_DEPENDENCY_AUDIT = PASS

USA_PROTECTED = PASS
RUSSIA_PROTECTED = PASS
CHINA_PROTECTED = PASS

BIG_REEXTRACT = PASS
STATIC_INITIALIZATION_VALIDATION = PASS

READY FOR USER RUNTIME TEST = YES

Honesty: STATIC PASS only. Not tested in a live Zero Hour session.
