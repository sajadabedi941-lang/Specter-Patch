# NEW FOLDER AIRCRAFT SOURCE AUDIT

Baseline: `final-global-aircraft-completion-v1` (`_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big`).
Primary art source: New folder multipart archive reconstructed as TEOD (`!TEOD_W3D.big`, `!TEOD_Textures.big`).
TEOD Object/Weapon/CommandSet INI was inspected for names only and was **not** imported.

DATA sha256: `c969158d0378709a7abb4011aed38d6962ba35a7773d51e472b261fcc52e1274` (362897985 bytes)
ART  sha256: `b043d86f4e71964f04c82e6eab8bd770a117b2a6b45763f6f8178d4bb978c812` (688620277 bytes)

Statuses: `NEW_FOLDER_EXACT` | `NEW_FOLDER_CLOSE_MATCH` | `CURRENT_STANDIN_PRESERVED` | `NEW_FOLDER_NOT_FOUND` | `DUPLICATE_MODEL` | `BROKEN_ASSET`

## Dotted aliases

| Alias | Dot | New folder search result | Archive/volume | Exact W3D | Textures | W3D size | Current object | Old visual | New visual | Gameplay identity | Country | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EdaEurodyone. | yes | no Eurodrone / EuroMALE / MALE UAV W3D | !TEOD_W3D.big | — | — | — | GermanyUAVEuroMALE | Nat_Heron | Nat_Heron | Eurodrone MALE recon+PGM x4 | Germany Heavy 8 | CURRENT_STANDIN_PRESERVED |
| neuRonucan. | yes | no nEUROn / Neuron / DassaultNeuron W3D. RU_Skat is a Russian UCAV, not used | !TEOD_W3D.big | — | — | — | FranceUCAVNeuron | CHI_GJ11L | CHI_GJ11L | nEUROn stealth UCAV GBU x2 | France Heavy 5 | CURRENT_STANDIN_PRESERVED |
| Edafcas. | yes | no dedicated FCAS/NGF/SCAF W3D. NVJ31 is FC-31/J-31 family fighter-shaped, not UAV | !TEOD_W3D.big | NVJ31.W3D / NVJ31_D.W3D / NVJ31_E.W3D | J31.dds + housecolor2.dds | 46424 / 46426 / 42748 | GermanyJetFCASNGF | LSFJ31 | NVJ31 | FCAS NGF Meteor x4 + GBU x2 | Germany Heavy 9 | NEW_FOLDER_CLOSE_MATCH |
| Mirage 17. | yes | GLAJetMirage / UVMirage. F1-like delta, kept F1CR identity | !TEOD_W3D.big | UVMirage.W3D / _D / _E | UVMirage.dds, Straight Flush2.dds | 80336 / 80348 / 52063 | FranceJetMirageF1CR | LSFFRF1 | UVMirage | Mirage F1CR | France Fighter 11 | NEW_FOLDER_EXACT |
| Edavulcan. | yes | no Vulcan / Avro / VULCANB2 W3D | !TEOD_W3D.big | — | — | — | BritainBomberVulcan (untouched) | existing B-52-class stand-in | unchanged | Avro Vulcan B.2 not created | UK Heavy 5 existing | NEW_FOLDER_NOT_FOUND |
| EDA tornado. | yes | UVTornado_M.W3D is 7750 bytes and maps UVT-55.dds (T-55 projectile), not a Tornado airframe | !TEOD_W3D.big | UVTornado_M.W3D | UVT-55.dds | 7750 | BritainAircraftTornadoECR | LSFTornado | LSFTornado | Tornado ECR SEAD | UK Heavy 12 | BROKEN_ASSET |
| Dassaultrafale. | yes | no Rafale / DassaultRafale W3D | !TEOD_W3D.big | — | — | — | FranceJetRafaleF4 | LSFIDRafale | LSFIDRafale | Rafale F4 Meteor x6 MICA x4 AASM x4 | France Fighter 12 | CURRENT_STANDIN_PRESERVED |
| RQ_180. | yes | AV_RQ180 flying-wing HALE | !TEOD_W3D.big | AV_RQ180.W3D / _D / _E | Drones_US_RU.dds | 23300 / 23302 / 20926 | AmericaDroneRQ180 | (new) | AV_RQ180 | Unarmed stealth recon. OBJECT_READY_NO_VISIBLE_USA_SLOT | USA (no slot) | NEW_FOLDER_EXACT |
| Turbo vampire. | yes | GLAJetTurboVampire / UV_Turbo | !TEOD_W3D.big | UV_Turbo.W3D / UV_Turbo_D.W3D | GLA-Vampire.dds, Scudmissile.dds | 54918 / 54926 | BritainJetVampireFB5 | (new) | UV_Turbo | Vampire FB.5 cannon/rockets/bombs. No UK slot | UK (no slot) | NEW_FOLDER_EXACT |
| vampire. | yes | GLAJetVampire / UVVampire. Distinct from UV_Turbo | !TEOD_W3D.big | UVVampire.W3D / _D / UVVampire_E1.W3D (UVVampire_E missing) | GLA-Vampire.dds | 47852 / 47864 / 30675 | BritainJetVampireFB9 | (new) | UVVampire | Vampire FB.9. Not DUPLICATE_VAMPIRE_MODEL. No UK slot | UK (no slot) | NEW_FOLDER_EXACT |
| OriohuAV. | yes | RU_Orion | !TEOD_W3D.big | RU_Orion.W3D / RU_Orion_D.W3D | Orion.dds, RU-rotor.dds | 18668 / 18670 | RussiaDronesOrion2 (+ Orion2R) | RUS_Orion2 + Animation | RU_Orion, Animation stripped | Existing Orion recon-strike. No duplicate | Russia | NEW_FOLDER_EXACT |
| cargoplane. | yes | AVCargoPln. TEOD INI AmericaJetCargoPlane. Textures AC130.dds. 4-engine turboprop C-130/AC-130 class. NVCargoPln/UVCargoPln are other nations' cargo and were not used | !TEOD_W3D.big | AVCargoPln.W3D / _D / _E | AC130.dds, AH64 rotor.dds. CWCusAC130.tga NOT in TEOD | 75728 / 75740 / 49567 | JapanJetC130H | donor AVCargoPln/AVCrago2 | TEOD AVCargoPln | JASDF C-130H unarmed transport. Japan slot kept | Japan Heavy 7 | NEW_FOLDER_EXACT |
| Shenygng. | yes | no J-35 name. NVJ31 is Shenyang FC-31/J-31 family | !TEOD_W3D.big | NVJ31.W3D / _D / _E | J31.dds | 46424 / 46426 / 42748 | ChinaJetJ35A | CHAJ31HXNew | NVJ31 | J-35A PL-15 x6 PL-10 x2 LS-6 x2. Existing J-31 unchanged | China Heavy 12 | NEW_FOLDER_CLOSE_MATCH |

