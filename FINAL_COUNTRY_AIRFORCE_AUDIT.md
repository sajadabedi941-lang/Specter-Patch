# FINAL COUNTRY AIRFORCE AUDIT

Playable countries discovered from PlayerTemplate.ini (excluding Civilian, Observer, BossGeneral).
LOCKED / NOT MODIFIED: USA (FactionAmerica), Russia (FactionRussia), China (FactionChina).
Egypt has airbase buildings but no PlayerTemplate — not playable, skipped.

DATA sha256 `9b57540f8672d0372dfcf03a8164548acad2d00404fe3a4eb9d0743b5d7c7716`
ART sha256 `2255a132b5e68bc69d941bc7d5fa1dcb617c323db47bd502bef89af96eb4289e`

Protected CommandSet hashes (unchanged):

- `AmericaAirfieldCommandSet` `0954ea634aaf8a5a895a2e6d5f45024ad7237479844cc3276c36653c0bd1afc3`
- `America_LargeAirBaseCommandSet` `9045e025345dfb25d57ec19ec69361f7782be017f28ac44be598cba5b6c9c3b1`
- `America_HeavyAirBaseCommandSet` `3fcb76336e9c336c5827abf621f25f1c81481989d99a9f24221ab87de418d1ed`
- `RussiaAirfieldCommandSet` `e615b640749e67b40a09824adee695bc964a1a201662ab3ae5b81344c072c202`
- `Russia_LargeAirBaseCommandSet` `20cf43d97715d4eb8a40a25617ea8562125b3f3b2b966a503d733a34bf0117ac`
- `Russia_HeavyAirBaseCommandSet` `4d98bbc64f76cf2beba2c7e8f9448b9f2e0f4cef382e6e77b75009fbfdf1ca2f`
- `PLAAirfieldCommandSet` `522862c4d7e9e5568ed44bd3377da95632e3afe8725d24694b4c5d2d90b9dadb`
- `China_LargeAirBaseCommandSet` `afdecf56f3b8e16fd59e79ef76bc99a439fae12d78ff3c68604dc7172261806e`
- `China_HeavyAirBaseCommandSet` `2fc489c13960283dac231a9aa611ac72c40443e6236686e03804cb3a07a61c90`

---

COUNTRY: France

FIGHTER AIRBASE — 12/12
01. FranceJetRafaleC (`FranceJetRafaleC`)
    Role: existing live unit
    Visual W3D: LSFRafale
    Visual source: already packed
    A2A: yes
    A2G: yes
02. FranceJetRafaleB (`FranceJetRafaleB`)
    Role: existing live unit
    Visual W3D: LSFRafale
    Visual source: already packed
    A2A: yes
    A2G: yes
03. FranceJetRafaleM (`FranceJetRafaleM`)
    Role: existing live unit
    Visual W3D: LSFRafaleAS
    Visual source: already packed
    A2A: yes
    A2G: yes
04. FranceJetRafaleF4 (`FranceJetRafaleF4`)
    Role: existing live unit
    Visual W3D: LSFIDRafale
    Visual source: already packed
    A2A: yes
    A2G: yes
05. FranceJetRafaleF3 (`FranceJetRafaleF3`)
    Role: existing live unit
    Visual W3D: Egy_RafaleM
    Visual source: already packed
    A2A: yes
    A2G: yes
06. FranceJetMirage20005F (`FranceJetMirage20005F`)
    Role: existing live unit
    Visual W3D: FraMirage2000
    Visual source: already packed
    A2A: yes
    A2G: yes
07. FranceJetMirage2000 (`FranceJetMirage2000`)
    Role: existing live unit
    Visual W3D: LSFMirage2000
    Visual source: already packed
    A2A: yes
    A2G: yes
08. FranceJetMirage2000D (`FranceJetMirage2000D`)
    Role: existing live unit
    Visual W3D: LSFMirage2KD
    Visual source: already packed
    A2A: yes
    A2G: yes
09. FranceJetMirageF1CT (`FranceJetMirageF1CT`)
    Role: existing live unit
    Visual W3D: LSFFRF1
    Visual source: already packed
    A2A: yes
    A2G: yes
10. FranceJetMirageIIIE (`FranceJetMirageIIIE`)
    Role: existing live unit
    Visual W3D: LSFMirage3
    Visual source: already packed
    A2A: yes
    A2G: yes
11. FranceJetMirage5 (`FranceJetMirage5`)
    Role: existing live unit
    Visual W3D: LSFMirage5
    Visual source: already packed
    A2A: yes
    A2G: yes
12. FranceJetFCASNGF (`FranceJetFCASNGF`)
    Role: existing live unit
    Visual W3D: LSFJ20
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- FranceJetC130  Type: transport  Visual: LSFUSAC130
- FranceAircraftE3  Type: awacs  Visual: E3
- FranceUCAVNeuron  Type: uav  Visual: CHI_GJ11L
- FranceHelicopterTiger  Type: helicopter  Visual: LSFFRTiger
- FranceHelicopterNH90  Type: helicopter  Visual: LSFFRNH90
- FranceHelicopterCaracal  Type: helicopter  Visual: LSFRUMi171
- FranceJetMirageF1CR  Type: fighter  Visual: UVMirage

HELICOPTERS
- FranceHelicopterTiger — helicopter — constructible on Heavy, W3D LSFFRTiger
- FranceHelicopterNH90 — helicopter — constructible on Heavy, W3D LSFFRNH90
- FranceHelicopterCaracal — helicopter — constructible on Heavy, W3D LSFRUMi171
UAVs
- FranceUCAVNeuron — UAV/UCAV — CHI_GJ11L
AWACS
- FranceAircraftE3 — existing Specter AWACS logic preserved — E3
TRANSPORTS
- FranceJetC130 — transport — LSFUSAC130
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Germany

FIGHTER AIRBASE — 12/12
01. GermanyJetTyphoonT4 (`GermanyJetTyphoonT4`)
    Role: existing live unit
    Visual W3D: LSFEUEF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
02. Typhoon T1 (`GermanyJetTyphoonT1`)
    Role: a2a
    Visual W3D: EVTyphoon
    Visual source: DONOR_ART EVTyphoon.W3D unused unique
    A2A: yes
    A2G: no / gun only
03. GermanyJetTyphoonECR (`GermanyJetTyphoonECR`)
    Role: existing live unit
    Visual W3D: LSFEUEF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
