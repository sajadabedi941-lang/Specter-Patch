# DONOR UNUSED AIRCRAFT AUDIT

Baseline: `final-global-aircraft-complete-v1`
DATA sha256 `d0f2c811a1ae234d4bbebcc59859f09b73f770dc0b411865cf419d4e4e3250dd`
ART sha256 `bd0da9ad92cd4838e3d4e5ba9d7c06789d2a5ed5b9a10aafb4742d66a688bba9`

DONOR_ART is visual-only. No donor Object/Weapon/CommandSet INI was imported.
USA / Russia / China live gameplay files were hash-protected and left unchanged.

## Per-alias audit

| # | Alias | Resolved W3D | Texture set | SHA256/16 | Already used? | Existing objects | Unique visual? | Target country | Final identity | Object | Role | CommandSet/Slot | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | F18G | EA18G / LSFEA18G / US_EA18G | LSFEA18G.dds / UsaEA18Map.tga | 4ed1dceb834b031b / 4a28b58c20762da1 / ff6324294ac72e80 | YES | AmericaJetEA18G (US_EA18G); NATO clones share US_EA18G | NO (three hashes) | - | - | - | - | - | USED_ALREADY |
| 02 | Typhon | LSFEUEF2000.W3D | packed Typhoon | 32e8ec01c18a2476 | YES | BritainJetTyphoonFGR4, GermanyJetTyphoonT4/ECR, ItalyJetTyphoon | YES | - | - | - | - | - | USED_ALREADY |
| 03 | Tornado | LSFTornado.W3D | packed Tornado | 8b807972b7e0cab6 | YES | UK/DE/IT Tornado objects | YES | - | - | - | - | - | USED_ALREADY |
| 04 | Rafale | LSFRafale.W3D | packed Rafale | 42ce8cbfcc5d1aa0 | YES | FranceJetRafaleB, FranceJetRafaleC | YES | - | - | - | - | - | USED_ALREADY |
| 05 | Lighting | AVLightn.W3D | AVLightn.dds | 5b71ab3f0fbdc5a4 | YES | BritainJetLightningF6 | YES | - | - | - | - | - | USED_ALREADY |
| 06 | F16Falcon | LSFF16C.W3D | LSFF16C.tga / LSFUSAF16.dds | 83a6c19d1a2c2a71 | NO | none (TurkeyJetF16C now AVF16) | YES | Pakistan | F-16A MLU | PakistanJetF16AMLU | legacy multirole | Pakistan_AirfieldCommandSet 7 | ADDED_EXACT |
| 07 | Eagle | LSFUSAF15C.W3D (+ unused US_F15C.W3D) | LSFUSAF15C.tga / US_F15C.dds | 795178822318e4ca / 2217e98acaada7df | NO | none (USA F-15E uses US_F15E) | YES (two distinct unused hashes) | Japan (+ Israel extra mesh) | F-15J (+ F-15C Baz) | JapanJetF15J / IsraelJetF15CBaz | air superiority / interceptor | Japan_Heavy 9 / Israel_Heavy 3 | ADDED_EXACT |
| 08 | F35B | ENF35A.W3D | Ef35/f35 | 6e008029316a5068 | YES | BritainJetF35B, ItalyJetF35B | YES | - | - | - | - | - | USED_ALREADY |
| 09 | F18prowler fighter | EA18G.W3D / LSFEA18G.W3D | LSFEA18G.dds | 4ed1dceb834b031b / 4a28b58c20762da1 | NO dedicated Prowler; Growler unused extra meshes | none for EA18G/LSFEA18G; US_EA18G used by AmericaJetEA18G | NO vs US_EA18G | - | - | - | - | - | NO_REALISTIC_COUNTRY |
| 10 | F22Raptor | US_F22A.W3D / LSFF22.W3D | packed / LSFF22.dds | 48320fb8eace20d4 / e7dbe3d342c220fc | YES | AmericaJetF-22A_AA; TurkeyJetKAAN | YES (two hashes both live) | - | - | - | - | - | USED_ALREADY |
| 11 | Falcon | LSFF16C.W3D | LSFF16C.tga | 83a6c19d1a2c2a71 | NO | same as 06 | NO | Pakistan | F-16A MLU | PakistanJetF16AMLU | legacy multirole | slot 7 | DUPLICATE_ALIAS |
| 12 | F18PROWLER | EA18G / LSFEA18G / US_EA18G | LSFEA18G.dds | same as 01/09 | YES identity | AmericaJetEA18G | NO extra Prowler mesh | - | - | - | - | - | DUPLICATE_ALIAS |
| 13 | F18HORNET | AmF18A.W3D / F18SEA.W3D | AmF18MA01.tga / F18SEA_*.tga | 81113b17a306d412 / c96e4c9cf302a5b2 | NO | none | YES (two distinct unused Hornet hashes) | - | - | - | - | - | NO_REALISTIC_COUNTRY |
| 14 | Lightning | AVLightn_A1.W3D | AVLightn.dds | c83af18f3e075a98 | NO as aircraft | helper of AVLightn (4035 bytes) | NO | - | - | - | - | - | DUPLICATE_ALIAS |
| 15 | auter f22 | LSFF22.W3D | LSFF22.dds | e7dbe3d342c220fc | YES | TurkeyJetKAAN | NO vs 10 LSFF22 | - | - | - | - | - | DUPLICATE_ALIAS |
| 16 | F15strikeEagle | US_F15E.W3D used; LSFUSAF15E.W3D unused unique | LSFUSAF15E.dds | 952a869cd89d8e77 / c5b4347d456a185c | YES for US_F15E; NO for LSFUSAF15E | AmericaJetF-15E_AA uses US_F15E | YES unused extra hash | Saudi Arabia | F-15S | SaudiJetF15S | strike | SaudiArabia_HeavyAirBaseCommandSet 1 | ADDED_EXACT |
| 17 | F2 | JPF2.W3D | LSFJPF2.dds | 197f5b0832732cad | YES | JapanJetF2A | YES | - | - | - | - | - | USED_ALREADY |
| 18 | F16fighter | LSFKF16.W3D | LSFKF16.dds | edc889829d2bb892 | YES | TurkeyJetF16Ozgur | YES | - | - | - | - | - | USED_ALREADY |
| 19 | Tomcat | Iran_F14A.W3D used; LSFIRF14A.W3D unused extra | LSFF14A.dds | e9cd92e67ef753ab / 11aa6372b8b43b74 | YES for Iran_F14A | IranJetF14A | YES unused extra Tomcat hash | - | - | - | - | - | USED_ALREADY |
| 20 | StrikeEagle | US_F15EX.W3D | packed | 9eabd3d7c16eef9c | YES | AmericaJetAurora / AmericaJetF15E_GBU72 | related to 16 | - | - | - | - | - | DUPLICATE_ALIAS |
| 21 | J11FLANKER | LSFJ11B.W3D | packed | 8b7947638aabc1c0 | YES | ChinaJetJ11B | YES | - | - | - | - | - | USED_ALREADY |
| 22 | auterj31 | LSFJ31.W3D | packed | 82bfb69417a1a5b1 | YES | ChinaJetJ31 (Germany FCAS uses NVJ31) | YES | - | - | - | - | - | USED_ALREADY |
| 23 | J10BRAPTOR | ChJ10B.W3D | packed | 68193997ec77aefe | YES | ChinaJetJ10B (Pakistan J-10CE uses NVJ-10) | YES | - | - | - | - | - | USED_ALREADY |
| 24 | Qiang5 | QIANG5.W3D | chq5m.dds | d4bc2841c6531ea4 | YES | ChinaJetQ5 | YES | - | - | - | - | - | USED_ALREADY |
| 25 | S6-30superflahker | RUS_SU30SM2 used; RUSU30.W3D unused unique | RUSU30MKK.dds | a0d751cad05e7702 / a7bcee3bd0bb51bb | YES for SM2; NO for RUSU30 | RussiaJetSu30SM2 | YES unused extra hash | India | Su-30MKI | IndiaJetSu30MKI | multirole | India_HeavyAirBaseCommandSet 1 | ADDED_EXACT |
| 26 | F16ingLeapard | CHJH7A.W3D unused extra; CHI_JH7A2/NVJH-7A used | chfbc.tga | ce9d3a8b9a0cb8c0 | YES family / NO exact CHJH7A | ChinaJetJH7A2 uses NVJH-7A; clones use CHI_JH7A2 | YES unused extra JH-7 hash | - | - | - | - | - | NO_REALISTIC_COUNTRY |
| 27 | J15A | J15JZ.W3D | packed | 2345cdf7e1df4b22 | YES | ChinaJetJ15 | YES | - | - | - | - | - | USED_ALREADY |
| 28 | J20C | NVJ-20 live China; LSFJ20.W3D unused unique | LSFJ20.dds | 222b75c620cab5f6 / 321abab7aec6b792 | YES China object; NO exact LSFJ20 | ChinaJetJ20C uses NVJ-20 | YES unused extra hash | France | FCAS NGF | FranceJetFCASNGF | air superiority | France_HeavyAirBaseCommandSet 6 | ADDED_AS_REALISTIC_STANDIN |
| 29 | J7chengdu | LSFJ7 used China; LSFPKJ7/LSFIRJ7 unused unique skins | LSFPKJ7.dds / LSFIRJ7.dds | 1c512d3753e82c3a / 557322bab379c87c / dc6d62471406d45d | YES LSFJ7; NO country skins | ChinaJetJ7 | YES two unused country hashes | Pakistan / Iran | F-7PG / F-7N | PakistanJetF7PG / IranJetF7N | legacy fighter | Pakistan_Airfield 8 / Iran_Heavy 4 | ADDED_EXACT |
| 30 | Rafale fighter | LSFRafaleAS.W3D | packed | af9f837cc378743c | YES | FranceJetRafaleM | YES | - | - | - | - | - | USED_ALREADY |
| 31 | Mirage 2000d | LSFMirage2KD.W3D | packed | bd121ff24058722b | YES | FranceJetMirage2000D | YES | - | - | - | - | - | USED_ALREADY |
| 32 | StormFighter | (none) | - | - | NO | none; BritainJetTempest uses SPEC_OLD_F35 | NO dedicated Storm/Tempest W3D | - | - | - | - | - | MISSING_W3D |
| 33 | AuterF2 | LSF02TJ.W3D | chZBD92.dds | 4a0874f501caa0b9 | YES | JapanJetF2Kai | YES | - | - | - | - | - | USED_ALREADY |
| 34 | Shinshin | LSFSX2.W3D | SHAXIN2.dds | f1410feb44057ea6 | YES | JapanJetX2Shinshin | YES | - | - | - | - | - | USED_ALREADY |
| 35 | Eagle Japan | LSFJPF15J.W3D | LSFJPF15J.dds | 8cf833961173e2be | YES | JapanJetF15JKai | YES | - | - | - | - | - | USED_ALREADY |
| 36 | F4phantom | JPF4.W3D | LSFJPF4.dds | dc72dc5cc2140848 | YES | IranJetF4E, JapanJetF4EJKai, TurkeyJetF4ETerm, UK Phantom, Germany F-4F | YES | - | - | - | - | - | USED_ALREADY |
| 37 | F2fighter | AGMZJPF2G.W3D | AGMZJPF2G.tga | 36c871e211a4e969 | YES | JapanJetF2B | YES | - | - | - | - | - | USED_ALREADY |
| 38 | Mirage2000fighter | FraMirage2000.W3D | Mirage2000m.dds | 729bd016f661983e | YES | FranceJetMirage20005F | YES | - | - | - | - | - | USED_ALREADY |
| 39 | Mirage21fighter | LSFFRF1 / LSFMirage3 / LSFMirage5 / UVMirage | packed | 5e36de7862f9abe7 / 626b2380517289e3 / 96bda9bbadd84b8a / 59f722831a4ecf71 | YES | France Mirage F1CT/IIIE/5/F1CR, UK Jaguar, Italy AMX | family used | - | - | - | - | - | USED_ALREADY |

