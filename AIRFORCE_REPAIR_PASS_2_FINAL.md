# Air Force Repair Pass 2 Final

USA E-3 packed donor objects (untouched): US_E3G_AWACS and AmericaJetE3Visual.
Donor modules referenced by local wrappers: StealthDetectorUpdate, SpecialAbility SuperweaponNatoAWACS, OCLSpecialPower Superweapon_ANAPY2_SARSCANMODE, JetAIUpdate NeedsRunway=Yes, CMF56_2_Turbofan_engine + BasicJetTaxiLocomotor.
SpectreGunshipUpdate was NOT copied (that orbit module is why local AWACS failed to take off/land). Packed USA/Russia/China object files were hash-verified unchanged.

## TURKEY
NF-5A: old AVHawk -> new UVVampire (packed ART UVVampire, compact vintage jet stand-in; no dedicated F-5/Tiger II W3D in donor/packed ART)
Hurjet: old AVHawk -> new LSFT50 (packed ART, T-50 class)
AWACS: old TurkeyJetE3AAWACS (Rank3 + SpectreGunship) -> TurkeyAircraftE3AWACS; scan SpecialPower; weapons = NONE

## SOUTH AFRICA
Hawk120 visual: UVVampire
Hawk127 visual: AVHawk
Impala visual: UV_Turbo
Mirage IIICZ scale: 0.86 -> 1.08 (ref FranceJetMirageF1CT 0.85 / TurkeyJetF16C 0.90)
IL-76 status: playable SouthAfricaJetIL76, science SouthAfrica_IL-76 left for paradrop
helicopters added: Rooivalk (LSFFRTiger), Oryx (NAT_Puma); Mi-8T kept and converted to JetAI NeedsRunway=No

## LIBYA
Mirage F1BA: treated as Libya_MirageF1_Bq (no F1BA object exists). Radar prerequisite removed. BUILDABLE_FROM_CORRECT_AIRBASE
MiG-21MF scale/loadout: 0.80 -> 0.96; IR + GenericUnguidedRockets + gun
MiG-21bis scale/loadout: 0.82 -> 0.92; IR + gun + 4 heavier Fab-250
IL-76: playable LibyaJetIL76
helicopters: Mi-8T kept/fixed + Mi-24 (Iraq_Mi-35M3)

## UKRAINE
AWACS: UkraineAircraftE3AWACS replacing UkraineJetE3AAWACS menu target
MiG-29 scale: 0.88 -> 0.96 (below Su-27 0.98)
MiG-21bis scale/loadout: 0.82 -> 0.94; tertiary UkraineJetMig21_WpnBombMed ClipSize 4 (GBU24_GuidedBombObject)

## SWEDEN
EF2000TrancheF: no object by that name. Unlocked SwedenJetEF2000T4 (and T4_AA / T4_CAS) by removing StrategyCenter + SCIENCE_Rank5
SK60 visual: AGMZRT501
SK60B visual: AVHawk_D1

## ITALY
M339 visual: qsnt50
M346 visual: LSFT50d
EF2000T4 visual: ItalyJetTyphoon EVTyphoon
NH90/AW101/AW139: ChinookAIUpdate -> JetAIUpdate NeedsRunway=No
MQ-9: NeedsRunway=Yes
G550: USA E-3 scan/detector, KVE737 visual, zero weapons, no Animation=
C-130 bomber: ItalyJetC130J (C-130J) + ItalyJetC130J_WpnHeavy ClipSize 8 GBU-24 class
C-27J gunship: GAU23A + L60 Bofors + M102 105mm (existing packed weapons, no turret bones)

## FRANCE
E-3 AWACS: US_E3G visual + USA E-3 scan/detector + runway JetAI
NH90 Caiman: JetAIUpdate NeedsRunway=No
nEUROn visual: AV_RQ180; NeedsRunway=Yes
Rafale: C/B/M/F4/F3 have no object Prerequisites (C/B/M already unlocked in INI). Fighter airbase CommandSet FranceAirfieldCommandSet slots 1-5. No France_Rafale object exists.