### Dotted not-found reports

- Eurodrone: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`Nat_Heron`)
- nEUROn: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`CHI_GJ11L`). `RU_Skat` rejected (wrong nation/shape for French nEUROn)
- Edavulcan: `NEW_FOLDER_VULCAN_NOT_FOUND`. Existing Vulcan object was **not** retargeted to B-52
- Dassaultrafale: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`LSFIDRafale`)
- EDA tornado: `BROKEN_ASSET` (`UVTornado_M` is UVT-55 ammo) / `CURRENT_STANDIN_PRESERVED` (`LSFTornado`)
- CWCusAC130.tga: referenced by TEOD AVCargoPln, **not present** in `!TEOD_Textures.big`. Main skin `AC130.dds` is packed

## Appearance-only aliases (no-dot)

| Alias | New folder W3D | Used? | Target | Status |
|---|---|---|---|---|
| Typhon | NOT FOUND | no | Germany Typhoon live units untouched | NEW_FOLDER_NOT_FOUND |
| F_16 | AVF16.W3D | yes | TurkeyJetF16C only. Turkey F-16 OZGUR stays LSFF16C-family | NEW_FOLDER_EXACT |
| Jh_7A | NVJH-7A.W3D | no | China JH-7 live unit untouched | NEW_FOLDER_EXACT found, not applied (related China unit) |
| J_31 | NVJ31.W3D | yes | GermanyJetFCASNGF + ChinaJetJ35A | NEW_FOLDER_CLOSE_MATCH |
| J_10 / J10fireba | NVJ-10.W3D | yes | PakistanJetJ10CE | NEW_FOLDER_EXACT |
| J_20 | NVJ-20.W3D | no | China J-20 live units untouched | found, not applied |
| J_16 / J16 | NVJ16.W3D | no | China J-16 live units untouched | found, not applied |
| F_35 | AVF-35.W3D | no | USA/UK/IT/DE F-35 live units untouched | found, not applied |
| F_18E | AVF-18.W3D | no | USA F/A-18 live units untouched | found, not applied |
| Mirage2000 | no dedicated W3D (UVMirage is F1-class) | no | France Mirage 2000 untouched | NEW_FOLDER_NOT_FOUND |
| Mig31 | RU-Mig31.W3D | no | Russia MiG-31 untouched | found, not applied |
| su35 / Su35flanker | no SU-35.W3D; SU-37.W3D uses SU-35.dds | yes | IranJetSu35S | NEW_FOLDER_CLOSE_MATCH |
| mirg35 | RUMIG_35.W3D | no | Russia MiG-35 untouched | found, not applied |
| Su34 | RUSU-34.W3D | no | Russia Su-34 untouched | found, not applied |
| Su25 | RUSU-25.W3D | no | Russia Su-25 untouched | found, not applied |
| sqt50Rakfa | PAK-FA.W3D | yes | ItalyJetGCAP | NEW_FOLDER_EXACT |
| Mig21 / Mig21 fishing | UVMig-21.W3D | yes | IranJetMig21Bis | NEW_FOLDER_EXACT |