## Unused aliases (still unused after this pass)

These remain unused so they can be assigned manually:

1. **F18G / F18prowler fighter / F18PROWLER extra meshes** `EA18G.W3D` (sha `4ed1dceb834b031b`) and `LSFEA18G.W3D` (sha `4a28b58c20762da1`). Growler identity already live as `AmericaJetEA18G` (`US_EA18G`). No Australia faction. Do not invent German/French/Italian EA-18G service.
2. **F18HORNET** `AmF18A.W3D` (sha `81113b17a306d412`, 214327 bytes, textures AmF18MA01/02) and `F18SEA.W3D` (sha `c96e4c9cf302a5b2`, 559006 bytes, textures F18SEA_1/2/3). Unique unused Hornets. No Australia/Canada/Finland/Spain/Switzerland faction exists in this build.
3. **StormFighter** — no dedicated Tempest/Storm W3D in DONOR_ART. UK Tempest already uses `SPEC_OLD_F35`.
4. **F16ingLeapard extra** `CHJH7A.W3D` (sha `ce9d3a8b9a0cb8c0`). JH-7 family; China already has `ChinaJetJH7A2` on `NVJH-7A`. No realistic non-China JH-7 operator among playable factions.
5. **Tomcat extra** `LSFIRF14A.W3D` (sha `11aa6372b8b43b74`, 311558 bytes). Iran already operates the live `Iran_F14A` Tomcat. Iran is the only realistic F-14 operator; live object was not overwritten.
6. **Lighting helper** `AVLightn_A1.W3D` (4035 bytes) — duplicate helper, not a second aircraft.

