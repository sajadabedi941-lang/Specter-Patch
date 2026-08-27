# POST_414_STARTUP_REGRESSION_AUDIT.md

Packed BIG comparison, not git working-tree only.

## Baseline

- Last known runtime-safe: **PR #414** (`cursor/china-aircraft-final-fix-e54a`, 8002fcc).
- Packed DATA used as byte baseline: PR **#413** release `china-aircraft-icon-fix-v1` `_SPEC_DATA_ONE.big`.
- Packed ART used as byte baseline: `china-h20` `_SPEC_ART_ONE.big` (ART from the #413/#414 era).
- Current packed: this v2 repair of `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big`.

## Counts

- New DATA files vs #413 packed: **275**
- Changed DATA files vs #413 packed: **25**
- New W3D vs h20 ART: **189**
- DATA files changed vs crash-fix v1 pack: **6**

## Post-414 PRs inspected

| PR | Title | Startup role |
|---|---|---|
| 414 | Unique China portraits + J-31 A2A | LAST RUNTIME SAFE |
| 415 | France air force rebuild | FIRST duplicate CommandSet (`France_HeavyAirBaseCommandSet`) |
| 416 | France helicopters | Additional PRELOAD helis on Heavy pad |
| 417 | Germany/Italy/UK air forces | G550/H145M Animation crash + more CommandSet dups + TornadoECR button dups |
| 418 | Europe airbase structure | HelicopterBase objects (unused dozer slot); helis folded to Heavy |
| 419 | Europe weapon fire | WeaponSet/FireFX repairs (not uniqueness) |
| 420 | UK diversity | E-7/helis/CommandButtons in CommandSet.ini |
| 421 | UK F-35 / Tempest | Visual/donor |
| 422 | UK E-7 boot crash fix | Removed E-7 Animation= on KVE737; did not fix G550/H145M |
| 423 | Global donor expansion | More aircraft + Weapon.ini inlines |
| 424-428 | Completion / unused donor / 12-fighter roster | More CommandSet.ini injects |
| 429 | Init crash fix v1 | G550/H145M Animation strip only |

## Definite BROKEN items found in packed crash-fix v1 (repaired here)

| File | Object | vs #414 | Risk | Verdict |
|---|---|---|---|---|
| CommandSet_France.ini + CommandSet.ini | France_HeavyAirBaseCommandSet / FranceGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |
| CommandSet_Germany.ini + CommandSet.ini | Germany_HeavyAirBaseCommandSet / GermanyGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |
| CommandSet_Britain.ini + CommandSet.ini | Britain_HeavyAirBaseCommandSet / BritainGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |
| CommandSet_Italy.ini + CommandSet.ini | Italy_HeavyAirBaseCommandSet / ItalyGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |
| CommandSet.ini | Command_ConstructGermanyJetTornadoECR / ItalyJetTornadoECR | Dup vs CommandButton.ini | Init parser | **BROKEN → fixed** |
| Weapon.ini | Japan_Weapon_AAM4B_F15J | Two identical Weapon blocks | Init parser | **BROKEN → fixed** |
| ItalyAircraftG550CAEW.ini | ItalyAircraftG550CAEW | Animation= on 0-anim KVE737 | PRELOAD Draw | **BROKEN → fixed in v1, kept** |
| GermanyHelicopterH145M.ini | GermanyHelicopterH145M | Animation= on 0-anim LSFFenneck | PRELOAD Draw | **BROKEN → fixed in v1, kept** |

## Files actually patched in this v2 DATA BIG vs crash-fix v1

- `Data\INI\CommandSet.ini` (changed)
- `Data\INI\CommandSet_Britain.ini` (changed)
- `Data\INI\CommandSet_France.ini` (changed)
- `Data\INI\CommandSet_Germany.ini` (changed)
- `Data\INI\CommandSet_Italy.ini` (changed)
- `Data\INI\Weapon.ini` (changed)

## New DATA files after #413 (aircraft / airbase related subset)

- `Data\INI\CommandSet_Britain.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\CommandSet_France.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\CommandSet_Germany.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\CommandSet_Italy.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMig29.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMirage2000.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetMirageF1.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\ArabicArmy\Airforce\ArabJetSu25.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftTornadoECR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainBomberVulcan.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainDroneMQ9.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetA400M.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetC17.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHarrierGR9.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHawk200.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetJaguarGR3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetLightningF6.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFG1.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFGR2.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetSeaHarrierFA2.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTempest.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoF3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoGR4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonFGR4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonT3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetVampireFB5.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetVampireFB9.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Buildings\Britain_HelicopterBase.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterApache.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterChinook.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterMerlin.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterPuma.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterWildcat.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceAircraftE3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetFCASNGF.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage20005F.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000D.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage5.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CT.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageIIIE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleC.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleF4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleM.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Airforce\FranceUCAVNeuron.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Buildings\France_HelicopterBase.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterCaracal.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterNH90.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterTiger.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyAircraftE3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyDroneHeronTP.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetA400M.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetAlphaJet.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130J.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF4F.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetFCASNGF.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMako.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMiG29G.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoADV.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoECR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoIDS.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonECR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT1.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyUAVEuroMALE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Buildings\Germany_HelicopterBase.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterCH53.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterH145M.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterNH90.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterTigerUHT.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetAMCA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetJaguarIS.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig21Bison.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig27.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig29K.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000H.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000I.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleDH.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleEH.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetSu30MKI.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTejas.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF14AM.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF4E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF7N.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMig21Bis.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iranian Army\Airforce\IranJetSu35S.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetF16IQ.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetL159.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetSu25UB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF15CBaz.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF15IRaamII.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF16CBarak.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetF4E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetKfir.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetNesher.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyAircraftG550CAEW.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyDroneMQ9.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetAMX.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetC130J.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetC27J.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF16.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetGCAP.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetHarrierII.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetM346FA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetMB339.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoECR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoIDS.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTyphoon.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Buildings\Italy_HelicopterBase.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterA129.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW101.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW139.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW249.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterNH90.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetC130H.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15DJ.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15JKai.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2Kai.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF4EJKai.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetFX.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanUAVRQ4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21MF.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig23.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig25.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMirageF1BD.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22M4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu24.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF16C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF18F.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetF35B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\NATO\Airforce\NatoJetTornadoIDS.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig21PF.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig23.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig23BN.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetMig29UB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu22.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu22M4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetSu25UB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetA5C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16AMLU.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7P.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7PG.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJ10CE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17Blk3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage5.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirageROSE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\PLA\Airforce\ChinaJetJ20C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\PLA\Airforce\ChinaJetJ35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\PLA\Airforce\ChinaJetQ5.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15K.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15KSlam.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16D.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF4E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF5E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetFA50.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF16.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21Blk2.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetT50.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15EX.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15S.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15SA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF5E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetHawk65.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetLightning.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoADV.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoECR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoIDS.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoon.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoonT3.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetBuccaneer.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahC.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahD.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenC.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenD.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk120.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk127.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetImpala.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetMirageIIICZ.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetDrakenJ35.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenE.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetLansenJ32.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60B.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenAJS37.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenJA37.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenSH.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetL39.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21MF.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig23.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig25.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22M4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu24.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16Blk30.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16C.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF16Ozgur.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF35A.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF4E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetF4ETerm.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetHurjet.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetKAAN.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetKAANBlk2.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetNF5.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Turkey Armed Forces\Airforce\TurkeyJetRF4E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetF16AM.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29MU1.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMirage2000.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24M.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24MR.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25M1.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27UB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15EA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15SA.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16ECegy.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16F.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetHawk102.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20005.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage2000DAD.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\United States Of America\Airforce\AmericaDroneRQ180.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetF5E.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetL39.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21bis.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22M4.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27UB.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30MK2.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)
- `Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)

