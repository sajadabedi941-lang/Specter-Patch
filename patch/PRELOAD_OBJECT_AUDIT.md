# PRELOAD_OBJECT_AUDIT.md

Scan of packed DATA for `KindOf` containing **PRELOAD**.

## Summary

- New-vs-#413 PRELOAD objects whose default Model is missing from SPEC ART: **0** (models may still live in EnglishZH).
- New-vs-#413 PRELOAD objects with Animation= on a SPEC W3D that has zero animation chunks: **0** after v1/v2 repairs.
- Pre-#414 PRELOAD objects with the E-7-class pattern (Animation= on 0-anim W3D): **128**. Present in #413; user booted #414. Not stripped.

## Repaired PRELOAD Draw

| Object | Model | Was | Now |
|---|---|---|---|
| ItalyAircraftG550CAEW | KVE737 | Animation=KVE737.KVE737 on 0-anim W3D | static Model= only |
| GermanyHelicopterH145M | LSFFenneck | Animation=LSFFENNECK.LSFFENNECK on 0-anim W3D | static Model= only |
| BritainAircraftE7 | KVE737 | fixed in PR #422 | static Model= only |

## New PRELOAD air / airbase objects (post-#413 files)

- `ArabJetMig29` in `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMig29.ini` models=['Irq_Mig29A', 'Irq_Mig29A', 'Irq_Mig29A', 'Irq_Mig29A'] — PASS
- `ArabJetMirage2000` in `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMirage2000.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `ArabJetMirageF1` in `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMirageF1.ini` models=['Irq_MirageF1_Bq', 'Irq_MirageF1_Bq', 'Irq_MirageF1_Bq', 'Irq_MirageF1_Bq'] — PASS
- `ArabJetSu25` in `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetSu25.ini` models=['Irq_Su25k', 'Irq_Su25k', 'Irq_Su25k', 'Irq_Su25k'] — PASS
- `BritainAircraftE7` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini` models=['KVE737', 'KVE737', 'KVE737', 'KVE737'] — PASS
- `BritainAircraftTornadoECR` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftTornadoECR.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `BritainBomberVulcan` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainBomberVulcan.ini` models=['LSFUSAB52', 'LSFUSAB52d', 'LSFUSAB52d', 'LSFUSAB52d'] — PASS
- `BritainDroneMQ9` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainDroneMQ9.ini` models=['AVReaper', 'AVReaper_D', 'AVReaper_D'] — PASS
- `BritainJetA400M` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetA400M.ini` models=['IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew'] — PASS
- `BritainJetC17` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetC17.ini` models=['IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew'] — PASS
- `BritainJetF35B` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini` models=['ENF35A', 'ENF35A', 'ENF35A', 'ENF35A'] — PASS
- `BritainJetHarrierGR9` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHarrierGR9.ini` models=['LSFAV8B', 'LSFAV8Bd', 'LSFAV8Bd', 'LSFAV8Bd'] — PASS
- `BritainJetHawk200` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHawk200.ini` models=['LSFF16', 'LSFF16d', 'LSFF16d', 'LSFF16d'] — PASS
- `BritainJetJaguarGR3` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetJaguarGR3.ini` models=['LSFFRF1', 'LSFFRF1d', 'LSFFRF1d', 'LSFFRF1d'] — PASS
- `BritainJetLightningF6` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetLightningF6.ini` models=['AVLightn', 'AVLightn_D', 'AVLightn_D', 'AVLightn_D'] — PASS
- `BritainJetPhantomFG1` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFG1.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `BritainJetPhantomFGR2` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFGR2.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `BritainJetSeaHarrierFA2` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetSeaHarrierFA2.ini` models=['US_FA18E', 'US_FA18F', 'US_FA18F', 'US_FA18F'] — PASS
- `BritainJetTempest` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTempest.ini` models=['SPEC_OLD_F35', 'SPEC_OLD_F35', 'SPEC_OLD_F35', 'SPEC_OLD_F35'] — PASS
- `BritainJetTornadoF3` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoF3.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `BritainJetTornadoGR4` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoGR4.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `BritainJetTyphoonFGR4` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonFGR4.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `BritainJetTyphoonT3` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonT3.ini` models=['NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4'] — PASS
- `BritainJetVampireFB5` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetVampireFB5.ini` models=['UV_Turbo', 'UV_Turbo_D', 'UV_Turbo_D', 'UV_Turbo_D'] — PASS
- `BritainJetVampireFB9` in `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetVampireFB9.ini` models=['UVVampire', 'UVVampire_D', 'UVVampire_D', 'UVVampire_D'] — PASS
- `Britain_HelicopterBase` in `Data\INI\Object\Specter\British Armed Forces\Buildings\Britain_HelicopterBase.ini` models=['HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort'] — PASS
- `BritainHelicopterApache` in `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterApache.ini` models=['LSFAH64D', 'LSFAH64Dd', 'LSFAH64Dd'] — PASS
- `BritainHelicopterChinook` in `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterChinook.ini` models=['US_CH47F', 'US_CH47F', 'US_CH47F'] — PASS
- `BritainHelicopterMerlin` in `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterMerlin.ini` models=['LSFGENH90', 'LSFGENH90', 'LSFGENH90'] — PASS
- `BritainHelicopterPuma` in `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterPuma.ini` models=['LSFRUMi171', 'LSFRUMi171d', 'LSFRUMi171k'] — PASS
- `BritainHelicopterWildcat` in `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterWildcat.ini` models=['LSFLynxAHMK', 'LSFLynxAHMK', 'LSFLynxAHMK'] — PASS
- `FranceAircraftE3` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceAircraftE3.ini` models=['E3', 'E3', 'E3', 'E3'] — PASS
- `FranceJetC130` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130.ini` models=['LSFUSAC130', 'LSFUSAC130', 'LSFUSAC130d', 'LSFUSAC130d'] — PASS
- `FranceJetFCASNGF` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetFCASNGF.ini` models=['LSFJ20', 'LSFJ20', 'LSFJ20', 'LSFJ20'] — PASS
- `FranceJetMirage2000` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `FranceJetMirage20005F` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage20005F.ini` models=['FraMirage2000', 'FraMirage2000', 'FraMirage2000', 'FraMirage2000'] — PASS
- `FranceJetMirage2000D` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000D.ini` models=['LSFMirage2KD', 'LSFMirage2KDd', 'LSFMirage2KDd', 'LSFMirage2KDd'] — PASS
- `FranceJetMirage5` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage5.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `FranceJetMirageF1CR` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CR.ini` models=['UVMirage', 'UVMirage_D', 'UVMirage_D', 'UVMirage_D'] — PASS
- `FranceJetMirageF1CT` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CT.ini` models=['LSFFRF1', 'LSFFRF1d', 'LSFFRF1d', 'LSFFRF1d'] — PASS
- `FranceJetMirageIIIE` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageIIIE.ini` models=['LSFMirage3', 'LSFMirage3d', 'LSFMirage3d', 'LSFMirage3d'] — PASS
- `FranceJetRafaleB` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleB.ini` models=['LSFRafale', 'LSFRafaled', 'LSFRafaled', 'LSFRafaled'] — PASS
- `FranceJetRafaleC` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleC.ini` models=['LSFRafale', 'LSFRafaled', 'LSFRafaled', 'LSFRafaled'] — PASS
- `FranceJetRafaleF4` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleF4.ini` models=['LSFIDRafale', 'LSFIDRafaled', 'LSFIDRafaled', 'LSFIDRafaled'] — PASS
- `FranceJetRafaleM` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleM.ini` models=['LSFRafaleAS', 'LSFRafaleASd', 'LSFRafaleASd', 'LSFRafaleASd'] — PASS
- `FranceUCAVNeuron` in `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceUCAVNeuron.ini` models=['CHI_GJ11L', 'CHI_GJ11LD', 'CHI_GJ11LD', 'CHI_GJ11LD'] — PASS
- `France_HelicopterBase` in `Data\INI\Object\Specter\French Armed Forces\Buildings\France_HelicopterBase.ini` models=['HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort'] — PASS
- `FranceHelicopterCaracal` in `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterCaracal.ini` models=['LSFRUMi171', 'LSFRUMi171d', 'LSFRUMi171k'] — PASS
- `FranceHelicopterNH90` in `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterNH90.ini` models=['LSFFRNH90', 'LSFFRNH90', 'LSFFRNH90'] — PASS
- `FranceHelicopterTiger` in `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterTiger.ini` models=['LSFFRTiger', 'LSFFRTigerd', 'LSFFRTigerk'] — PASS
- `GermanyAircraftE3` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyAircraftE3.ini` models=['E3', 'E3', 'E3', 'E3'] — PASS
- `GermanyDroneHeronTP` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyDroneHeronTP.ini` models=['AVReaper', 'AVReaper_D', 'AVReaper_D'] — PASS
- `GermanyJetA400M` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetA400M.ini` models=['IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew', 'IUAC17HXNew'] — PASS
- `GermanyJetAlphaJet` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetAlphaJet.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `GermanyJetC130J` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130J.ini` models=['LSFUSAC130', 'LSFUSAC130', 'LSFUSAC130d', 'LSFUSAC130k'] — PASS
- `GermanyJetF35A` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF35A.ini` models=['LSFUSAF35A', 'LSFUSAF35Ad', 'LSFUSAF35Ad', 'LSFUSAF35Ad'] — PASS
- `GermanyJetF4F` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF4F.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `GermanyJetFCASNGF` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetFCASNGF.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `GermanyJetMako` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMako.ini` models=['LSFF16', 'LSFF16d', 'LSFF16d', 'LSFF16d'] — PASS
- `GermanyJetMiG29G` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMiG29G.ini` models=['LSFruMiG29', 'LSFruMiG29d', 'LSFruMiG29d', 'LSFruMiG29d'] — PASS
- `GermanyJetTornadoADV` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoADV.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `GermanyJetTornadoECR` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoECR.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `GermanyJetTornadoIDS` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoIDS.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `GermanyJetTyphoonECR` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonECR.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `GermanyJetTyphoonT1` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT1.ini` models=['EVTyphoon', 'EVTyphoon', 'EVTyphoon', 'EVTyphoon'] — PASS
- `GermanyJetTyphoonT4` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT4.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `GermanyUAVEuroMALE` in `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyUAVEuroMALE.ini` models=['Nat_Heron', 'Nat_HeronD', 'Nat_HeronD', 'Nat_HeronD'] — PASS
- `Germany_HelicopterBase` in `Data\INI\Object\Specter\German Armed Forces\Buildings\Germany_HelicopterBase.ini` models=['HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort'] — PASS
- `GermanyHelicopterCH53` in `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterCH53.ini` models=['LSFRUMi171', 'LSFRUMi171d', 'LSFRUMi171k'] — PASS
- `GermanyHelicopterH145M` in `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterH145M.ini` models=['LSFFenneck', 'LSFFenneckd', 'LSFFenneckk'] — PASS
- `GermanyHelicopterNH90` in `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterNH90.ini` models=['LSFGENH90', 'LSFGENH90', 'LSFGENH90'] — PASS
- `GermanyHelicopterTigerUHT` in `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterTigerUHT.ini` models=['LSFGETiger', 'LSFGETigerd', 'LSFGETigerk'] — PASS
- `IndiaJetAMCA` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetAMCA.ini` models=['LSFJ31', 'LSFJ31d', 'LSFJ31d', 'LSFJ31d'] — PASS
- `IndiaJetJaguarIS` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetJaguarIS.ini` models=['LSFFRF1', 'LSFFRF1d', 'LSFFRF1d', 'LSFFRF1d'] — PASS
- `IndiaJetMig21Bison` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig21Bison.ini` models=['LSFIDMig21', 'LSFIDMig21d', 'LSFIDMig21d', 'LSFIDMig21d'] — PASS
- `IndiaJetMig27` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig27.ini` models=['MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq'] — PASS
- `IndiaJetMig29K` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig29K.ini` models=['RUS_Mig35', 'RUS_Mig35', 'RUS_Mig35', 'RUS_Mig35'] — PASS
- `IndiaJetMirage2000H` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000H.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `IndiaJetMirage2000I` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000I.ini` models=['LSFMirage2KD', 'LSFMirage2KDd', 'LSFMirage2KDd', 'LSFMirage2KDd'] — PASS
- `IndiaJetRafaleDH` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleDH.ini` models=['LSFRafaleAS', 'LSFRafaleASd', 'LSFRafaleASd', 'LSFRafaleASd'] — PASS
- `IndiaJetRafaleEH` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleEH.ini` models=['LSFIDRafale', 'LSFIDRafaled', 'LSFIDRafaled', 'LSFIDRafaled'] — PASS
- `IndiaJetSu30MKI` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetSu30MKI.ini` models=['RUSU30', 'RUSU30d', 'RUSU30d', 'RUSU30d'] — PASS
- `IndiaJetTejas` in `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTejas.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `IranJetF14AM` in `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF14AM.ini` models=['LSFIRF14A', 'LSFIRF14Ad', 'LSFIRF14Ad', 'LSFIRF14Ad'] — PASS
- `IranJetF4E` in `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF4E.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `IranJetF7N` in `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF7N.ini` models=['LSFIRJ7', 'LSFIRJ7d', 'LSFIRJ7d', 'LSFIRJ7d'] — PASS
- `IranJetMig21Bis` in `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMig21Bis.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `IranJetSu35S` in `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetSu35S.ini` models=['SU-37', 'SU-37_D', 'SU-37_D', 'SU-37_D'] — PASS
- `IraqJetF16IQ` in `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetF16IQ.ini` models=['US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52'] — PASS
- `IraqJetL159` in `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetL159.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `IraqJetMig21` in `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetMig21.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `IraqJetSu25UB` in `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetSu25UB.ini` models=['RUSU-25', 'RUSU-25_D', 'RUSU-25_D', 'RUSU-25_D'] — PASS
- `IsraelJetF15CBaz` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF15CBaz.ini` models=['US_F15C', 'US_F15C', 'US_F15C', 'US_F15C'] — PASS
- `IsraelJetF15IRaamII` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF15IRaamII.ini` models=['LSFISF15E', 'LSFISF15Ed', 'LSFISF15Ed', 'LSFISF15Ed'] — PASS
- `IsraelJetF16CBarak` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF16CBarak.ini` models=['LSFISF16', 'LSFISF16d', 'LSFISF16d', 'LSFISF16d'] — PASS
- `IsraelJetF4E` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF4E.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `IsraelJetKfir` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetKfir.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `IsraelJetNesher` in `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetNesher.ini` models=['LSFMirage3', 'LSFMirage3d', 'LSFMirage3d', 'LSFMirage3d'] — PASS
- `ItalyAircraftG550CAEW` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyAircraftG550CAEW.ini` models=['KVE737', 'KVE737', 'KVE737', 'KVE737'] — PASS
- `ItalyDroneMQ9` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyDroneMQ9.ini` models=['AVReaper', 'AVReaper_D', 'AVReaper_D'] — PASS
- `ItalyJetAMX` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetAMX.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `ItalyJetC130J` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetC130J.ini` models=['LSFUSAC130', 'LSFUSAC130', 'LSFUSAC130d', 'LSFUSAC130k'] — PASS
- `ItalyJetC27J` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetC27J.ini` models=['LSFUSAC130', 'LSFUSAC130', 'LSFUSAC130d', 'LSFUSAC130k'] — PASS
- `ItalyJetF16` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF16.ini` models=['LSFF16', 'LSFF16d', 'LSFF16d', 'LSFF16d'] — PASS
- `ItalyJetF35A` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35A.ini` models=['AVF-35', 'AVF-35_D', 'AVF-35_D', 'AVF-35_D'] — PASS
- `ItalyJetF35B` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35B.ini` models=['ENF35A', 'ENF35A', 'ENF35A', 'ENF35A'] — PASS
- `ItalyJetGCAP` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetGCAP.ini` models=['PAK-FA', 'PAK-FA_D', 'PAK-FA_D', 'PAK-FA_D'] — PASS
- `ItalyJetHarrierII` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetHarrierII.ini` models=['LSFAV8B', 'LSFAV8Bd', 'LSFAV8Bd', 'LSFAV8Bd'] — PASS
- `ItalyJetM346FA` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetM346FA.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `ItalyJetMB339` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetMB339.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `ItalyJetTornadoECR` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoECR.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `ItalyJetTornadoIDS` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoIDS.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `ItalyJetTyphoon` in `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTyphoon.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `Italy_HelicopterBase` in `Data\INI\Object\Specter\Italian Armed Forces\Buildings\Italy_HelicopterBase.ini` models=['HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort', 'HXUSABigAirPort'] — PASS
- `ItalyHelicopterA129` in `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterA129.ini` models=['LSFGETiger', 'LSFGETigerd', 'LSFGETigerk'] — PASS
- `ItalyHelicopterAW101` in `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW101.ini` models=['LSFGENH90', 'LSFGENH90', 'LSFGENH90'] — PASS
- `ItalyHelicopterAW139` in `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW139.ini` models=['LSFRUMi171', 'LSFRUMi171d', 'LSFRUMi171k'] — PASS
- `ItalyHelicopterAW249` in `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW249.ini` models=['LSFAH64D', 'LSFAH64Dd', 'LSFAH64Dd'] — PASS
- `ItalyHelicopterNH90` in `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterNH90.ini` models=['LSFGENH90', 'LSFGENH90', 'LSFGENH90'] — PASS
- `JapanJetC130H` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetC130H.ini` models=['AVCargoPln', 'AVCargoPln', 'AVCargoPln_D', 'AVCargoPln_D'] — PASS
- `JapanJetF15DJ` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15DJ.ini` models=['US_F15EX', 'US_F15EX', 'US_F15EX', 'US_F15EX'] — PASS
- `JapanJetF15J` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini` models=['LSFUSAF15C', 'LSFUSAF15Cd', 'LSFUSAF15Cd', 'LSFUSAF15Cd'] — PASS
- `JapanJetF15JKai` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15JKai.ini` models=['LSFJPF15J', 'LSFJPF15Jd', 'LSFJPF15Jd', 'LSFJPF15Jd'] — PASS
- `JapanJetF2A` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2A.ini` models=['JPF2', 'JPF2D', 'JPF2D', 'JPF2D'] — PASS
- `JapanJetF2B` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2B.ini` models=['AGMZJPF2G', 'AGMZJPF2G', 'AGMZJPF2G', 'AGMZJPF2G'] — PASS
- `JapanJetF2Kai` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2Kai.ini` models=['LSF02TJ', 'LSF02TJd', 'LSF02TJd', 'LSF02TJd'] — PASS
- `JapanJetF3` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF3.ini` models=['PAK-FA', 'PAK-FA_D', 'PAK-FA_D', 'PAK-FA_D'] — PASS
- `JapanJetF35A` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35A.ini` models=['LSFUSAF35A', 'LSFUSAF35Ad', 'LSFUSAF35Ad', 'LSFUSAF35Ad'] — PASS
- `JapanJetF35B` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini` models=['ENF35A', 'ENF35A', 'ENF35A', 'ENF35A'] — PASS
- `JapanJetF4EJKai` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF4EJKai.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `JapanJetFX` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetFX.ini` models=['CHAJ31HXNew', 'CHAJ31HXNew', 'CHAJ31HXNew', 'CHAJ31HXNew'] — PASS
- `JapanJetX2Shinshin` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini` models=['LSFSX2', 'LSFSX2d', 'LSFSX2d', 'LSFSX2d'] — PASS
- `JapanUAVRQ4` in `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanUAVRQ4.ini` models=['US_RQ-4', 'US_MQ-4', 'US_MQ-4', 'US_MQ-4'] — PASS
- `LibyaJetJ7` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini` models=['LSFJ7', 'LSFJ7d', 'LSFJ7d', 'LSFJ7d'] — PASS
- `LibyaJetMig21` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `LibyaJetMig21MF` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21MF.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `LibyaJetMig23` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig23.ini` models=['MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq'] — PASS
- `LibyaJetMig25` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig25.ini` models=['Iraq_Mig-25bm', 'Iraq_Mig-25bm', 'Iraq_Mig-25bm', 'Iraq_Mig-25bm'] — PASS
- `LibyaJetMirageF1BD` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMirageF1BD.ini` models=['UVMirage', 'UVMirage_D', 'UVMirage_D', 'UVMirage_D'] — PASS
- `LibyaJetSu22` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22.ini` models=['Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3'] — PASS
- `LibyaJetSu22M4` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22M4.ini` models=['Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2'] — PASS
- `LibyaJetSu24` in `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu24.ini` models=['Irq_Su24Mk', 'Irq_Su24Mk', 'Irq_Su24Mk', 'Irq_Su24Mk'] — PASS
- `NatoJetF16C` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF16C.ini` models=['AVF16', 'AVF16_D', 'AVF16_D', 'AVF16_D'] — PASS
- `NatoJetF18A` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18A.ini` models=['AmF18A', 'AmF18A', 'AmF18A', 'AmF18A'] — PASS
- `NatoJetF18C` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18C.ini` models=['AVF-18', 'AVF-18_D', 'AVF-18_D', 'AVF-18_D'] — PASS
- `NatoJetF18E` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18E.ini` models=['F18SEA', 'F18SEA', 'F18SEA', 'F18SEA'] — PASS
- `NatoJetF18F` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18F.ini` models=['US_FA18F', 'US_FA18F', 'US_FA18F', 'US_FA18F'] — PASS
- `NatoJetF35B` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetF35B.ini` models=['ENF35A', 'ENF35A', 'ENF35A', 'ENF35A'] — PASS
- `NatoJetTornadoIDS` in `Data\INI\Object\Specter\NATO\Airforce\NatoJetTornadoIDS.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `NorthKoreaJetJ7` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7.ini` models=['LSFJ7', 'LSFJ7d', 'LSFJ7d', 'LSFJ7d'] — PASS
- `NorthKoreaJetJ7B` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7B.ini` models=['LSFJ7', 'LSFJ7d', 'LSFJ7d', 'LSFJ7d'] — PASS
- `NorthKoreaJetMig21` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig21.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `NorthKoreaJetMig21PF` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig21PF.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `NorthKoreaJetMig23` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig23.ini` models=['MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq'] — PASS
- `NorthKoreaJetMig23BN` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig23BN.ini` models=['MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq'] — PASS
- `NorthKoreaJetMig29UB` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig29UB.ini` models=['LSFruMiG29', 'LSFruMiG29d', 'LSFruMiG29d', 'LSFruMiG29d'] — PASS
- `NorthKoreaJetSu22` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu22.ini` models=['Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2'] — PASS
- `NorthKoreaJetSu22M4` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu22M4.ini` models=['Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3'] — PASS
- `NorthKoreaJetSu25UB` in `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu25UB.ini` models=['RUSU-25', 'RUSU-25_D', 'RUSU-25_D', 'RUSU-25_D'] — PASS
- `PakistanJetA5C` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetA5C.ini` models=['QIANG5', 'QIANG5d', 'QIANG5d', 'QIANG5d'] — PASS
- `PakistanJetF16AMLU` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16AMLU.ini` models=['LSFF16C', 'LSFF16Cd', 'LSFF16Cd', 'LSFF16Cd'] — PASS
- `PakistanJetF16B` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16B.ini` models=['LSFPKF16', 'LSFPKF16d', 'LSFPKF16d', 'LSFPKF16d'] — PASS
- `PakistanJetF7P` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7P.ini` models=['LSFJ7', 'LSFJ7d', 'LSFJ7d', 'LSFJ7d'] — PASS
- `PakistanJetF7PG` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7PG.ini` models=['LSFPKJ7', 'LSFPKJ7d', 'LSFPKJ7d', 'LSFPKJ7d'] — PASS
- `PakistanJetJ10CE` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJ10CE.ini` models=['NVJ-10', 'NVJ-10D', 'NVJ-10D', 'NVJ-10D'] — PASS
- `PakistanJetJF17` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17.ini` models=['LSFPKJF17', 'LSFPKJF17d', 'LSFPKJF17d', 'LSFPKJF17d'] — PASS
- `PakistanJetJF17Blk3` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17Blk3.ini` models=['LSFPKJF17', 'LSFPKJF17d', 'LSFPKJF17d', 'LSFPKJF17d'] — PASS
- `PakistanJetMirage3` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage3.ini` models=['LSFMirage3', 'LSFMirage3d', 'LSFMirage3d', 'LSFMirage3d'] — PASS
- `PakistanJetMirage5` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage5.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `PakistanJetMirageROSE` in `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirageROSE.ini` models=['UVMirage', 'UVMirage_D', 'UVMirage_D', 'UVMirage_D'] — PASS
- `ChinaJetJ20C` in `Data\INI\Object\Specter\PLA\Airforce\ChinaJetJ20C.ini` models=['NVJ-20', 'NVJ-20D', 'NVJ-20D', 'NVJ-20D'] — PASS
- `ChinaJetJ35A` in `Data\INI\Object\Specter\PLA\Airforce\ChinaJetJ35A.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `ChinaJetQ5` in `Data\INI\Object\Specter\PLA\Airforce\ChinaJetQ5.ini` models=['QIANG5', 'QIANG5d', 'QIANG5d', 'QIANG5d'] — PASS
- `SouthKoreaJetF15K` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15K.ini` models=['LSFF15K', 'LSFF15Kd', 'LSFF15Kd', 'LSFF15Kd'] — PASS
- `SouthKoreaJetF15KSlam` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15KSlam.ini` models=['US_F15E', 'US_F15E_D', 'US_F15E_D', 'US_F15E_D'] — PASS
- `SouthKoreaJetF16C` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16C.ini` models=['US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52'] — PASS
- `SouthKoreaJetF16D` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16D.ini` models=['US_F16D_B52', 'US_F16D_B52', 'US_F16D_B52', 'US_F16D_B52'] — PASS
- `SouthKoreaJetF35A` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35A.ini` models=['LSFUSAF35A', 'LSFUSAF35Ad', 'LSFUSAF35Ad', 'LSFUSAF35Ad'] — PASS
- `SouthKoreaJetF4E` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF4E.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `SouthKoreaJetF5E` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF5E.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SouthKoreaJetFA50` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetFA50.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SouthKoreaJetKF16` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF16.ini` models=['LSFKF16', 'LSFKF16d', 'LSFKF16d', 'LSFKF16d'] — PASS
- `SouthKoreaJetKF21` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21.ini` models=['LSFJ31', 'LSFJ31d', 'LSFJ31d', 'LSFJ31d'] — PASS
- `SouthKoreaJetKF21Blk2` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21Blk2.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `SouthKoreaJetT50` in `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetT50.ini` models=['AVHawk', 'AVHawk_P', 'AVHawk_P', 'AVHawk_P'] — PASS
- `SaudiJetF15C` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15C.ini` models=['LSFUSAF15C', 'LSFUSAF15Cd', 'LSFUSAF15Cd', 'LSFUSAF15Cd'] — PASS
- `SaudiJetF15EX` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15EX.ini` models=['US_F15EX', 'US_F15EX', 'US_F15EX', 'US_F15EX'] — PASS
- `SaudiJetF15S` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15S.ini` models=['LSFUSAF15E', 'LSFUSAF15Ed', 'LSFUSAF15Ed', 'LSFUSAF15Ed'] — PASS
- `SaudiJetF15SA` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15SA.ini` models=['Arb_F15SA', 'Arb_F15SA', 'Arb_F15SA', 'Arb_F15SA'] — PASS
- `SaudiJetF5E` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF5E.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SaudiJetHawk65` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetHawk65.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SaudiJetLightning` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetLightning.ini` models=['AVLightn', 'AVLightn_D', 'AVLightn_D', 'AVLightn_D'] — PASS
- `SaudiJetTornadoADV` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoADV.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `SaudiJetTornadoECR` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoECR.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `SaudiJetTornadoIDS` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoIDS.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `SaudiJetTyphoon` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoon.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `SaudiJetTyphoonT3` in `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoonT3.ini` models=['NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4'] — PASS
- `SouthAfricaJetBuccaneer` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetBuccaneer.ini` models=['LSFTornado', 'LSFTornadod', 'LSFTornadod', 'LSFTornadod'] — PASS
- `SouthAfricaJetCheetahC` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahC.ini` models=['LSFMirage3', 'LSFMirage3d', 'LSFMirage3d', 'LSFMirage3d'] — PASS
- `SouthAfricaJetCheetahD` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahD.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `SouthAfricaJetCheetahE` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahE.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `SouthAfricaJetGripenC` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenC.ini` models=['NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4'] — PASS
- `SouthAfricaJetGripenD` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenD.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `SouthAfricaJetGripenE` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenE.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `SouthAfricaJetHawk120` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk120.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SouthAfricaJetHawk127` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk127.ini` models=['AVHawk', 'AVHawk_P', 'AVHawk_P', 'AVHawk_P'] — PASS
- `SouthAfricaJetImpala` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetImpala.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SouthAfricaJetMirageIIICZ` in `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetMirageIIICZ.ini` models=['UVMirage', 'UVMirage_D', 'UVMirage_D', 'UVMirage_D'] — PASS
- `SwedenJetDrakenJ35` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetDrakenJ35.ini` models=['LSFMirage3', 'LSFMirage3d', 'LSFMirage3d', 'LSFMirage3d'] — PASS
- `SwedenJetGripenA` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenA.ini` models=['NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4', 'NAT_EF2000T4'] — PASS
- `SwedenJetGripenE` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenE.ini` models=['LSFEUEF2000', 'LSFEUEF2000d', 'LSFEUEF2000d', 'LSFEUEF2000d'] — PASS
- `SwedenJetLansenJ32` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetLansenJ32.ini` models=['LSFFRF1', 'LSFFRF1d', 'LSFFRF1d', 'LSFFRF1d'] — PASS
- `SwedenJetSK60` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SwedenJetSK60B` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60B.ini` models=['AVHawk', 'AVHawk_P', 'AVHawk_P', 'AVHawk_P'] — PASS
- `SwedenJetViggenAJS37` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenAJS37.ini` models=['LSFMirage2KD', 'LSFMirage2KDd', 'LSFMirage2KDd', 'LSFMirage2KDd'] — PASS
- `SwedenJetViggenJA37` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenJA37.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `SwedenJetViggenSH` in `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenSH.ini` models=['UVMirage', 'UVMirage_D', 'UVMirage_D', 'UVMirage_D'] — PASS
- `SyriaJetJ7` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini` models=['LSFJ7', 'LSFJ7d', 'LSFJ7d', 'LSFJ7d'] — PASS
- `SyriaJetL39` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetL39.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `SyriaJetMig21` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `SyriaJetMig21MF` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21MF.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `SyriaJetMig23` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig23.ini` models=['MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq', 'MiG-23bn_Irq'] — PASS
- `SyriaJetMig25` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig25.ini` models=['Iraq_Mig-25bm', 'Iraq_Mig-25bm', 'Iraq_Mig-25bm', 'Iraq_Mig-25bm'] — PASS
- `SyriaJetSu22` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22.ini` models=['Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3'] — PASS
- `SyriaJetSu22M4` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22M4.ini` models=['Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2'] — PASS
- `SyriaJetSu24` in `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu24.ini` models=['Irq_Su24Mk', 'Irq_Su24Mk', 'Irq_Su24Mk', 'Irq_Su24Mk'] — PASS
- `TurkeyJetF16Blk30` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16Blk30.ini` models=['LSFF16', 'LSFF16d', 'LSFF16d', 'LSFF16d'] — PASS
- `TurkeyJetF16C` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16C.ini` models=['AVF16', 'AVF16_D', 'AVF16_D', 'AVF16_D'] — PASS
- `TurkeyJetF16Ozgur` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16Ozgur.ini` models=['LSFKF16', 'LSFKF16d', 'LSFKF16d', 'LSFKF16d'] — PASS
- `TurkeyJetF35A` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF35A.ini` models=['LSFUSAF35A', 'LSFUSAF35Ad', 'LSFUSAF35Ad', 'LSFUSAF35Ad'] — PASS
- `TurkeyJetF4E` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF4E.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `TurkeyJetF4ETerm` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF4ETerm.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `TurkeyJetHurjet` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetHurjet.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `TurkeyJetKAAN` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetKAAN.ini` models=['LSFF22', 'LSFF22d', 'LSFF22d', 'LSFF22d'] — PASS
- `TurkeyJetKAANBlk2` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetKAANBlk2.ini` models=['NVJ31', 'NVJ31_D', 'NVJ31_D', 'NVJ31_D'] — PASS
- `TurkeyJetNF5` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetNF5.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `TurkeyJetRF4E` in `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetRF4E.ini` models=['JPF4', 'JPF4D', 'JPF4D', 'JPF4D'] — PASS
- `UkraineJetF16AM` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetF16AM.ini` models=['US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52', 'US_F16CJ_blk52'] — PASS
- `UkraineJetMig21` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig21.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `UkraineJetMig29` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29.ini` models=['LSFruMiG29', 'LSFruMiG29d', 'LSFruMiG29d', 'LSFruMiG29d'] — PASS
- `UkraineJetMig29MU1` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29MU1.ini` models=['RUS_Mig35', 'RUS_Mig35', 'RUS_Mig35', 'RUS_Mig35'] — PASS
- `UkraineJetMirage2000` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMirage2000.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `UkraineJetSu24M` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24M.ini` models=['RUS_SU24M2', 'RUS_SU24M2', 'RUS_SU24M2', 'RUS_SU24M2'] — PASS
- `UkraineJetSu24MR` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24MR.ini` models=['RUS_SU24MP', 'RUS_SU24MP', 'RUS_SU24MP', 'RUS_SU24MP'] — PASS
- `UkraineJetSu25` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25.ini` models=['RUS_SU25T', 'RUS_SU25T', 'RUS_SU25T', 'RUS_SU25T'] — PASS
- `UkraineJetSu25M1` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25M1.ini` models=['RUSU-25', 'RUSU-25_D', 'RUSU-25_D', 'RUSU-25_D'] — PASS
- `UkraineJetSu27` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27.ini` models=['LSFRUSU27SK', 'LSFRUSU27SKd', 'LSFRUSU27SKd', 'LSFRUSU27SKd'] — PASS
- `UkraineJetSu27UB` in `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27UB.ini` models=['RUS_SU30SM2', 'RUS_SU30SM2', 'RUS_SU30SM2', 'RUS_SU30SM2'] — PASS
- `UAEJetF15E` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini` models=['US_F15E', 'US_F15E_D', 'US_F15E_D', 'US_F15E_D'] — PASS
- `UAEJetF15EA` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15EA.ini` models=['US_F15EX', 'US_F15EX', 'US_F15EX', 'US_F15EX'] — PASS
- `UAEJetF15SA` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15SA.ini` models=['Arb_F15SA', 'Arb_F15SA', 'Arb_F15SA', 'Arb_F15SA'] — PASS
- `UAEJetF16E` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16E.ini` models=['Arb_F16C_B60', 'Arb_F16C_B60', 'Arb_F16C_B60', 'Arb_F16C_B60'] — PASS
- `UAEJetF16ECegy` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16ECegy.ini` models=['LSFF16CEgy', 'LSFF16CEgyd', 'LSFF16CEgyd', 'LSFF16CEgyd'] — PASS
- `UAEJetF16F` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16F.ini` models=['Egy_F16C', 'Egy_F16C_D', 'Egy_F16C_D', 'Egy_F16C_D'] — PASS
- `UAEJetHawk102` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetHawk102.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `UAEJetMirage20005` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20005.ini` models=['LSFMirage5', 'LSFMirage5d', 'LSFMirage5d', 'LSFMirage5d'] — PASS
- `UAEJetMirage20009` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009.ini` models=['LSFMirage2000', 'LSFMirage2000d', 'LSFMirage2000d', 'LSFMirage2000d'] — PASS
- `UAEJetMirage20009E` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009E.ini` models=['FraMirage2000', 'FraMirage2000', 'FraMirage2000', 'FraMirage2000'] — PASS
- `UAEJetMirage2000DAD` in `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage2000DAD.ini` models=['LSFMirage2KD', 'LSFMirage2KDd', 'LSFMirage2KDd', 'LSFMirage2KDd'] — PASS
- `AmericaDroneRQ180` in `Data\INI\Object\Specter\United States Of America\Airforce\AmericaDroneRQ180.ini` models=['AV_RQ180', 'AV_RQ180_D', 'AV_RQ180_D', 'AV_RQ180_D'] — PASS
- `VietnamJetF5E` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetF5E.ini` models=['AVHawk', 'AVHawk_P', 'AVHawk_P', 'AVHawk_P'] — PASS
- `VietnamJetL39` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetL39.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS
- `VietnamJetMig21` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21.ini` models=['LSFIDMig21', 'LSFIDMig21d', 'LSFIDMig21d', 'LSFIDMig21d'] — PASS
- `VietnamJetMig21bis` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21bis.ini` models=['UVMig-21', 'UVMig-21_D', 'UVMig-21_D', 'UVMig-21_D'] — PASS
- `VietnamJetSu22` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22.ini` models=['Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3', 'Irq_SU22M3'] — PASS
- `VietnamJetSu22M4` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22M4.ini` models=['Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2', 'Irn_SU22M2'] — PASS
- `VietnamJetSu27` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27.ini` models=['LSFRUSU27SK', 'LSFRUSU27SKd', 'LSFRUSU27SKd', 'LSFRUSU27SKd'] — PASS
- `VietnamJetSu27UB` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27UB.ini` models=['LSFSU35', 'LSFSU35d', 'LSFSU35d', 'LSFSU35d'] — PASS
- `VietnamJetSu30` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30.ini` models=['RUS_SU30SM2', 'RUS_SU30SM2', 'RUS_SU30SM2', 'RUS_SU30SM2'] — PASS
- `VietnamJetSu30MK2` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30MK2.ini` models=['RUSU30', 'RUSU30d', 'RUSU30d', 'RUSU30d'] — PASS
- `VietnamJetYak130` in `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini` models=['AVHawk', 'AVHawk_D', 'AVHawk_D', 'AVHawk_D'] — PASS

## HelicopterBase PRELOAD structures

France/Germany/Italy/Britain `_HelicopterBase` are PRELOAD STRUCTURE objects using `HXUSABigAirPort` (animation chunks present).
They are **not** on dozer CommandSets. They still parse at init. Syntax is End-balanced. Left in packed DATA.

## MappedImage / Science / CommandButton / Weapon / OCL reachability

Every post-414 European air CommandSet slot resolves to a declared CommandButton.
TornadoECR buttons exist once in CommandButton.ini.
`Japan_Weapon_AAM4B_F15J` exists once; ProjectileObject `MeteorMissile_Object` is the pre-existing projectile.
SPEC_China MappedImage duplicates are the #414 portrait overlay and are preserved.

**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**