Helper/duplicate aliases not given slots: Falcon (11), Lightning (14), auter f22 (15), StrikeEagle (20), F18PROWLER (12).

## New aircraft this pass

| Object | Country | Identity | Role | W3D | Scale | CommandSet | Slot |
|---|---|---|---|---|---|---|---|
| PakistanJetF16AMLU | Pakistan | F-16A MLU | legacy multirole | LSFF16C | 0.90 | Pakistan_AirfieldCommandSet | 7 |
| PakistanJetF7PG | Pakistan | F-7PG | legacy fighter | LSFPKJ7 | 0.86 | Pakistan_AirfieldCommandSet | 8 |
| JapanJetF15J | Japan | F-15J | air superiority | LSFUSAF15C | 1.02 | Japan_HeavyAirBaseCommandSet | 9 |
| IsraelJetF15CBaz | Israel | F-15C Baz | interceptor | US_F15C | 1.00 | Israel_HeavyAirBaseCommandSet | 3 |
| FranceJetFCASNGF | France | FCAS NGF | air superiority | LSFJ20 | 1.00 | France_HeavyAirBaseCommandSet | 6 |
| SaudiJetF15S | Saudi Arabia | F-15S | strike | LSFUSAF15E | 1.05 | SaudiArabia_HeavyAirBaseCommandSet | 1 |
| IndiaJetSu30MKI | India | Su-30MKI | multirole | RUSU30 | 0.92 | India_HeavyAirBaseCommandSet | 1 |
| IranJetF7N | Iran | F-7N | legacy fighter | LSFIRJ7 | 0.86 | Iran_HeavyAirBaseCommandSet | 4 |