## SCALE TABLE
| Aircraft | Old Scale | New Scale | Reference |
|---|---|---|---|
| SouthAfricaJetMirageIIICZ | 0.86 | 1.08 | FranceJetMirageF1CT 0.85 / TurkeyJetF16C 0.90 |
| LibyaJetMig21MF | 0.80 | 0.96 | IndiaJetMig21Bison 0.84 / F-16 0.90 |
| LibyaJetMig21 | 0.82 | 0.92 | same UVMig-21 family, offset from MF |
| UkraineJetMig29 | 0.88 | 0.96 | UkraineJetSu27 0.98 ceiling |
| UkraineJetMig21 | 0.82 | 0.94 | IndiaJetMig21Bison 0.84 / F-16 0.90 |

## MATRIX
TURKEY_NF5A_VISUAL = PASS
TURKEY_HURJET_VISUAL = PASS
TURKEY_NF5A_HURJET_DISTINCT = PASS
TURKEY_E3_AWACS = PASS
SOUTH_AFRICA_HAWK120_VISUAL = PASS
SOUTH_AFRICA_HAWK127_VISUAL = PASS
SOUTH_AFRICA_IMPALA_VISUAL = PASS
SOUTH_AFRICA_VISUAL_DIVERSITY = PASS
SOUTH_AFRICA_MIRAGE3_SCALE = PASS
SOUTH_AFRICA_IL76_STATIC = PASS
SOUTH_AFRICA_HELICOPTERS = PASS
LIBYA_MIRAGE_F1BA_BUILDABLE = PASS
LIBYA_MIG21MF_SCALE = PASS
LIBYA_MIG21BIS_SCALE = PASS
LIBYA_MIG21_LOADOUTS_DISTINCT = PASS
LIBYA_IL76_STATIC = PASS
LIBYA_HELICOPTERS = PASS
UKRAINE_E3_AWACS = PASS
UKRAINE_MIG29_SCALE = PASS
UKRAINE_MIG21BIS_SCALE = PASS
UKRAINE_MIG21BIS_NEW_BOMBS = PASS
SWEDEN_EF2000_BUILDABLE = PASS
SWEDEN_SK60_VISUAL = PASS
SWEDEN_SK60B_VISUAL = PASS
SWEDEN_SK60_SK60B_DISTINCT = PASS
ITALY_M339_VISUAL = PASS
ITALY_M346_VISUAL = PASS
ITALY_EF2000T4_VISUAL = PASS
ITALY_THREE_VISUALS_DISTINCT = PASS
ITALY_NH90_FLIGHT_STATIC = PASS
ITALY_AW101_FLIGHT_STATIC = PASS
ITALY_AW139_FLIGHT_STATIC = PASS
ITALY_MQ9_LANDING_STATIC = PASS
ITALY_G550_AWACS = PASS
ITALY_G550_ZERO_WEAPONS = PASS
ITALY_C130_BOMBER = PASS
ITALY_C27J_AC130_FIRE = PASS
FRANCE_E3_AWACS = PASS
FRANCE_NH90_FLIGHT_STATIC = PASS
FRANCE_NEURON_NEW_VISUAL = PASS
FRANCE_NEURON_TAKEOFF_LANDING = PASS
FRANCE_RAFALE_BUILDABLE = PASS
AWACS_STANDARDIZATION = PASS
VISUAL_DIVERSITY = PASS
IL76_COMMON_FIX = PASS
DUPLICATE_DEFINITION_AUDIT = PASS
INVALID_ANIMATION_AUDIT = PASS
W3D_DEPENDENCY_AUDIT = PASS
USA_RUSSIA_CHINA_PROTECTED = PASS
BIG_REEXTRACT = PASS
STATIC_INITIALIZATION_VALIDATION = PASS
ITALY_C130_HEAVY_BOMB_COUNT = 8

STATIC STARTUP VALIDATION: PASS -- USER RUNTIME TEST REQUIRED