## Existing stand-ins replaced vs preserved

Replaced Draw/Model only (weapons/CommandSet/cost/CSF/country kept):

- FranceJetMirageF1CR LSFFRF1 -> UVMirage
- JapanJetC130H donor AVCargoPln/AVCargoPln_D1 -> TEOD AVCargoPln / AVCargoPln_E
- ChinaJetJ35A CHAJ31HXNew -> NVJ31
- GermanyJetFCASNGF LSFJ31 -> NVJ31
- IranJetMig21Bis LSFIDMig21 -> UVMig-21
- IranJetSu35S LSFSU35 -> SU-37
- PakistanJetJ10CE CHI_J10C -> NVJ-10
- ItalyJetGCAP qsnt50 -> PAK-FA
- TurkeyJetF16C LSFF16C -> AVF16
- RussiaDronesOrion2 / Orion2R RUS_Orion2+Animation -> RU_Orion (Animation stripped)

Preserved:

- GermanyUAVEuroMALE Nat_Heron
- FranceUCAVNeuron CHI_GJ11L
- FranceJetRafaleF4 LSFIDRafale
- BritainAircraftTornadoECR LSFTornado
- JapanUAVRQ4 US_RQ-4
- TurkeyJetF4ETerm JPF4
- BritainBomberVulcan existing stand-in (not B-52 retarget)
- IranDroneFotros still RUS_Orion2+Animation (not the Russian Orion object)

## New objects (complete, no visible slot)

| Object | W3D | Role | Slot |
|---|---|---|---|
| AmericaDroneRQ180 | AV_RQ180 | Unarmed stealth HALE recon, detector, no A2A/A2G | OBJECT_READY_NO_VISIBLE_USA_SLOT |
| BritainJetVampireFB5 | UV_Turbo | Legacy FB cannon/rockets/bombs | OBJECT_READY_NO_VISIBLE_UK_SLOT |
| BritainJetVampireFB9 | UVVampire | Distinct Vampire, IR+cannon+bombs | OBJECT_READY_NO_VISIBLE_UK_SLOT |

USA Fighter/Large/Heavy 1-12 are full unique units. UK Fighter/Large/Heavy 1-12 are full (Tempest/Phantom protected). Buttons exist; they are not attached to hidden slots 13/14.

## CommandSet slots (unchanged)