Existing aircraft visually upgraded: **0** (no live USA/RU/CN/UK/DE/IT object Model= lines were rewritten).

G. Existing aircraft visually upgraded: 0
H. Added per country: Pakistan 2, Japan 1, Israel 1, France 1, Saudi Arabia 1, India 1, Iran 1
I. Air-superiority count (new): 2 (Japan F-15J, France FCAS NGF)
J. Interceptor count (new): 1 (Israel F-15C Baz)
K. Multirole count (new): 2 (Pakistan F-16A MLU, India Su-30MKI)
L. Strike/CAS/legacy count (new): 3 (Saudi F-15S strike, Pakistan F-7PG, Iran F-7N)
M. Exact donor identity uses: 7
N. Realistic stand-in uses: 1 (LSFJ20 as France FCAS NGF)
O. Unused aliases: F18G extra Growler meshes, F18prowler fighter, F18PROWLER extra, F18HORNET, StormFighter, F16ingLeapard extra CHJH7A, Tomcat extra LSFIRF14A, Lighting helper
P. See unused list above for exact reasons.

Packed completion hashes:

- DATA sha256 `d0f2c811a1ae234d4bbebcc59859f09b73f770dc0b411865cf419d4e4e3250dd`
- ART sha256 `bd0da9ad92cd4838e3d4e5ba9d7c06789d2a5ed5b9a10aafb4742d66a688bba9`

USA/Russia/China CommandSet and object INI hashes matched the complete-v1 baseline after packing.