Full new DATA file count: 275. Non-air new files are Specter extras packed by later roster packers (portraits, CSF, mapped images). They are listed in the packer re-extract tree.

## New W3D vs h20 ART

189 meshes. Zero-byte/tiny (<2KB) new W3Ds: **0**.

Suspect large-but-static TEOD / donor meshes (0 anim chunks, used as Model= without Animation=):

- `avf-35.W3D` size=41242 anim_chunks=0 — SUSPICIOUS static mesh
- `nvj31.W3D` size=46424 anim_chunks=0 — SUSPICIOUS static mesh
- `nvj-20.W3D` size=42909 anim_chunks=0 — SUSPICIOUS static mesh
- `uvmirage.W3D` size=80336 anim_chunks=0 — SUSPICIOUS static mesh
- `pak-fa.W3D` size=74234 anim_chunks=0 — SUSPICIOUS static mesh
- `su-37.W3D` size=110969 anim_chunks=0 — SUSPICIOUS static mesh
- `avf16.W3D` size=96772 anim_chunks=0 — SUSPICIOUS static mesh
- `avf-18.W3D` size=76947 anim_chunks=0 — SUSPICIOUS static mesh
- `uvmig-21.W3D` size=51058 anim_chunks=0 — SUSPICIOUS static mesh
- `nvj-10.W3D` size=57968 anim_chunks=0 — SUSPICIOUS static mesh
- `avcargopln.W3D` size=75728 anim_chunks=1 — has animation
- `kve737.W3D` size=44628 anim_chunks=0 — SUSPICIOUS static mesh
- `lsffenneck.W3D` size=70160 anim_chunks=0 — SUSPICIOUS static mesh

## Texture dependency (new W3Ds)

Exact case-sensitive filename in SPEC ART. TGA in W3D vs DDS in ART is reported as unresolved-in-SPEC, not auto-deleted.

New W3Ds with at least one texture string not packed as that exact leaf in SPEC ART: **59** / 189.

This is **SUSPICIOUS** for in-game missing skins, not a proven init exception. EnglishZH and DDS cache often supply the same material.

## Object inheritance / duplicates

- New duplicate Object names vs #413: **0**
- New duplicate Weapon names vs #413 after repair: **0**
- New duplicate CommandSet names vs #413 after repair: **0** (the eight European collisions removed)
- New duplicate CommandButton names vs #413 after repair: **0** (TornadoECR CommandSet.ini copies removed)
- ChildObject: none added

## USA / Russia / China protection

America/Russia/China Airfield + Large + Heavy CommandSet SHA256 unchanged from crash-fix v1 / roster v1.
327 USA/RU/PLA object INI file hashes unchanged.

## Verdict per gate

| Gate | Result |
|---|---|
| INI parser | PASS |
| Object uniqueness (new vs #413) | PASS |
| Weapon uniqueness (new vs #413) | PASS |
| CommandButton refs (European air sets) | PASS |
| CommandSet refs (European air sets) | PASS |
| MappedImage uniqueness | PASS (China #414 portraits kept) |
| SpecialPower uniqueness | PASS |
| Locomotor uniqueness | PASS |
| Projectile refs (repaired weapon) | PASS |
| W3D existence (G550/H145M/KVE737) | PASS |
| W3D animation-reference (no KVE737/LSFFENNECK Animation=) | PASS |
| Preload (new E-7-class) | PASS |
| End-balance (repaired objects) | PASS |
| CSF | PASS |
| BIG re-extract | PASS |

**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**