04. GermanyJetTornadoADV (`GermanyJetTornadoADV`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
05. GermanyJetF35A (`GermanyJetF35A`)
    Role: existing live unit
    Visual W3D: LSFUSAF35A
    Visual source: already packed
    A2A: yes
    A2G: yes
06. GermanyJetMiG29G (`GermanyJetMiG29G`)
    Role: existing live unit
    Visual W3D: LSFruMiG29
    Visual source: already packed
    A2A: yes
    A2G: yes
07. GermanyJetTornadoIDS (`GermanyJetTornadoIDS`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
08. GermanyJetTornadoECR (`GermanyJetTornadoECR`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
09. GermanyJetF4F (`GermanyJetF4F`)
    Role: existing live unit
    Visual W3D: JPF4
    Visual source: already packed
    A2A: yes
    A2G: yes
10. GermanyJetAlphaJet (`GermanyJetAlphaJet`)
    Role: existing live unit
    Visual W3D: AVHawk
    Visual source: already packed
    A2A: yes
    A2G: yes
11. GermanyJetMako (`GermanyJetMako`)
    Role: existing live unit
    Visual W3D: LSFF16
    Visual source: already packed
    A2A: yes
    A2G: yes
12. GermanyJetFCASNGF (`GermanyJetFCASNGF`)
    Role: existing live unit
    Visual W3D: NVJ31
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- GermanyJetA400M  Type: transport  Visual: IUAC17HXNew
- GermanyJetC130J  Type: transport  Visual: LSFUSAC130
- GermanyAircraftE3  Type: awacs  Visual: E3
- GermanyDroneHeronTP  Type: uav  Visual: AVReaper
- GermanyUAVEuroMALE  Type: uav  Visual: Nat_Heron
- GermanyHelicopterTigerUHT  Type: helicopter  Visual: LSFGETiger
- GermanyHelicopterNH90  Type: helicopter  Visual: LSFGENH90
- GermanyHelicopterCH53  Type: helicopter  Visual: LSFRUMi171
- GermanyHelicopterH145M  Type: helicopter  Visual: LSFFenneck

HELICOPTERS
- GermanyHelicopterTigerUHT — helicopter — constructible on Heavy, W3D LSFGETiger
- GermanyHelicopterNH90 — helicopter — constructible on Heavy, W3D LSFGENH90
- GermanyHelicopterCH53 — helicopter — constructible on Heavy, W3D LSFRUMi171
- GermanyHelicopterH145M — helicopter — constructible on Heavy, W3D LSFFenneck
UAVs
- GermanyDroneHeronTP — UAV/UCAV — AVReaper
- GermanyUAVEuroMALE — UAV/UCAV — Nat_Heron
AWACS
- GermanyAircraftE3 — existing Specter AWACS logic preserved — E3
TRANSPORTS
- GermanyJetA400M — transport — IUAC17HXNew
- GermanyJetC130J — transport — LSFUSAC130
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Italy

FIGHTER AIRBASE — 12/12
01. ItalyJetTyphoon (`ItalyJetTyphoon`)
    Role: existing live unit
    Visual W3D: LSFEUEF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
02. ItalyJetEF2000T4 (`ItalyJetEF2000T4`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
03. ItalyJetF35A (`ItalyJetF35A`)
    Role: existing live unit
    Visual W3D: AVF-35
    Visual source: already packed
    A2A: yes
    A2G: yes
04. ItalyJetF35B (`ItalyJetF35B`)
    Role: existing live unit
    Visual W3D: ENF35A
    Visual source: already packed
    A2A: yes
    A2G: yes
05. ItalyJetTornadoIDS (`ItalyJetTornadoIDS`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
06. ItalyJetTornadoECR (`ItalyJetTornadoECR`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
07. ItalyJetAMX (`ItalyJetAMX`)
    Role: existing live unit
    Visual W3D: LSFMirage5
    Visual source: already packed
    A2A: yes
    A2G: yes
08. ItalyJetHarrierII (`ItalyJetHarrierII`)
    Role: existing live unit
    Visual W3D: LSFAV8B
    Visual source: already packed
    A2A: yes
    A2G: yes
09. ItalyJetF16 (`ItalyJetF16`)
    Role: existing live unit
    Visual W3D: LSFF16
    Visual source: already packed
    A2A: yes
    A2G: yes
10. ItalyJetGCAP (`ItalyJetGCAP`)
    Role: existing live unit
    Visual W3D: PAK-FA
    Visual source: already packed
    A2A: yes
    A2G: yes
11. ItalyJetM346FA (`ItalyJetM346FA`)
    Role: existing live unit
    Visual W3D: AVHawk
    Visual source: already packed
    A2A: yes
    A2G: yes
12. ItalyJetMB339 (`ItalyJetMB339`)
    Role: existing live unit
    Visual W3D: AVHawk
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- ItalyJetC130J  Type: transport  Visual: LSFUSAC130
- ItalyJetC27J  Type: transport  Visual: LSFUSAC130
- ItalyAircraftG550CAEW  Type: awacs  Visual: KVE737
- ItalyDroneMQ9  Type: uav  Visual: AVReaper
- ItalyHelicopterAW249  Type: helicopter  Visual: LSFAH64D
- ItalyHelicopterA129  Type: helicopter  Visual: LSFGETiger
- ItalyHelicopterNH90  Type: helicopter  Visual: LSFGENH90
- ItalyHelicopterAW101  Type: helicopter  Visual: LSFGENH90
- ItalyHelicopterAW139  Type: helicopter  Visual: LSFRUMi171

HELICOPTERS
- ItalyHelicopterAW249 — helicopter — constructible on Heavy, W3D LSFAH64D
- ItalyHelicopterA129 — helicopter — constructible on Heavy, W3D LSFGETiger
- ItalyHelicopterNH90 — helicopter — constructible on Heavy, W3D LSFGENH90
- ItalyHelicopterAW101 — helicopter — constructible on Heavy, W3D LSFGENH90
- ItalyHelicopterAW139 — helicopter — constructible on Heavy, W3D LSFRUMi171
UAVs
- ItalyDroneMQ9 — UAV/UCAV — AVReaper
AWACS
- ItalyAircraftG550CAEW — existing Specter AWACS logic preserved — KVE737
TRANSPORTS
- ItalyJetC130J — transport — LSFUSAC130
- ItalyJetC27J — transport — LSFUSAC130
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: United Kingdom

FIGHTER AIRBASE — 12/12
01. BritainJetF35B (`BritainJetF35B`)
    Role: existing live unit
    Visual W3D: ENF35A
    Visual source: already packed
    A2A: yes
    A2G: yes
02. BritainJetTyphoonFGR4 (`BritainJetTyphoonFGR4`)
    Role: existing live unit
    Visual W3D: LSFEUEF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
03. BritainJetTyphoonT3 (`BritainJetTyphoonT3`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
04. BritainJetTempest (`BritainJetTempest`)
    Role: existing live unit
    Visual W3D: SPEC_OLD_F35
    Visual source: already packed
    A2A: yes
    A2G: yes
05. BritainJetTornadoF3 (`BritainJetTornadoF3`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
06. BritainJetTornadoGR4 (`BritainJetTornadoGR4`)
    Role: existing live unit
    Visual W3D: LSFTornado
    Visual source: already packed
    A2A: yes
    A2G: yes
07. BritainJetHarrierGR9 (`BritainJetHarrierGR9`)
    Role: existing live unit
    Visual W3D: LSFAV8B
    Visual source: already packed
    A2A: yes
    A2G: yes
08. BritainJetSeaHarrierFA2 (`BritainJetSeaHarrierFA2`)
    Role: existing live unit
    Visual W3D: US_FA18E
    Visual source: already packed
    A2A: yes
    A2G: yes
09. BritainJetPhantomFG1 (`BritainJetPhantomFG1`)
    Role: existing live unit
    Visual W3D: JPF4
    Visual source: already packed
    A2A: yes
    A2G: yes
10. BritainJetJaguarGR3 (`BritainJetJaguarGR3`)
    Role: existing live unit
    Visual W3D: LSFFRF1
    Visual source: already packed
    A2A: yes
    A2G: yes
11. BritainJetLightningF6 (`BritainJetLightningF6`)
    Role: existing live unit
    Visual W3D: AVLightn
    Visual source: already packed
    A2A: yes
    A2G: yes
12. BritainJetHawk200 (`BritainJetHawk200`)
    Role: existing live unit
    Visual W3D: LSFF16
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- BritainJetA400M  Type: transport  Visual: IUAC17HXNew
- BritainJetC17  Type: transport  Visual: IUAC17HXNew
- BritainAircraftE7  Type: awacs  Visual: KVE737
- BritainDroneMQ9  Type: uav  Visual: AVReaper
- BritainBomberVulcan  Type: bomber  Visual: LSFUSAB52
- BritainHelicopterApache  Type: helicopter  Visual: LSFAH64D
- BritainHelicopterChinook  Type: helicopter  Visual: US_CH47F
- BritainHelicopterMerlin  Type: helicopter  Visual: LSFGENH90
- BritainHelicopterWildcat  Type: helicopter  Visual: LSFLynxAHMK
- BritainHelicopterPuma  Type: helicopter  Visual: LSFRUMi171
- BritainJetPhantomFGR2  Type: fighter  Visual: JPF4
- BritainAircraftTornadoECR  Type: fighter  Visual: LSFTornado

HELICOPTERS
- BritainHelicopterApache — helicopter — constructible on Heavy, W3D LSFAH64D
- BritainHelicopterChinook — helicopter — constructible on Heavy, W3D US_CH47F
- BritainHelicopterMerlin — helicopter — constructible on Heavy, W3D LSFGENH90
- BritainHelicopterWildcat — helicopter — constructible on Heavy, W3D LSFLynxAHMK
- BritainHelicopterPuma — helicopter — constructible on Heavy, W3D LSFRUMi171
UAVs
- BritainDroneMQ9 — UAV/UCAV — AVReaper
AWACS
- BritainAircraftE7 — existing Specter AWACS logic preserved — KVE737
TRANSPORTS
- BritainJetA400M — transport — IUAC17HXNew
- BritainJetC17 — transport — IUAC17HXNew
BOMBERS
- BritainBomberVulcan — bomber — LSFUSAB52

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Japan

FIGHTER AIRBASE — 12/12
01. JapanJetF15JKai (`JapanJetF15JKai`)
    Role: existing live unit
    Visual W3D: LSFJPF15J
    Visual source: already packed
    A2A: yes
    A2G: yes
02. JapanJetF15J (`JapanJetF15J`)
    Role: existing live unit
    Visual W3D: LSFUSAF15C
    Visual source: already packed
    A2A: yes
    A2G: yes
03. F-15DJ (`JapanJetF15DJ`)
    Role: multirole
    Visual W3D: US_F15EX
    Visual source: packed US_F15EX
    A2A: yes
    A2G: yes
04. JapanJetF2A (`JapanJetF2A`)
    Role: existing live unit
    Visual W3D: JPF2
    Visual source: already packed
    A2A: yes
    A2G: yes
05. JapanJetF2B (`JapanJetF2B`)
    Role: existing live unit
    Visual W3D: AGMZJPF2G
    Visual source: already packed
    A2A: yes
    A2G: yes
06. JapanJetF2Kai (`JapanJetF2Kai`)
    Role: existing live unit
    Visual W3D: LSF02TJ
    Visual source: already packed
    A2A: yes
    A2G: yes
07. JapanJetF4EJKai (`JapanJetF4EJKai`)
    Role: existing live unit
    Visual W3D: JPF4
    Visual source: already packed
    A2A: yes
    A2G: yes
08. JapanJetX2Shinshin (`JapanJetX2Shinshin`)
    Role: existing live unit
    Visual W3D: LSFSX2
    Visual source: already packed
    A2A: yes
    A2G: yes
09. F-35A (`JapanJetF35A`)
    Role: stealth / air superiority
    Visual W3D: LSFUSAF35A
    Visual source: packed LSFUSAF35A
    A2A: yes
    A2G: no / gun only
10. F-35B (`JapanJetF35B`)
    Role: stealth / air superiority
    Visual W3D: ENF35A
    Visual source: packed ENF35A
    A2A: yes
    A2G: no / gun only
11. F-X (`JapanJetFX`)
    Role: stealth / air superiority
    Visual W3D: CHAJ31HXNew
    Visual source: packed unused CHAJ31HXNew
    A2A: yes
    A2G: no / gun only
12. F-3 GCAP (`JapanJetF3`)
    Role: stealth / air superiority
    Visual W3D: PAK-FA
    Visual source: packed PAK-FA
    A2A: yes
    A2G: no / gun only

HEAVY / LARGE AIRBASE
- JapanJetC130H  Type: transport  Visual: AVCargoPln
- JapanUAVRQ4  Type: uav  Visual: US_RQ-4

HELICOPTERS
- none on Heavy (GLA has no Heavy Airbase)
UAVs
- JapanUAVRQ4 — UAV/UCAV — US_RQ-4
AWACS
- none on this Heavy menu
TRANSPORTS
- JapanJetC130H — transport — AVCargoPln
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Turkey

FIGHTER AIRBASE — 12/12
01. TurkeyJetKAAN (`TurkeyJetKAAN`)
    Role: existing live unit
    Visual W3D: LSFF22
    Visual source: already packed
    A2A: yes
    A2G: yes
02. KAAN Block 2 (`TurkeyJetKAANBlk2`)
    Role: a2a
    Visual W3D: NVJ31
    Visual source: packed NVJ31
    A2A: yes
    A2G: no / gun only
03. TurkeyJetF16C (`TurkeyJetF16C`)
    Role: existing live unit
    Visual W3D: AVF16
    Visual source: already packed
    A2A: yes
    A2G: yes
04. TurkeyJetF16Ozgur (`TurkeyJetF16Ozgur`)
    Role: existing live unit
    Visual W3D: LSFKF16
    Visual source: already packed
    A2A: yes
    A2G: yes
05. TurkeyJetF16DBlk52 (`TurkeyJetF16DBlk52`)
    Role: existing live unit
    Visual W3D: US_F16D_B52
    Visual source: already packed
    A2A: yes
    A2G: yes
06. F-16C Block 30 (`TurkeyJetF16Blk30`)
    Role: multirole
    Visual W3D: LSFF16
    Visual source: packed LSFF16
    A2A: yes
    A2G: yes
07. TurkeyJetF4ETerm (`TurkeyJetF4ETerm`)
    Role: existing live unit
    Visual W3D: JPF4
    Visual source: already packed
    A2A: yes
    A2G: yes
08. F-4E Phantom (`TurkeyJetF4E`)
    Role: legacy
    Visual W3D: JPF4
    Visual source: packed JPF4
    A2A: yes
    A2G: yes
09. RF-4E Phantom (`TurkeyJetRF4E`)
    Role: strike
    Visual W3D: JPF4
    Visual source: packed JPF4
    A2A: limited
    A2G: yes
10. F-35A (`TurkeyJetF35A`)
    Role: stealth / air superiority
    Visual W3D: LSFUSAF35A
    Visual source: packed LSFUSAF35A
    A2A: yes
    A2G: no / gun only
11. Hurjet (`TurkeyJetHurjet`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk light-attack stand-in
    A2A: limited
    A2G: yes
12. NF-5A (`TurkeyJetNF5`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_D
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- TurkeyJetE3AAWACS  Type: awacs  Visual: US_E3G
- TurkeyHelicopterAH64E  Type: helicopter  Visual: US_AH64E
- TurkeyHelicopterUH60  Type: helicopter  Visual: US_UH60
- TurkeyHelicopterCH47F  Type: helicopter  Visual: US_CH47F

HELICOPTERS
- TurkeyHelicopterAH64E — helicopter — constructible on Heavy, W3D US_AH64E
- TurkeyHelicopterUH60 — helicopter — constructible on Heavy, W3D US_UH60
- TurkeyHelicopterCH47F — helicopter — constructible on Heavy, W3D US_CH47F
UAVs
- none on this Heavy menu
AWACS
- TurkeyJetE3AAWACS — existing Specter AWACS logic preserved — US_E3G
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Iran

FIGHTER AIRBASE — 12/12
01. IranJetF14A (`IranJetF14A`)
    Role: existing live unit
    Visual W3D: Iran_F14A
    Visual source: already packed
    A2A: yes
    A2G: yes
02. F-14AM (`IranJetF14AM`)
    Role: interceptor
    Visual W3D: LSFIRF14A
    Visual source: DONOR_ART LSFIRF14A unused unique Tomcat
    A2A: yes
    A2G: no / gun only
03. IranJetF4E (`IranJetF4E`)
    Role: existing live unit
    Visual W3D: JPF4
    Visual source: already packed
    A2A: yes
    A2G: yes
04. IranJetMig29A (`IranJetMig29A`)
    Role: existing live unit
    Visual W3D: Irn_Mig29A
    Visual source: already packed
    A2A: yes
    A2G: yes
05. IranJetMig21Bis (`IranJetMig21Bis`)
    Role: existing live unit
    Visual W3D: UVMig-21
    Visual source: already packed
    A2A: yes
    A2G: yes
06. IranJetF7N (`IranJetF7N`)
    Role: existing live unit
    Visual W3D: LSFIRJ7
    Visual source: already packed
    A2A: yes
    A2G: yes
07. IranJetSU22 (`IranJetSU22`)
    Role: existing live unit
    Visual W3D: Irn_SU22M2
    Visual source: already packed
    A2A: yes
    A2G: yes
08. IranJetSU24M (`IranJetSU24M`)
    Role: existing live unit
    Visual W3D: Irq_Su24Mk
    Visual source: already packed
    A2A: yes
    A2G: yes
09. IranJetSU25K (`IranJetSU25K`)
    Role: existing live unit
    Visual W3D: Irq_Su25k
    Visual source: already packed
    A2A: yes
    A2G: yes
10. IranJetSu35S (`IranJetSu35S`)
    Role: existing live unit
    Visual W3D: SU-37
    Visual source: already packed
    A2A: yes
    A2G: yes
11. IranJetJ10CE (`IranJetJ10CE`)
    Role: existing live unit
    Visual W3D: CHI_J10C
    Visual source: already packed
    A2A: yes
    A2G: yes
12. IranJetSu57E (`IranJetSu57E`)
    Role: existing live unit
    Visual W3D: RUS_SU57
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- IranHelicopterPanha2091  Type: helicopter  Visual: iran_panha2091
- IranHelicopterMi8  Type: helicopter  Visual: Irn_MI8A
- IranJetSu47Berkut  Type: fighter  Visual: RUS_SU35S

HELICOPTERS
- IranHelicopterPanha2091 — helicopter — constructible on Heavy, W3D iran_panha2091
- IranHelicopterMi8 — helicopter — constructible on Heavy, W3D Irn_MI8A
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Pakistan

FIGHTER AIRBASE — 12/12
01. PakistanJetF16AMLU (`PakistanJetF16AMLU`)
    Role: existing live unit
    Visual W3D: LSFF16C
    Visual source: already packed
    A2A: yes
    A2G: yes
02. Pakistan_F16Blk52 (`Pakistan_F16Blk52`)
    Role: existing live unit
    Visual W3D: US_F16CJ_blk52
    Visual source: already packed
    A2A: yes
    A2G: yes
03. F-16B (`PakistanJetF16B`)
    Role: multirole
    Visual W3D: LSFPKF16
    Visual source: DONOR_ART LSFPKF16 unused unique
    A2A: yes
    A2G: yes
04. PakistanJetJ10CE (`PakistanJetJ10CE`)
    Role: existing live unit
    Visual W3D: NVJ-10
    Visual source: already packed
    A2A: yes
    A2G: yes
05. JF-17 Thunder (`PakistanJetJF17`)
    Role: multirole
    Visual W3D: LSFPKJF17
    Visual source: packed LSFPKJF17 unused by Pakistan
    A2A: yes
    A2G: yes
06. JF-17 Block III (`PakistanJetJF17Blk3`)
    Role: strike
    Visual W3D: LSFPKJF17
    Visual source: packed LSFPKJF17k
    A2A: limited
    A2G: yes
07. PakistanJetF7PG (`PakistanJetF7PG`)
    Role: existing live unit
    Visual W3D: LSFPKJ7
    Visual source: already packed
    A2A: yes
    A2G: yes
08. F-7P (`PakistanJetF7P`)
    Role: legacy
    Visual W3D: LSFJ7
    Visual source: packed LSFJ7
    A2A: yes
    A2G: yes
09. Mirage IIIEP (`PakistanJetMirage3`)
    Role: interceptor
    Visual W3D: LSFMirage3
    Visual source: packed LSFMirage3
    A2A: yes
    A2G: no / gun only
10. Mirage 5 PA (`PakistanJetMirage5`)
    Role: strike
    Visual W3D: LSFMirage5
    Visual source: packed LSFMirage5
    A2A: limited
    A2G: yes
11. Mirage ROSE III (`PakistanJetMirageROSE`)
    Role: strike
    Visual W3D: UVMirage
    Visual source: packed UVMirage
    A2A: limited
    A2G: yes
12. A-5C Fantan (`PakistanJetA5C`)
    Role: cas
    Visual W3D: QIANG5
    Visual source: packed QIANG5
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- Pakistan_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- Pakistan_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- Pakistan_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- Pakistan_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: India

FIGHTER AIRBASE — 12/12
01. IndiaJetSu30MKI (`IndiaJetSu30MKI`)
    Role: existing live unit
    Visual W3D: RUSU30
    Visual source: already packed
    A2A: yes
    A2G: yes
02. India_Mig-29A (`India_Mig-29A`)
    Role: existing live unit
    Visual W3D: Irq_Mig29A
    Visual source: already packed
    A2A: yes
    A2G: yes
03. MiG-29K (`IndiaJetMig29K`)
    Role: multirole
    Visual W3D: RUS_Mig35
    Visual source: packed RUS_Mig35
    A2A: yes
    A2G: yes
04. Rafale EH (`IndiaJetRafaleEH`)
    Role: multirole
    Visual W3D: LSFIDRafale
    Visual source: packed LSFIDRafale India mesh
    A2A: yes
    A2G: yes
05. Rafale DH (`IndiaJetRafaleDH`)
    Role: strike
    Visual W3D: LSFRafaleAS
    Visual source: packed LSFRafaleAS
    A2A: limited
    A2G: yes
06. Mirage 2000H (`IndiaJetMirage2000H`)
    Role: a2a
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000
    A2A: yes
    A2G: no / gun only
07. Mirage 2000I (`IndiaJetMirage2000I`)
    Role: strike
    Visual W3D: LSFMirage2KD
    Visual source: packed LSFMirage2KD
    A2A: limited
    A2G: yes
08. MiG-21 Bison (`IndiaJetMig21Bison`)
    Role: legacy
    Visual W3D: LSFIDMig21
    Visual source: packed unused LSFIDMig21
    A2A: yes
    A2G: yes
09. Jaguar IS (`IndiaJetJaguarIS`)
    Role: strike
    Visual W3D: LSFFRF1
    Visual source: packed LSFFRF1 Jaguar-class donor
    A2A: limited
    A2G: yes
10. MiG-27 Bahadur (`IndiaJetMig27`)
    Role: cas
    Visual W3D: MiG-23bn_Irq
    Visual source: packed MiG-23bn_Irq
    A2A: limited
    A2G: yes
11. Tejas Mk1A (`IndiaJetTejas`)
    Role: multirole
    Visual W3D: NVJ31
    Visual source: packed NVJ31 Tejas/AMCA-class stand-in
    A2A: yes
    A2G: yes
12. AMCA (`IndiaJetAMCA`)
    Role: stealth / air superiority
    Visual W3D: LSFJ31
    Visual source: packed LSFJ31 AMCA stand-in
    A2A: yes
    A2G: no / gun only

HEAVY / LARGE AIRBASE
- India_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- India_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- India_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- India_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Israel

FIGHTER AIRBASE — 12/12
01. IsraelJetF35I_AA (`IsraelJetF35I_AA`)
    Role: existing live unit
    Visual W3D: US_F35A
    Visual source: already packed
    A2A: yes
    A2G: yes
02. IsraelJetF35IAdirPenetrator (`IsraelJetF35IAdirPenetrator`)
    Role: existing live unit
    Visual W3D: US_F35A
    Visual source: already packed
    A2A: yes
    A2G: yes
03. IsraelJetF16ISufaPrecision (`IsraelJetF16ISufaPrecision`)
    Role: existing live unit
    Visual W3D: Isr_F16I
    Visual source: already packed
    A2A: yes
    A2G: yes
04. Israel_F16I_AG (`Israel_F16I_AG`)
    Role: existing live unit
    Visual W3D: Isr_F16I
    Visual source: already packed
    A2A: yes
    A2G: yes
05. F-16C Barak (`IsraelJetF16CBarak`)
    Role: multirole
    Visual W3D: LSFISF16
    Visual source: DONOR_ART LSFISF16 unused unique
    A2A: yes
    A2G: yes
06. IsraelJetF15CBaz (`IsraelJetF15CBaz`)
    Role: existing live unit
    Visual W3D: US_F15C
    Visual source: already packed
    A2A: yes
    A2G: yes
07. Israel_F15I_AA (`Israel_F15I_AA`)
    Role: existing live unit
    Visual W3D: Isr_F15I
    Visual source: already packed
    A2A: yes
    A2G: yes
08. F-15I Ra'am (`IsraelJetF15IRaamII`)
    Role: strike
    Visual W3D: LSFISF15E
    Visual source: DONOR_ART LSFISF15E unused unique
    A2A: limited
    A2G: yes
09. Kfir C.10 (`IsraelJetKfir`)
    Role: multirole
    Visual W3D: LSFMirage5
    Visual source: packed LSFMirage5 Kfir stand-in
    A2A: yes
    A2G: yes
10. Nesher (`IsraelJetNesher`)
    Role: legacy
    Visual W3D: LSFMirage3
    Visual source: packed LSFMirage3
    A2A: yes
    A2G: yes
11. F-4E Kurnass (`IsraelJetF4E`)
    Role: legacy
    Visual W3D: JPF4
    Visual source: packed JPF4
    A2A: yes
    A2G: yes
12. IsraelJetF15IRaamDeepStrike (`IsraelJetF15IRaamDeepStrike`)
    Role: existing live unit
    Visual W3D: Isr_F15I
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- IsraelJetF15BazHeavyBomber  Type: bomber  Visual: Isr_F15I
- IsraelJetG550Eitam  Type: awacs  Visual: US_E3G

HELICOPTERS
- none on Heavy (GLA has no Heavy Airbase)
UAVs
- none on this Heavy menu
AWACS
- IsraelJetG550Eitam — existing Specter AWACS logic preserved — US_E3G
TRANSPORTS
- none on this Heavy menu
BOMBERS
- IsraelJetF15BazHeavyBomber — bomber — Isr_F15I

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Saudi Arabia

FIGHTER AIRBASE — 12/12
01. SaudiJetF15S (`SaudiJetF15S`)
    Role: existing live unit
    Visual W3D: LSFUSAF15E
    Visual source: already packed
    A2A: yes
    A2G: yes
02. F-15SA (`SaudiJetF15SA`)
    Role: strike
    Visual W3D: Arb_F15SA
    Visual source: packed Arb_F15SA
    A2A: limited
    A2G: yes
03. F-15C (`SaudiJetF15C`)
    Role: a2a
    Visual W3D: LSFUSAF15C
    Visual source: packed LSFUSAF15C
    A2A: yes
    A2G: no / gun only
04. F-15EX (`SaudiJetF15EX`)
    Role: multirole
    Visual W3D: US_F15EX
    Visual source: packed US_F15EX
    A2A: yes
    A2G: yes
05. Typhoon F.2 (`SaudiJetTyphoon`)
    Role: a2a
    Visual W3D: LSFEUEF2000
    Visual source: packed LSFEUEF2000
    A2A: yes
    A2G: no / gun only
06. Typhoon T3 (`SaudiJetTyphoonT3`)
    Role: multirole
    Visual W3D: NAT_EF2000T4
    Visual source: packed NAT_EF2000T4
    A2A: yes
    A2G: yes
07. Tornado IDS (`SaudiJetTornadoIDS`)
    Role: strike
    Visual W3D: LSFTornado
    Visual source: packed LSFTornado
    A2A: limited
    A2G: yes
08. Tornado ADV (`SaudiJetTornadoADV`)
    Role: interceptor
    Visual W3D: LSFTornado
    Visual source: packed LSFTornado
    A2A: yes
    A2G: no / gun only
09. Tornado ECR (`SaudiJetTornadoECR`)
    Role: strike
    Visual W3D: LSFTornado
    Visual source: packed LSFTornado
    A2A: limited
    A2G: yes
10. Hawk 65 (`SaudiJetHawk65`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes
11. Lightning F.53 (`SaudiJetLightning`)
    Role: interceptor
    Visual W3D: AVLightn
    Visual source: packed AVLightn
    A2A: yes
    A2G: no / gun only
12. F-5E Tiger II (`SaudiJetF5E`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_D
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- SaudiArabia_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- SaudiArabia_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- SaudiArabia_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- SaudiArabia_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: NATO

FIGHTER AIRBASE — 12/12
01. F/A-18A Hornet (`NatoJetF18A`)
    Role: multirole
    Visual W3D: AmF18A
    Visual source: DONOR_ART AmF18A unused unique
    A2A: yes
    A2G: yes
02. F/A-18C Hornet (`NatoJetF18C`)
    Role: multirole
    Visual W3D: AVF-18
    Visual source: packed unused AVF-18
    A2A: yes
    A2G: yes
03. F/A-18E Super Hornet (`NatoJetF18E`)
    Role: strike
    Visual W3D: F18SEA
    Visual source: DONOR_ART F18SEA unused unique
    A2A: limited
    A2G: yes
04. F/A-18F Super Hornet (`NatoJetF18F`)
    Role: multirole
    Visual W3D: US_FA18F
    Visual source: packed US_FA18F
    A2A: yes
    A2G: yes
05. NatoJetEA18G (`NatoJetEA18G`)
    Role: existing live unit
    Visual W3D: US_EA18G
    Visual source: already packed
    A2A: yes
    A2G: yes
06. NatoJetF35C (`NatoJetF35C`)
    Role: existing live unit
    Visual W3D: US_F35A
    Visual source: already packed
    A2A: yes
    A2G: yes
07. F-35B (`NatoJetF35B`)
    Role: stealth / air superiority
    Visual W3D: ENF35A
    Visual source: packed ENF35A
    A2A: yes
    A2G: no / gun only
08. NatoJetEF2000T4 (`NatoJetEF2000T4`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
09. F-16C (`NatoJetF16C`)
    Role: multirole
    Visual W3D: AVF16
    Visual source: packed AVF16
    A2A: yes
    A2G: yes
10. NatoJetF16DBlk52 (`NatoJetF16DBlk52`)
    Role: existing live unit
    Visual W3D: US_F16D_B52
    Visual source: already packed
    A2A: yes
    A2G: yes
11. NatoJetRafaleF3 (`NatoJetRafaleF3`)
    Role: existing live unit
    Visual W3D: Egy_RafaleM
    Visual source: already packed
    A2A: yes
    A2G: yes
12. Tornado IDS (`NatoJetTornadoIDS`)
    Role: strike
    Visual W3D: LSFTornado
    Visual source: packed LSFTornado
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- NatoJetE3AAWACS  Type: awacs  Visual: US_E3G
- NatoHelicopterAH64E  Type: helicopter  Visual: US_AH64E
- NatoHelicopterUH60  Type: helicopter  Visual: US_UH60
- NatoHelicopterCH47F  Type: helicopter  Visual: US_CH47F

HELICOPTERS
- NatoHelicopterAH64E — helicopter — constructible on Heavy, W3D US_AH64E
- NatoHelicopterUH60 — helicopter — constructible on Heavy, W3D US_UH60
- NatoHelicopterCH47F — helicopter — constructible on Heavy, W3D US_CH47F
UAVs
- none on this Heavy menu
AWACS
- NatoJetE3AAWACS — existing Specter AWACS logic preserved — US_E3G
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Sweden

FIGHTER AIRBASE — 12/12
01. JAS 39A Gripen (`SwedenJetGripenA`)
    Role: a2a
    Visual W3D: NAT_EF2000T4
    Visual source: packed NAT_EF2000T4 early Gripen family
    A2A: yes
    A2G: no / gun only
02. SwedenJetEF2000T4 (`SwedenJetEF2000T4`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
03. SwedenJetEF2000T4_AA (`SwedenJetEF2000T4_AA`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
04. JAS 39E Gripen (`SwedenJetGripenE`)
    Role: a2a
    Visual W3D: LSFEUEF2000
    Visual source: packed LSFEUEF2000 Gripen-E canard stand-in
    A2A: yes
    A2G: no / gun only
05. SwedenJetEF2000T4_CAS (`SwedenJetEF2000T4_CAS`)
    Role: existing live unit
    Visual W3D: NAT_EF2000T4
    Visual source: already packed
    A2A: yes
    A2G: yes
06. JA 37 Viggen (`SwedenJetViggenJA37`)
    Role: interceptor
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000 delta stand-in
    A2A: yes
    A2G: no / gun only
07. AJS 37 Viggen (`SwedenJetViggenAJS37`)
    Role: strike
    Visual W3D: LSFMirage2KD
    Visual source: packed LSFMirage2KD
    A2A: limited
    A2G: yes
08. SH 37 Viggen (`SwedenJetViggenSH`)
    Role: strike
    Visual W3D: UVMirage
    Visual source: packed UVMirage
    A2A: limited
    A2G: yes
09. J 35 Draken (`SwedenJetDrakenJ35`)
    Role: interceptor
    Visual W3D: LSFMirage3
    Visual source: packed LSFMirage3 double-delta stand-in
    A2A: yes
    A2G: no / gun only
10. J 32 Lansen (`SwedenJetLansenJ32`)
    Role: strike
    Visual W3D: LSFFRF1
    Visual source: packed LSFFRF1
    A2A: limited
    A2G: yes
11. SK 60 (`SwedenJetSK60`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes
12. SK 60B (`SwedenJetSK60B`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_P
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- SwedenJetE3AAWACS  Type: awacs  Visual: US_E3G
- SwedenHelicopterCH47F  Type: helicopter  Visual: US_CH47F
- SwedenHelicopterUH60  Type: helicopter  Visual: US_UH60
- SwedenHelicopterAH64E  Type: helicopter  Visual: US_AH64E

HELICOPTERS
- SwedenHelicopterCH47F — helicopter — constructible on Heavy, W3D US_CH47F
- SwedenHelicopterUH60 — helicopter — constructible on Heavy, W3D US_UH60
- SwedenHelicopterAH64E — helicopter — constructible on Heavy, W3D US_AH64E
UAVs
- none on this Heavy menu
AWACS
- SwedenJetE3AAWACS — existing Specter AWACS logic preserved — US_E3G
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Ukraine

FIGHTER AIRBASE — 12/12
01. MiG-29 (`UkraineJetMig29`)
    Role: a2a
    Visual W3D: LSFruMiG29
    Visual source: packed LSFruMiG29
    A2A: yes
    A2G: no / gun only
02. MiG-29MU1 (`UkraineJetMig29MU1`)
    Role: multirole
    Visual W3D: RUS_Mig35
    Visual source: packed RUS_Mig35
    A2A: yes
    A2G: yes
03. Su-27 (`UkraineJetSu27`)
    Role: a2a
    Visual W3D: LSFRUSU27SK
    Visual source: packed LSFRUSU27SK
    A2A: yes
    A2G: no / gun only
04. Su-27UB (`UkraineJetSu27UB`)
    Role: multirole
    Visual W3D: RUS_SU30SM2
    Visual source: packed RUS_SU30SM2
    A2A: yes
    A2G: yes
05. F-16AM (`UkraineJetF16AM`)
    Role: multirole
    Visual W3D: US_F16CJ_blk52
    Visual source: packed US_F16CJ_blk52
    A2A: yes
    A2G: yes
06. UkraineJetF16DBlk52 (`UkraineJetF16DBlk52`)
    Role: existing live unit
    Visual W3D: US_F16D_B52
    Visual source: already packed
    A2A: yes
    A2G: yes
07. Mirage 2000 (`UkraineJetMirage2000`)
    Role: multirole
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000
    A2A: yes
    A2G: yes
08. Su-24M (`UkraineJetSu24M`)
    Role: strike
    Visual W3D: RUS_SU24M2
    Visual source: packed RUS_SU24M2
    A2A: limited
    A2G: yes
09. Su-24MR (`UkraineJetSu24MR`)
    Role: strike
    Visual W3D: RUS_SU24MP
    Visual source: packed RUS_SU24MP
    A2A: limited
    A2G: yes
10. Su-25 (`UkraineJetSu25`)
    Role: cas
    Visual W3D: RUS_SU25T
    Visual source: packed RUS_SU25T
    A2A: limited
    A2G: yes
11. Su-25M1 (`UkraineJetSu25M1`)
    Role: cas
    Visual W3D: RUSU-25
    Visual source: packed RUSU-25
    A2A: limited
    A2G: yes
12. MiG-21bis (`UkraineJetMig21`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- UkraineJetE3AAWACS  Type: awacs  Visual: US_E3G
- UkraineHelicopterCH47F  Type: helicopter  Visual: US_CH47F
- UkraineHelicopterUH60  Type: helicopter  Visual: US_UH60
- UkraineHelicopterAH64E  Type: helicopter  Visual: US_AH64E

HELICOPTERS
- UkraineHelicopterCH47F — helicopter — constructible on Heavy, W3D US_CH47F
- UkraineHelicopterUH60 — helicopter — constructible on Heavy, W3D US_UH60
- UkraineHelicopterAH64E — helicopter — constructible on Heavy, W3D US_AH64E
UAVs
- none on this Heavy menu
AWACS
- UkraineJetE3AAWACS — existing Specter AWACS logic preserved — US_E3G
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: UAE

FIGHTER AIRBASE — 12/12
01. F-16E Block 60 (`UAEJetF16E`)
    Role: multirole
    Visual W3D: Arb_F16C_B60
    Visual source: packed Arb_F16C_B60
    A2A: yes
    A2G: yes
02. F-16E Desert Falcon (`UAEJetF16ECegy`)
    Role: strike
    Visual W3D: LSFF16CEgy
    Visual source: DONOR_ART LSFF16CEgy unused unique
    A2A: limited
    A2G: yes
03. UAE_F16Blk52 (`UAE_F16Blk52`)
    Role: existing live unit
    Visual W3D: US_F16CJ_blk52
    Visual source: already packed
    A2A: yes
    A2G: yes
04. F-16F Block 60 (`UAEJetF16F`)
    Role: multirole
    Visual W3D: Egy_F16C
    Visual source: packed Egy_F16C
    A2A: yes
    A2G: yes
05. Mirage 2000-9 (`UAEJetMirage20009`)
    Role: a2a
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000
    A2A: yes
    A2G: no / gun only
06. Mirage 2000-9E (`UAEJetMirage20009E`)
    Role: multirole
    Visual W3D: FraMirage2000
    Visual source: packed FraMirage2000
    A2A: yes
    A2G: yes
07. Mirage 2000DAD (`UAEJetMirage2000DAD`)
    Role: strike
    Visual W3D: LSFMirage2KD
    Visual source: packed LSFMirage2KD
    A2A: limited
    A2G: yes
08. F-15EA (`UAEJetF15EA`)
    Role: strike
    Visual W3D: US_F15EX
    Visual source: packed US_F15EX
    A2A: limited
    A2G: yes
09. F-15E (`UAEJetF15E`)
    Role: strike
    Visual W3D: US_F15E
    Visual source: packed US_F15E
    A2A: limited
    A2G: yes
10. F-15SA (`UAEJetF15SA`)
    Role: a2a
    Visual W3D: Arb_F15SA
    Visual source: packed Arb_F15SA
    A2A: yes
    A2G: no / gun only
11. Hawk 102 (`UAEJetHawk102`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes
12. Mirage 2000-5 (`UAEJetMirage20005`)
    Role: multirole
    Visual W3D: LSFMirage5
    Visual source: packed LSFMirage5
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- UAE_IL-76  Type: transport  Visual: Iraq_IL-76
- UAE_Mi-8T  Type: helicopter  Visual: Irq_MI8T

HELICOPTERS
- UAE_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- UAE_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Libya

FIGHTER AIRBASE — 12/12
01. Libya_Mig-29A (`Libya_Mig-29A`)
    Role: existing live unit
    Visual W3D: Irq_Mig29A
    Visual source: already packed
    A2A: yes
    A2G: yes
02. Libya_MirageF1_Bq (`Libya_MirageF1_Bq`)
    Role: existing live unit
    Visual W3D: Irq_MirageF1_Bq
    Visual source: already packed
    A2A: yes
    A2G: yes
03. Mirage F1BD (`LibyaJetMirageF1BD`)
    Role: multirole
    Visual W3D: UVMirage
    Visual source: packed UVMirage
    A2A: yes
    A2G: yes
04. MiG-23ML (`LibyaJetMig23`)
    Role: multirole
    Visual W3D: MiG-23bn_Irq
    Visual source: packed MiG-23bn_Irq
    A2A: yes
    A2G: yes
05. MiG-25PD (`LibyaJetMig25`)
    Role: interceptor
    Visual W3D: Iraq_Mig-25bm
    Visual source: packed Iraq_Mig-25bm
    A2A: yes
    A2G: no / gun only
06. MiG-21bis (`LibyaJetMig21`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
07. MiG-21MF (`LibyaJetMig21MF`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
08. J-7 (`LibyaJetJ7`)
    Role: legacy
    Visual W3D: LSFJ7
    Visual source: packed LSFJ7
    A2A: yes
    A2G: yes
09. Su-22M3 (`LibyaJetSu22`)
    Role: strike
    Visual W3D: Irq_SU22M3
    Visual source: packed Irq_SU22M3
    A2A: limited
    A2G: yes
10. Su-22M4 (`LibyaJetSu22M4`)
    Role: cas
    Visual W3D: Irn_SU22M2
    Visual source: packed Irn_SU22M2
    A2A: limited
    A2G: yes
11. Libya_Su-25K (`Libya_Su-25K`)
    Role: existing live unit
    Visual W3D: Irq_Su25k
    Visual source: already packed
    A2A: yes
    A2G: yes
12. Su-24MK (`LibyaJetSu24`)
    Role: strike
    Visual W3D: Irq_Su24Mk
    Visual source: packed Irq_Su24Mk
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- Libya_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- Libya_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- Libya_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- Libya_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Syria

FIGHTER AIRBASE — 12/12
01. Syria_Mig-29A (`Syria_Mig-29A`)
    Role: existing live unit
    Visual W3D: Irq_Mig29A
    Visual source: already packed
    A2A: yes
    A2G: yes
02. Syria_MirageF1_Bq (`Syria_MirageF1_Bq`)
    Role: existing live unit
    Visual W3D: Irq_MirageF1_Bq
    Visual source: already packed
    A2A: yes
    A2G: yes
03. MiG-23ML (`SyriaJetMig23`)
    Role: multirole
    Visual W3D: MiG-23bn_Irq
    Visual source: packed MiG-23bn_Irq
    A2A: yes
    A2G: yes
04. MiG-25PD (`SyriaJetMig25`)
    Role: interceptor
    Visual W3D: Iraq_Mig-25bm
    Visual source: packed Iraq_Mig-25bm
    A2A: yes
    A2G: no / gun only
05. MiG-21bis (`SyriaJetMig21`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
06. MiG-21MF (`SyriaJetMig21MF`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
07. J-7 (`SyriaJetJ7`)
    Role: legacy
    Visual W3D: LSFJ7
    Visual source: packed LSFJ7
    A2A: yes
    A2G: yes
08. Su-22M3 (`SyriaJetSu22`)
    Role: strike
    Visual W3D: Irq_SU22M3
    Visual source: packed Irq_SU22M3
    A2A: limited
    A2G: yes
09. Su-22M4 (`SyriaJetSu22M4`)
    Role: cas
    Visual W3D: Irn_SU22M2
    Visual source: packed Irn_SU22M2
    A2A: limited
    A2G: yes
10. Syria_Su-25K (`Syria_Su-25K`)
    Role: existing live unit
    Visual W3D: Irq_Su25k
    Visual source: already packed
    A2A: yes
    A2G: yes
11. Su-24MK (`SyriaJetSu24`)
    Role: strike
    Visual W3D: Irq_Su24Mk
    Visual source: packed Irq_Su24Mk
    A2A: limited
    A2G: yes
12. L-39ZA (`SyriaJetL39`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- Syria_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- Syria_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- Syria_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- Syria_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: South Africa

FIGHTER AIRBASE — 12/12
01. SouthAfrica_MirageF1_Bq (`SouthAfrica_MirageF1_Bq`)
    Role: existing live unit
    Visual W3D: Irq_MirageF1_Bq
    Visual source: already packed
    A2A: yes
    A2G: yes
02. Mirage IIICZ (`SouthAfricaJetMirageIIICZ`)
    Role: interceptor
    Visual W3D: UVMirage
    Visual source: packed UVMirage
    A2A: yes
    A2G: no / gun only
03. Cheetah C (`SouthAfricaJetCheetahC`)
    Role: a2a
    Visual W3D: LSFMirage3
    Visual source: packed LSFMirage3
    A2A: yes
    A2G: no / gun only
04. Cheetah D (`SouthAfricaJetCheetahD`)
    Role: strike
    Visual W3D: LSFMirage5
    Visual source: packed LSFMirage5
    A2A: limited
    A2G: yes
05. Cheetah E (`SouthAfricaJetCheetahE`)
    Role: multirole
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000
    A2A: yes
    A2G: yes
06. JAS 39C Gripen (`SouthAfricaJetGripenC`)
    Role: multirole
    Visual W3D: NAT_EF2000T4
    Visual source: packed NAT_EF2000T4 Gripen stand-in
    A2A: yes
    A2G: yes
07. JAS 39D Gripen (`SouthAfricaJetGripenD`)
    Role: multirole
    Visual W3D: LSFEUEF2000
    Visual source: packed LSFEUEF2000
    A2A: yes
    A2G: yes
08. JAS 39E Gripen (`SouthAfricaJetGripenE`)
    Role: a2a
    Visual W3D: NVJ31
    Visual source: packed NVJ31 Gripen-E stand-in
    A2A: yes
    A2G: no / gun only
09. Hawk 120 (`SouthAfricaJetHawk120`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes
10. Hawk 127 (`SouthAfricaJetHawk127`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_P
    A2A: limited
    A2G: yes
11. Impala Mk II (`SouthAfricaJetImpala`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_D
    A2A: limited
    A2G: yes
12. Buccaneer S.50 (`SouthAfricaJetBuccaneer`)
    Role: strike
    Visual W3D: LSFTornado
    Visual source: packed LSFTornado swing-wing stand-in
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- SouthAfrica_Mi-8T  Type: helicopter  Visual: Irq_MI8T
- SouthAfrica_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- SouthAfrica_Mi-8T — helicopter — constructible on Heavy, W3D Irq_MI8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- SouthAfrica_IL-76 — transport — Iraq_IL-76
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: South Korea

FIGHTER AIRBASE — 12/12
01. F-15K Slam Eagle (`SouthKoreaJetF15K`)
    Role: strike
    Visual W3D: LSFF15K
    Visual source: DONOR_ART LSFF15K unused unique
    A2A: limited
    A2G: yes
02. F-15K (`SouthKoreaJetF15KSlam`)
    Role: strike
    Visual W3D: US_F15E
    Visual source: packed US_F15E second F-15K mesh
    A2A: limited
    A2G: yes
03. F-16C (`SouthKoreaJetF16C`)
    Role: multirole
    Visual W3D: US_F16CJ_blk52
    Visual source: packed US_F16CJ_blk52
    A2A: yes
    A2G: yes
04. F-16D (`SouthKoreaJetF16D`)
    Role: multirole
    Visual W3D: US_F16D_B52
    Visual source: packed US_F16D_B52
    A2A: yes
    A2G: yes
05. KF-16 (`SouthKoreaJetKF16`)
    Role: strike
    Visual W3D: LSFKF16
    Visual source: packed LSFKF16
    A2A: limited
    A2G: yes
06. F-35A (`SouthKoreaJetF35A`)
    Role: stealth / air superiority
    Visual W3D: LSFUSAF35A
    Visual source: packed LSFUSAF35A
    A2A: yes
    A2G: no / gun only
07. KF-21 Boramae (`SouthKoreaJetKF21`)
    Role: a2a
    Visual W3D: LSFJ31
    Visual source: packed LSFJ31 KF-21 stand-in
    A2A: yes
    A2G: no / gun only
08. KF-21 Block 2 (`SouthKoreaJetKF21Blk2`)
    Role: stealth / air superiority
    Visual W3D: NVJ31
    Visual source: packed NVJ31
    A2A: yes
    A2G: no / gun only
09. FA-50 (`SouthKoreaJetFA50`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk FA-50 stand-in
    A2A: limited
    A2G: yes
10. T-50 Golden Eagle (`SouthKoreaJetT50`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_P
    A2A: limited
    A2G: yes
11. F-4E Phantom (`SouthKoreaJetF4E`)
    Role: legacy
    Visual W3D: JPF4
    Visual source: packed JPF4
    A2A: yes
    A2G: yes
12. F-5E Tiger II (`SouthKoreaJetF5E`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_D
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- SouthKoreaHelicopterWZ10ME  Type: helicopter  Visual: CHI_WZ10ME
- SouthKoreaHelicopterMi28N  Type: helicopter  Visual: RUS_MI28N
- SouthKoreaHelicopterKa52M  Type: helicopter  Visual: RUS_Ka52M2

HELICOPTERS
- SouthKoreaHelicopterWZ10ME — helicopter — constructible on Heavy, W3D CHI_WZ10ME
- SouthKoreaHelicopterMi28N — helicopter — constructible on Heavy, W3D RUS_MI28N
- SouthKoreaHelicopterKa52M — helicopter — constructible on Heavy, W3D RUS_Ka52M2
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: North Korea

FIGHTER AIRBASE — 12/12
01. NorthKoreaJetMig29S (`NorthKoreaJetMig29S`)
    Role: existing live unit
    Visual W3D: RUS_Mig35
    Visual source: already packed
    A2A: yes
    A2G: yes
02. MiG-29UB (`NorthKoreaJetMig29UB`)
    Role: a2a
    Visual W3D: LSFruMiG29
    Visual source: packed LSFruMiG29
    A2A: yes
    A2G: no / gun only
03. MiG-21bis (`NorthKoreaJetMig21`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
04. MiG-21PF (`NorthKoreaJetMig21PF`)
    Role: interceptor
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: no / gun only
05. MiG-23ML (`NorthKoreaJetMig23`)
    Role: multirole
    Visual W3D: MiG-23bn_Irq
    Visual source: packed MiG-23bn_Irq
    A2A: yes
    A2G: yes
06. MiG-23BN (`NorthKoreaJetMig23BN`)
    Role: cas
    Visual W3D: MiG-23bn_Irq
    Visual source: packed MiG-23bn_Irq
    A2A: limited
    A2G: yes
07. J-7 (`NorthKoreaJetJ7`)
    Role: legacy
    Visual W3D: LSFJ7
    Visual source: packed LSFJ7
    A2A: yes
    A2G: yes
08. J-7B (`NorthKoreaJetJ7B`)
    Role: legacy
    Visual W3D: LSFJ7
    Visual source: packed LSFJ7
    A2A: yes
    A2G: yes
09. Su-22 (`NorthKoreaJetSu22`)
    Role: strike
    Visual W3D: Irn_SU22M2
    Visual source: packed Irn_SU22M2
    A2A: limited
    A2G: yes
10. Su-22M4 (`NorthKoreaJetSu22M4`)
    Role: strike
    Visual W3D: Irq_SU22M3
    Visual source: packed Irq_SU22M3
    A2A: limited
    A2G: yes
11. NorthKoreaJetSu25T (`NorthKoreaJetSu25T`)
    Role: existing live unit
    Visual W3D: RUS_SU25T
    Visual source: already packed
    A2A: yes
    A2G: yes
12. Su-25UB (`NorthKoreaJetSu25UB`)
    Role: cas
    Visual W3D: RUSU-25
    Visual source: packed RUSU-25
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- NorthKoreaHelicopterWZ10ME  Type: helicopter  Visual: CHI_WZ10ME
- NorthKoreaHelicopterMi28N  Type: helicopter  Visual: RUS_MI28N
- NorthKoreaHelicopterKa52M  Type: helicopter  Visual: RUS_Ka52M2

HELICOPTERS
- NorthKoreaHelicopterWZ10ME — helicopter — constructible on Heavy, W3D CHI_WZ10ME
- NorthKoreaHelicopterMi28N — helicopter — constructible on Heavy, W3D RUS_MI28N
- NorthKoreaHelicopterKa52M — helicopter — constructible on Heavy, W3D RUS_Ka52M2
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Vietnam

FIGHTER AIRBASE — 12/12
01. VietnamJetMig29S (`VietnamJetMig29S`)
    Role: existing live unit
    Visual W3D: RUS_Mig35
    Visual source: already packed
    A2A: yes
    A2G: yes
02. MiG-21bis (`VietnamJetMig21`)
    Role: legacy
    Visual W3D: LSFIDMig21
    Visual source: packed LSFIDMig21
    A2A: yes
    A2G: yes
03. MiG-21MF (`VietnamJetMig21bis`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
04. Su-22M3 (`VietnamJetSu22`)
    Role: strike
    Visual W3D: Irq_SU22M3
    Visual source: packed Irq_SU22M3
    A2A: limited
    A2G: yes
05. Su-22M4 (`VietnamJetSu22M4`)
    Role: cas
    Visual W3D: Irn_SU22M2
    Visual source: packed Irn_SU22M2
    A2A: limited
    A2G: yes
06. Su-27SK (`VietnamJetSu27`)
    Role: a2a
    Visual W3D: LSFRUSU27SK
    Visual source: packed LSFRUSU27SK
    A2A: yes
    A2G: no / gun only
07. Su-27UBK (`VietnamJetSu27UB`)
    Role: a2a
    Visual W3D: LSFSU35
    Visual source: packed LSFSU35
    A2A: yes
    A2G: no / gun only
08. Su-30MK2 (`VietnamJetSu30`)
    Role: multirole
    Visual W3D: RUS_SU30SM2
    Visual source: packed RUS_SU30SM2
    A2A: yes
    A2G: yes
09. Su-30MK2V (`VietnamJetSu30MK2`)
    Role: strike
    Visual W3D: RUSU30
    Visual source: packed RUSU30
    A2A: limited
    A2G: yes
10. Yak-130 (`VietnamJetYak130`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk
    A2A: limited
    A2G: yes
11. L-39 (`VietnamJetL39`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_D
    A2A: limited
    A2G: yes
12. F-5E (`VietnamJetF5E`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk_P captured RVNAF F-5
    A2A: limited
    A2G: yes

HEAVY / LARGE AIRBASE
- VietnamHelicopterWZ10ME  Type: helicopter  Visual: CHI_WZ10ME
- VietnamHelicopterMi28N  Type: helicopter  Visual: RUS_MI28N
- VietnamHelicopterKa52M  Type: helicopter  Visual: RUS_Ka52M2

HELICOPTERS
- VietnamHelicopterWZ10ME — helicopter — constructible on Heavy, W3D CHI_WZ10ME
- VietnamHelicopterMi28N — helicopter — constructible on Heavy, W3D RUS_MI28N
- VietnamHelicopterKa52M — helicopter — constructible on Heavy, W3D RUS_Ka52M2
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- none on this Heavy menu
BOMBERS
- none on this Heavy menu

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: Iraq

FIGHTER AIRBASE — 12/12
01. F-16IQ (`IraqJetF16IQ`)
    Role: multirole
    Visual W3D: US_F16CJ_blk52
    Visual source: packed US_F16CJ_blk52
    A2A: yes
    A2G: yes
02. Iraq_Mig-29A (`Iraq_Mig-29A`)
    Role: existing live unit
    Visual W3D: Irq_Mig29A
    Visual source: already packed
    A2A: yes
    A2G: yes
03. Iraq_Mig-25BM (`Iraq_Mig-25BM`)
    Role: existing live unit
    Visual W3D: Iraq_Mig-25bm
    Visual source: already packed
    A2A: yes
    A2G: yes
04. Iraq_Mig-23ML (`Iraq_Mig-23ML`)
    Role: existing live unit
    Visual W3D: MiG-23bn_Irq
    Visual source: already packed
    A2A: yes
    A2G: yes
05. MiG-21bis (`IraqJetMig21`)
    Role: legacy
    Visual W3D: UVMig-21
    Visual source: packed UVMig-21
    A2A: yes
    A2G: yes
06. Iraq_MirageF1_Bq (`Iraq_MirageF1_Bq`)
    Role: existing live unit
    Visual W3D: Irq_MirageF1_Bq
    Visual source: already packed
    A2A: yes
    A2G: yes
07. Iraq_Su-22M3 (`Iraq_Su-22M3`)
    Role: existing live unit
    Visual W3D: Irq_SU22M3
    Visual source: already packed
    A2A: yes
    A2G: yes
08. Iraq_Su-24MK (`Iraq_Su-24MK`)
    Role: existing live unit
    Visual W3D: Irq_Su24Mk
    Visual source: already packed
    A2A: yes
    A2G: yes
09. Iraq_Su-25K (`Iraq_Su-25K`)
    Role: existing live unit
    Visual W3D: Irq_Su25k
    Visual source: already packed
    A2A: yes
    A2G: yes
10. Su-25UB (`IraqJetSu25UB`)
    Role: cas
    Visual W3D: RUSU-25
    Visual source: packed RUSU-25
    A2A: limited
    A2G: yes
11. L-159 / Tucano-class (`IraqJetL159`)
    Role: cas
    Visual W3D: AVHawk
    Visual source: packed AVHawk light attack
    A2A: limited
    A2G: yes
12. Iraq_Mig25RB (`Iraq_Mig25RB`)
    Role: existing live unit
    Visual W3D: Iraq_Mig-25bm
    Visual source: already packed
    A2A: yes
    A2G: yes

HEAVY / LARGE AIRBASE
- Iraq_Tu-22M3  Type: bomber  Visual: Iraq_Tu22m3
- Iraq_Tu-22M3_AI  Type: bomber  Visual: Iraq_Tu22m3
- Iraq_Su-24MR  Type: fighter  Visual: Irq_Su24MR
- Iraq_Mi-35M3  Type: helicopter  Visual: Iraq_Mi-35M3
- Iraq_Mi-28NE  Type: helicopter  Visual: Irq_MI28NE
- Iraq_Mi-8T  Type: helicopter  Visual: Irq_Mi8T
- Iraq_IL-76  Type: transport  Visual: Iraq_IL-76

HELICOPTERS
- Iraq_Mi-35M3 — helicopter — constructible on Heavy, W3D Iraq_Mi-35M3
- Iraq_Mi-28NE — helicopter — constructible on Heavy, W3D Irq_MI28NE
- Iraq_Mi-8T — helicopter — constructible on Heavy, W3D Irq_Mi8T
UAVs
- none on this Heavy menu
AWACS
- none on this Heavy menu
TRANSPORTS
- Iraq_IL-76 — transport — Iraq_IL-76
BOMBERS
- Iraq_Tu-22M3 — bomber — Iraq_Tu22m3
- Iraq_Tu-22M3_AI — bomber — Iraq_Tu22m3

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

COUNTRY: GLA / Arabic

FIGHTER AIRBASE — 12/12
01. ArabicArmy_F15SA (`ArabicArmy_F15SA`)
    Role: existing live unit
    Visual W3D: Arb_F15SA
    Visual source: already packed
    A2A: yes
    A2G: yes
02. ArabicArmy_F15SA_AA (`ArabicArmy_F15SA_AA`)
    Role: existing live unit
    Visual W3D: Arb_F15SA
    Visual source: already packed
    A2A: yes
    A2G: yes
03. ArabicArmy_F16C_E (`ArabicArmy_F16C_E`)
    Role: existing live unit
    Visual W3D: Arb_F16C_B60
    Visual source: already packed
    A2A: yes
    A2G: yes
04. ArabJetEF2000AA (`ArabJetEF2000AA`)
    Role: existing live unit
    Visual W3D: Arb_EF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
05. ArabicArmy_EF2000 (`ArabicArmy_EF2000`)
    Role: existing live unit
    Visual W3D: Arb_EF2000
    Visual source: already packed
    A2A: yes
    A2G: yes
06. ArabicArmy_Su35 (`ArabicArmy_Su35`)
    Role: existing live unit
    Visual W3D: Egy_SU35
    Visual source: already packed
    A2A: yes
    A2G: yes
07. ArabicArmy_Su30MKA (`ArabicArmy_Su30MKA`)
    Role: existing live unit
    Visual W3D: Arb_Su30MKA
    Visual source: already packed
    A2A: yes
    A2G: yes
08. ArabicArmy_Rafale_DM (`ArabicArmy_Rafale_DM`)
    Role: existing live unit
    Visual W3D: Egy_RafaleM
    Visual source: already packed
    A2A: yes
    A2G: yes
09. Arab_Su-24MK (`Arab_Su-24MK`)
    Role: existing live unit
    Visual W3D: Irq_Su24Mk
    Visual source: already packed
    A2A: yes
    A2G: yes
10. ArabicArmy_Su-24MR (`ArabicArmy_Su-24MR`)
    Role: existing live unit
    Visual W3D: Irq_Su24MR
    Visual source: already packed
    A2A: yes
    A2G: yes
11. Mirage 2000 (`ArabJetMirage2000`)
    Role: multirole
    Visual W3D: LSFMirage2000
    Visual source: packed LSFMirage2000
    A2A: yes
    A2G: yes
12. MiG-29 (`ArabJetMig29`)
    Role: a2a
    Visual W3D: Irq_Mig29A
    Visual source: packed Irq_Mig29A
    A2A: yes
    A2G: no / gun only

HEAVY / LARGE AIRBASE
- GLA/Arabic has only ArabicArmy_Airfield. No Heavy Airbase exists; none was created.
Helicopters/UAVs previously on the fighter pad were moved off the 12-jet menu.

STATUS:
Fighter roster = 12/12
All construct buttons valid = PASS
All W3D refs = PASS
Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)
Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)
Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)

---

## GLOBAL SUMMARY

| Country | Fighters | A2A/Interceptor | Multirole | Strike/CAS/Legacy | Bombers | AWACS | Transports | UAVs | Helicopters |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| France | 12 | 0 | 12 | 0 | 0 | 1 | 1 | 1 | 3 |
| Germany | 12 | 1 | 11 | 0 | 0 | 1 | 2 | 2 | 4 |
| Italy | 12 | 0 | 12 | 0 | 0 | 1 | 2 | 1 | 5 |
| United Kingdom | 12 | 0 | 12 | 0 | 1 | 1 | 2 | 1 | 5 |
| Japan | 12 | 4 | 8 | 0 | 0 | 0 | 1 | 1 | 0 |
| Turkey | 12 | 2 | 6 | 4 | 0 | 1 | 0 | 0 | 3 |
| Iran | 12 | 1 | 11 | 0 | 0 | 0 | 0 | 0 | 2 |
| Pakistan | 12 | 1 | 6 | 5 | 0 | 0 | 1 | 0 | 1 |
| India | 12 | 2 | 5 | 5 | 0 | 0 | 1 | 0 | 1 |
| Israel | 12 | 0 | 9 | 3 | 1 | 1 | 0 | 0 | 0 |
| Saudi Arabia | 12 | 4 | 3 | 5 | 0 | 0 | 1 | 0 | 1 |
| NATO | 12 | 1 | 9 | 2 | 0 | 1 | 0 | 0 | 3 |
| Sweden | 12 | 4 | 3 | 5 | 0 | 1 | 0 | 0 | 3 |
| Ukraine | 12 | 2 | 5 | 5 | 0 | 1 | 0 | 0 | 3 |
| UAE | 12 | 2 | 5 | 5 | 0 | 0 | 1 | 0 | 1 |
| Libya | 12 | 1 | 5 | 6 | 0 | 0 | 1 | 0 | 1 |
| Syria | 12 | 1 | 4 | 7 | 0 | 0 | 1 | 0 | 1 |
| South Africa | 12 | 3 | 4 | 5 | 0 | 0 | 1 | 0 | 1 |
| South Korea | 12 | 3 | 2 | 7 | 0 | 0 | 0 | 0 | 3 |
| North Korea | 12 | 2 | 3 | 7 | 0 | 0 | 0 | 0 | 3 |
| Vietnam | 12 | 2 | 2 | 8 | 0 | 0 | 0 | 0 | 3 |
| Iraq | 12 | 0 | 9 | 3 | 2 | 0 | 1 | 0 | 3 |
| GLA / Arabic | 12 | 1 | 11 | 0 | 0 | 0 | 0 | 0 | 0 |

TOTAL playable countries audited: 23
TOTAL fighter aircraft (constructible 12-slot entries): 276
TOTAL helicopters (on Heavy menus counted): 50
TOTAL UAV/UCAV: 6
TOTAL AWACS: 9
TOTAL transports: 16
TOTAL bombers: 4

A2A/Multirole/Strike counts for existing (non-new) fighters are approximate; new jets use explicit role tags.

PROTECTED:
USA — UNCHANGED
RUSSIA — UNCHANGED
CHINA — UNCHANGED

No new airbases. No Nuclear/Atomic edits. No Fighter/Heavy building swaps.
In-game Zero Hour firing was NOT runtime-tested.