- Germany Heavy 8 Eurodrone, 9 FCAS NGF
- France Heavy 5 nEUROn
- France Fighter/Large 11 F1CR, 12 Rafale F4
- UK Heavy 12 Tornado ECR
- Japan Heavy 7 C-130H, 8 RQ-4
- China Heavy 12 J-35A
- Iran Heavy 2 MiG-21bis, 3 Su-35
- Turkey Heavy 6 F-4E Terminator (Turkey Heavy 4 F-16C visual swapped)
- Italy Heavy 8 GCAP
- Pakistan Airfield 9 J-10CE
- Rally 13 / Sell 14 preserved on those sets

No new airbase buildings. No helicopter airfield. No Nuclear/Atomic replacement.

## Country / aircraft / W3D table

| Country | Object | W3D now | Source |
|---|---|---|---|
| Germany | GermanyUAVEuroMALE | Nat_Heron | CURRENT_STANDIN_PRESERVED |
| Germany | GermanyJetFCASNGF | NVJ31 | NEW_FOLDER_CLOSE_MATCH |
| France | FranceUCAVNeuron | CHI_GJ11L | CURRENT_STANDIN_PRESERVED |
| France | FranceJetMirageF1CR | UVMirage | NEW_FOLDER_EXACT |
| France | FranceJetRafaleF4 | LSFIDRafale | CURRENT_STANDIN_PRESERVED |
| UK | BritainAircraftTornadoECR | LSFTornado | CURRENT_STANDIN_PRESERVED / BROKEN_ASSET UVTornado_M |
| UK | BritainBomberVulcan | unchanged | NEW_FOLDER_VULCAN_NOT_FOUND |
| UK | BritainJetVampireFB5 | UV_Turbo | NEW_FOLDER_EXACT, no slot |
| UK | BritainJetVampireFB9 | UVVampire | NEW_FOLDER_EXACT, no slot |
| Japan | JapanJetC130H | AVCargoPln (TEOD) | NEW_FOLDER_EXACT |
| Japan | JapanUAVRQ4 | US_RQ-4 | CURRENT_STANDIN_PRESERVED |
| China | ChinaJetJ35A | NVJ31 | NEW_FOLDER_CLOSE_MATCH |
| Iran | IranJetMig21Bis | UVMig-21 | NEW_FOLDER_EXACT |
| Iran | IranJetSu35S | SU-37 | NEW_FOLDER_CLOSE_MATCH |
| Turkey | TurkeyJetF4ETerm | JPF4 | CURRENT_STANDIN_PRESERVED |
| Turkey | TurkeyJetF16C | AVF16 | NEW_FOLDER_EXACT |
| Italy | ItalyJetGCAP | PAK-FA | NEW_FOLDER_EXACT |
| Pakistan | PakistanJetJ10CE | NVJ-10 | NEW_FOLDER_EXACT |
| Russia | RussiaDronesOrion2 | RU_Orion | NEW_FOLDER_EXACT |
| USA | AmericaDroneRQ180 | AV_RQ180 | NEW_FOLDER_EXACT, no slot |

## Exact New folder W3Ds packed

UVMirage.W3D UVMirage_D.W3D UVMirage_E.W3D
AVCargoPln.W3D AVCargoPln_D.W3D AVCargoPln_E.W3D
NVJ31.W3D NVJ31_D.W3D NVJ31_E.W3D
UVMig-21.W3D UVMig-21_D.W3D UVMig-21_E.W3D
SU-37.W3D SU-37_D.W3D SU-37_E.W3D
NVJ-10.W3D NVJ-10D.W3D NVJ-10_D.W3D
PAK-FA.W3D PAK-FA_D.W3D PAK-FA_E.W3D
AVF16.W3D AVF16_D.W3D AVF16_E.W3D
AV_RQ180.W3D AV_RQ180_D.W3D AV_RQ180_E.W3D
UV_Turbo.W3D UV_Turbo_D.W3D
UVVampire.W3D UVVampire_D.W3D UVVampire_E1.W3D
RU_Orion.W3D RU_Orion_D.W3D

SU-37_E references `5_E.dds`; packed as a copy of TEOD `SU-35_E.dds`.
