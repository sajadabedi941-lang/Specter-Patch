# SPECTER Baseline Report

Read-only inventory of the uploaded Specter repository and archives.  
No game files, INI, ART, or packed BIGs were modified to produce this report.

**Inventory date:** 2026-09-03  
**Sources:**

| Layer | Path / artifact | Notes |
|---|---|---|
| Overlay INI | `patch/Data/INI` | Cursor/Specter-Patch loose files. 1527 INI. |
| DATA archive | `_SPEC_DATA_ONE.big` (349,348,307 B, 1,430 files, 2026-07-21) | Extracted from repo zip volumes. |
| Packed ART | `_SPEC_ART_ONE.big` from `art_data.part01–22.rar` (524,800,955 B, 2,787 files, 2026-08-18) | Canonical packed ART for this report. |
| Older ART zip | `_SPEC_ART_ONE.zip` | Older 445 MB ART big. Do not treat as current. |
| Donor ART | `DONOR_Art.part001–069.rar` | 23,118 files; 12,161 W3D. Not loaded by the game unless copied into packed ART or loose `Art/`. |
| Loose Data.zip | `Data.zip` + `Data.z01–z14` | Cursors/movies/scripts. `Data/INI` inside this zip is empty. |
| INIZH.big | **Not in this repository** | Lives in a real Zero Hour game folder. Wins stock `CommandSet.ini` / `CommandButton.ini` paths. |

This environment cannot run Zero Hour. File presence is not in-game proof.

---

## 0. Load order (must know before any edit)

Zero Hour loads every `*.big` in the game folder, case-insensitive alphabetical order. **Later same-path wins.** Loose `Data/` beats every BIG.

After `Launch_Specter.bat` copies SPEC BIGs next to `generals.exe`, typical order is:

`_SPEC_ART_ONE.big` → `_SPEC_DATA_ONE.big` → … → **`INIZH.big` wins `Data\INI\CommandSet.ini` and `Data\INI\CommandButton.ini`**.

Consequences:

1. Packed SPEC `CommandSet.ini` / `CommandButton.ini` are **not** the live USA/stock bars unless a later BIG (`INIZHZ.big`) or loose `Data/INI/CommandSet.ini` + `CommandButton.ini` beats INIZH.
2. Redefining an already-defined **CommandSet** or **CommandButton** name in a second loaded file = `already defined` crash.
3. Unique-path files (`CommandSet_Japan.ini`, `CommandButton_FactionExpansion_Armies.ini`) may add **new** names.
4. Official packer `patch/tools/big/merge_patch_into_spec_big.py` **STOCK_SKIPs** overlay overwrite of: `Weapon.ini`, `CommandButton.ini`, `CommandSet.ini`, `Armor.ini`, `Locomotor.ini`.
5. Specter ControlBar (`ControlBar.wnd`) only shows slots **1–14**. Slots 15–18 exist in INI but are invisible.

---

## 1. Playable factions

### 1.1 DATA-big `PlayerTemplate.ini` (packed 349 MB DATA)

| PlayerTemplate | Side | Playable | Starting building | Object folder in DATA big | Notes |
|---|---|---|---|---|---|
| FactionCivilian | Civilian | No | — | — | Non-playable |
| FactionObserver | Observer | No | — | — | Non-playable |
| FactionAmerica | America | Yes | `AmericaCommandCenter` | United States Of America (285 objects) | Core USA |
| FactionRussia | Russia | Yes | `RussiaCommandCenter` | Armed Forces Of Russian Federation (339) | Core Russia |
| FactionChina | China | Yes | `ChinaCommandCenter` | PLA (110) | Uses `PLAAirfieldCommandSet` on `ChinaAirfield` |
| FactionGLA | GLA | Yes | `GLACommandCenter` | Arabic Alliance (123) | Arabic air roster |
| FactionIraq | Iraq | Yes | `Iraq_CommandCenter` | Iraq Army (247) | Iraq objects also duplicated under North Korea paths |
| FactionNorthKorea | NorthKorea | Yes | `NorthKorea_CommandCenter` | North Korea (83) + copied Iraq files | Many Iraq object-name collisions |
| FactionIran | Iran | Yes | `IranCommandCenter` | Iranian Army (151) | Expanded airfield set |
| FactionNato | Nato | Yes | `NatoCommandCenter` | NATO (91) | NATO air roster |
| FactionAmericaAirForceGeneral | AmericaAirForceGeneral | Yes | `AirF_AmericaCommandCenter` | Israel Defense Forces (85) | Comment in INI: “Israel”. Uses `Isr_*` models |
| FactionBossGeneral | Boss | Yes | `Boss_CommandCenter` | (stock + overlay runtime fix) | Mixed China/USA air |

**Japan is not in the 349 MB DATA big.** Japan exists only in overlay.

Egypt objects exist in DATA big (`Egyptian Armed Forces`, 49 objects) but there is **no** DATA-big `FactionEgypt`. Those units are Side-tagged GLA/America/China and are produced from GLA/Arabic/Egypt airfield sets inside packed DATA.

### 1.2 Overlay `PlayerTemplate_SpecterPatch.ini` (additive)

All `PlayableSide = Yes`. Starting building is `*_MilitaryHQ` (not the CommandCenter object).

| PlayerTemplate | Side | Starting building | CommandSet file (safe unique) |
|---|---|---|---|
| FactionTurkey | Turkey | `Turkey_MilitaryHQ` | `CommandSet_Turkey.ini` |
| FactionUkraine | Ukraine | `Ukraine_MilitaryHQ` | `CommandSet_Ukraine.ini` |
| FactionPakistan | Pakistan | `Pakistan_MilitaryHQ` | `CommandSet_Pakistan.ini` |
| FactionSaudiArabia | SaudiArabia | `SaudiArabia_MilitaryHQ` | `CommandSet_SaudiArabia.ini` |
| FactionUAE | UAE | `UAE_MilitaryHQ` | `CommandSet_UAE.ini` |
| FactionIndia | India | `India_MilitaryHQ` | `CommandSet_India.ini` |
| **FactionJapan** | **Japan** | **`Japan_MilitaryHQ`** | **`CommandSet_Japan.ini` (safe template)** |
| FactionBritain | Britain | `Britain_MilitaryHQ` | `CommandSet_Britain.ini` |
| FactionEgypt | Egypt | `Egypt_MilitaryHQ` | `CommandSet_Egypt.ini` |
| FactionFrance | France | `France_MilitaryHQ` | `CommandSet_France.ini` |
| FactionGermany | Germany | `Germany_MilitaryHQ` | `CommandSet_Germany.ini` |
| FactionIsrael | Israel | `Israel_MilitaryHQ` | `CommandSet_Israel.ini` + `CommandSet_Israel_Integrity.ini` |
| FactionItaly | Italy | `Italy_MilitaryHQ` | `CommandSet_Italy.ini` |
| FactionLibya | Libya | `Libya_MilitaryHQ` | `CommandSet_Libya.ini` |
| FactionSouthAfrica | SouthAfrica | `SouthAfrica_MilitaryHQ` | `CommandSet_SouthAfrica.ini` |
| FactionSouthKorea | SouthKorea | `SouthKorea_MilitaryHQ` | `CommandSet_SouthKorea.ini` |
| FactionSweden | Sweden | `Sweden_MilitaryHQ` | `CommandSet_Sweden.ini` |
| FactionSyria | Syria | `Syria_MilitaryHQ` | `CommandSet_Syria.ini` |
| FactionTaiwan | Taiwan | `Taiwan_MilitaryHQ` | `CommandSet_Taiwan.ini` |
| FactionUN | UN | `UN_MilitaryHQ` | `CommandSet_UN.ini` |
| FactionVietnam | Vietnam | `Vietnam_MilitaryHQ` | `CommandSet_Vietnam.ini` |

**Playable total if overlay is installed:** 10 DATA-big + 21 overlay = **31 playable sides** (plus Civilian/Observer).

---

## 2. Airfields and CommandSets

### 2.1 DATA-big production airfields (ignore civilian hangars)

| Object | Side | CommandSet | Model (packed ART) | File in DATA big |
|---|---|---|---|---|
| `AmericaAirfield` | America | `AmericaAirfieldCommandSet` | `US_AirField` | `…/United States Of America/Buildings/Airfield.ini` |
| `AmericaAirfield_T` | America | `AmericaAirfieldCommandSet_T` | `US_AirField` | `…/Airfield_T.ini` |
| `AmericaAircraftCarrier` | America | `AmericaAircraftCarrierCommandSet` | `PSAirCarrier` | `FactionBuilding.ini` |
| `RussiaAirfield` | Russia | `RussiaAirfieldCommandSet` | `RUS_Airfield` | `…/Russian Federation/Buildings/Airfield.ini` |
| `RussiaAirfield_T` | Russia | `RussiaAirfieldCommandSet_T` | `RUS_Airfield` | `…/Airfield_T.ini` |
| `ChinaAirfield` | China | `PLAAirfieldCommandSet` | `Chi_Airfield` | `…/PLA/Buildings/Airfield.ini` |
| `ChinaAirfield-bk` | China | `ChinaAirfieldCommandSet` | `RUS_Airfield` | AI leftover |
| `ArabicArmy_Airfield` | GLA | `ArabicAirfieldCommandSet` | `Arb_Airfield` | `…/Arabic Alliance/Buildings/Airfield.ini` |
| `ArabicArmy_Airfield_T` | GLA | `ArabicAirfieldCommandSet_T` | `Arb_Airfield` | `…/Airfield_T.ini` |
| `IraqMilitaryAirfield` | Iraq | `Iraq_AirfieldCommandSet` | `Irq_Airfield` | also duplicated under North Korea path |
| `Iraq_Airfield` | Iraq | `Iraq_AirfieldCommandSet_T` | `Irq_Airfield` | AI / T2 |
| `Iraq_Airfield_AI` | Iraq | `Iraq_AirfieldCommandSet_T` | `Irq_Airfield` | |
| `Iraq_Airfield_T` | Iraq | `Iraq_AirfieldCommandSet_T` | `Irq_Airfield` | |
| `NorthKorea_Airfield` | NorthKorea | `NorthKorea_AirfieldCommandSet` | `Irq_Airfield` | |
| `IranAirfield` | Iran | `IranExpandedAirfieldCommandSet` | `iran_airfield` | |
| `NatoAirfield` | Nato | `NatoAirfieldCommandSet` | `US_AirField` | |
| `AirF_AmericaAirfield` | AmericaAirForceGeneral | `AirF_AmericaAirfieldCommandSet` | `Isr_Airfield` | Israel folder |
| `Infa_ChinaAirfield` | ChinaInfantryGeneral | `Infa_ChinaAirfieldCommandSet` | `NBAirfield` | stock general |

Civilian-only (not faction production): `AirfieldHanger01`, `AirfieldHanger02`, `AmericanHangar03`, `CivilianHangar`.

### 2.2 DATA-big CommandCenters (starting buildings)

| Object | Side | CommandSet | Model |
|---|---|---|---|
| `AmericaCommandCenter` | America | `AmericaCommandCenterCommandSet` | `US_Command` |
| `RussiaCommandCenter` | Russia | `RussiaCommandCenterCommandSet` | `RUS_Comms` |
| `ChinaCommandCenter` | China | `ChinaCommandCenterCommandSet` | `Chi_Hq` |
| `GLACommandCenter` | GLA | `GLACommandCenterCommandSet` | `Arb_Command` |
| `Iraq_CommandCenter` | Iraq | `Iraq_CommandCenterCommandSet` | `Irq_Command` |
| `NorthKorea_CommandCenter` | NorthKorea | `NorthKorea_CommandCenterCommandSet` | `NKr_Command` |
| `IranCommandCenter` | Iran | `IranExpandedHQCommandSet` | `Iran_Command` |
| `NatoCommandCenter` | Nato | `NatoCommandCenterCommandSet` | `US_Command` |
| `AirF_AmericaCommandCenter` | AmericaAirForceGeneral | `AirF_AmericaCommandCenterCommandSet` | `Isr_Command` |

### 2.3 DATA-big airfield CommandSet slots (packed SPEC, not INIZH)

Visible bar = slots 1–14. Slots 15+ are packed but invisible.

**`AmericaAirfieldCommandSet` (DATA big)**

| Slot | Button | Object |
|---|---|---|
| 1 | `Command_ConstructAmericaJetRaptor` | `AmericaJetRaptor` |
| 2 | `Command_ConstructAmericaVehicleComanche` | `AmericaVehicleComanche` |
| 3 | `Command_ConstructAmericaJetAurora` | `AmericaJetAurora` |
| 4 | `Command_ConstructAmericaJetA10C` | `AmericaJetA10C` |
| 5 | `Command_ConstructAmericaJetB2Spirit` | `AmericaJetB2Spirit` |
| 6 | `Command_ConstructAmericaJetF-16C_AG` | `AmericaJetF-16C_AG` |
| 7 | `Command_ConstructAmericaJetF-15E_AA` | `AmericaJetF-15E_AA` |
| 8 | `Command_ConstructAmericaJetF-22A_AA` | `AmericaJetF-22A_AA` |
| 9 | `Command_UpgradeAmericaCountermeasures` | upgrade |
| 10 | `Command_ConstructAmericaVehicleUH60` | `AmericaHelicopterUH60` |
| 11 | `Command_ConstructAmericaJetEA18` | `AmericaJetEA18G` |
| 12 | `Command_ConstructAmericaJetB52H` | `AmericaJetB52H` |
| 13 | `Command_ConstructAmericaJetB1R` | `AmericaJetB1R` |
| 14 | `Command_Upgrade_NuclearTipWarhead2` | upgrade |
| 15 | `Command_Sell` | (invisible) |
| 16 | `Command_ConstructAmericaJetE3AWACS` | `AmericaJetE3AWACS` |
| 17 | `Command_ConstructAmericaJetF35C` | `AmericaJetF35C` |
| 18 | `Command_ConstructAmericaJetF35C_AA` | `AmericaJetF35C_AA` |

USA T / T1 / T2 / T3 are reduced AI rosters (`AmericaAirfieldCommandSet_T` … `_T3`).

**`RussiaAirfieldCommandSet` (DATA big)**

| Slot | Button | Object |
|---|---|---|
| 1 | `Command_ConstructRussiaJetSu75Checkmate` | `RussiaJetSu75Checkmate` |
| 2 | `Command_ConstructRussiaJetSu35S` | `RussiaJetSu35S` |
| 3 | `Command_ConstructRussiaJetSu30SM2` | `RussiaJetSu30SM2` |
| 4 | `Command_ConstructRussiaJetSU25T` | `RussiaJetSU25T` |
| 5 | `Command_ConstructRussiaJetSu34` | `RussiaJetSu34` |
| 6 | `Command_ConstructRussiaJetSu35AG` | `RussiaJetSu35AG` |
| 7 | `Command_ConstructRussiaJetSU24M2` | `RussiaJetSU24M2` |
| 8 | `Command_ConstructRussiaJetSu47Recon` | `RussiaJetSu47Recon` |
| 9 | `Command_ConstructRussiaJetMig31K` | `RussiaJetMig31K` |
| 10 | `Command_ConstructRussiaHelicopterMi28N` | `RussiaHelicopterMi28N` |
| 11 | `Command_ConstructRussiaHelicopterKA52` | `RussiaHelicopterKA52` |
| 12 | `Command_ConstructRussiaJetSU24MP` | `RussiaJetSU24MP` |
| 13 | `Command_ConstructRussiaJetTu22M3M` | `RussiaJetTu22M3M` |
| 14 | `Command_ConstructRussiaJetSu57AA` | `RussiaJetSu57AA` |

`RussiaJetSu57` (AG) exists in DATA but is **not** on this set. Dual button families exist in the same `CommandButton.ini`: `Command_ConstructRussian_Su57` → `Russia_Su57` vs `Command_ConstructRussiaJetSu57` → `RussiaJetSu57`.

**`PLAAirfieldCommandSet`** (used by live `ChinaAirfield`): J20B_AG, J50, J16D, WZ10ME, KJ500, J16B bunker, J20B_AA, JH7B, JH7A2, Z18A, J10C.

**`ArabicAirfieldCommandSet`:** F15SA, AH64D, EF2000 AA, F16C_E, Su35, Su30MKA, Su-24MR, CH4B, EF2000, Su-24MK, Rq20B, UH60, F15SA_AA.

**`Iraq_AirfieldCommandSet`:** Su-25K, Su-24MK, Mig-23ML, Mi-35M3, Mi-28NE, Mig-29A, Mig-25BM, Tu-22M3, Su-22M3, Su-24MR, Mi-8T, Mirage F1.

**`IranExpandedAirfieldCommandSet`:** F14A, Mig29A, SU22, SU24M, SU25K, Panha2091, Mi8, plus J10CE / Su47 / Su57E / J20E / MiG41.

**`NatoAirfieldCommandSet`:** Rafale F3, F35C, EF2000 T4, EA18G, F16D Blk52, F35C_AA, EF2000 AA/CAS, AH64E, Tornado ECR, E3A, UH60.

**`AirF_AmericaAirfieldCommandSet`:** Israel-skinned Raptor/Comanche/Aurora/F-35I plus F35I_AA, F16I_AG, F15I Raam, F35I Adir, F16I Sufa, F15 Baz, G550, F15I_AA.

**`NorthKorea_AirfieldCommandSet`:** WZ10ME, Mig29S, J10B, Mig31K, Su25T, Su24M2, JH7A, Tu22M3M, J20B, Mi28N, Ka52M.

**`EgyptAirfieldCommandSet`** (DATA big, GLA-side Egypt units): AH64, CH47, KA52, Mi17, F16C, Mig29M2, Rafale DM / AA, drones.

Also present (stock generals, not Specter core): `Lazr_AmericaAirfieldCommandSet`, `SupW_AmericaAirfieldCommandSet`, `Nuke_ChinaAirfieldCommandSet`, `Tank_ChinaAirfieldCommandSet`, `Infa_ChinaAirfieldCommandSet`, `Boss_ChinaAirfieldCommandSet`, plus `_Upgrade` / `_T#` variants.

**`America_LargeAirBaseCommandSet` is not in DATA-big `CommandSet.ini`.**

### 2.4 Overlay airfields (unique faction buildings)

| Object | Side | CommandSet | Model | File |
|---|---|---|---|---|
| `Japan_Airfield` | Japan | `Japan_AirfieldCommandSet` | `US_AirField` | `…/Japan Self-Defense Forces/Buildings/Japan_Airfield.ini` |
| `Britain_Airfield` | Britain | `Britain_AirfieldCommandSet` | `US_AirField` | Britain |
| `France_Airfield` | France | `France_AirfieldCommandSet` | `US_AirField` | France |
| `Germany_Airfield` | Germany | `Germany_AirfieldCommandSet` | `US_AirField` | Germany |
| `Italy_Airfield` | Italy | `Italy_AirfieldCommandSet` | `US_AirField` | Italy |
| `Sweden_Airfield` | Sweden | `Sweden_AirfieldCommandSet` | `US_AirField` | Sweden |
| `SouthKorea_Airfield` | SouthKorea | `SouthKorea_AirfieldCommandSet` | `US_AirField` | ROK |
| `Taiwan_Airfield` | Taiwan | `Taiwan_AirfieldCommandSet` | `US_AirField` | ROC |
| `UN_Airfield` | UN | `UN_AirfieldCommandSet` | `US_AirField` | UN |
| `Egypt_Airfield_T` | Egypt | `Egypt_AirfieldCommandSet` | `Irq_Airfield` | Egypt |
| `India_Airfield_T` | India | `India_AirfieldCommandSet` | `Irq_Airfield` | India |
| `Pakistan_Airfield_T` | Pakistan | `Pakistan_AirfieldCommandSet` | `Irq_Airfield` | Pakistan |
| `SaudiArabia_Airfield_T` | SaudiArabia | `SaudiArabia_AirfieldCommandSet` | `Irq_Airfield` | Saudi |
| `UAE_Airfield_T` | UAE | `UAE_AirfieldCommandSet` | `Irq_Airfield` | UAE |
| `Ukraine_Airfield_T` | Ukraine | `Ukraine_AirfieldCommandSet` | `Irq_Airfield` | Ukraine |
| `Libya_Airfield_T` | Libya | `Libya_AirfieldCommandSet` | `Irq_Airfield` | Libya |
| `Syria_Airfield_T` | Syria | `Syria_AirfieldCommandSet` | `Irq_Airfield` | Syria |
| `SouthAfrica_Airfield_T` | SouthAfrica | `SouthAfrica_AirfieldCommandSet` | `Irq_Airfield` | South Africa |
| `Vietnam_Airfield_T` | Vietnam | `Vietnam_AirfieldCommandSet` | `Irq_Airfield` | Vietnam |
| `Israel_Airfield_T` | Israel | `Israel_AirfieldCommandSet` | `Irq_Airfield` | Israel overlay |
| `Turkey_Airfield` | Turkey | `Turkey_AirfieldCommandSet_T` | `Irq_Airfield` | Turkey AI |
| `Turkey_Airfield_T` | Turkey | `Turkey_AirfieldCommandSet_T` | `Irq_Airfield` | Turkey |
| `Turkey_Airfield_AI` | Turkey | `Turkey_AirfieldCommandSet_T` | `Irq_Airfield` | Turkey |
| `TurkeyMilitaryAirfield` | Turkey | `Turkey_AirfieldCommandSet` | `Irq_Airfield` | Turkey |
| `America_LargeAirBase` | America | `America_LargeAirBaseCommandSet` | `TheAirPort` | Overlay only |
| `Boss_Airfield` | Boss | `Boss_ChinaAirfieldCommandSet` | `Chi_Airfield` | Runtime fix |

**Gap:** `America_LargeAirBase` references `America_LargeAirBaseCommandSet`, but that set is **not** defined in overlay `CommandSet.ini` or DATA-big `CommandSet.ini`. It exists only in `patch/tools/installer/usa_live/Data/INI/CommandSet.ini`. The hangar object is currently an unused/broken chain unless usa_live / INIZHZ is installed.

### 2.5 Overlay unique airfield CommandSets (Japan-style files)

NATO-clone overlay set (slots 1–7 + rally/sell). All use packed-ART models:

| CommandSet | File | Slots 1–7 (typical) |
|---|---|---|
| `Japan_AirfieldCommandSet` | `CommandSet_Japan.ini` | F35C, EF2000 T4, F16D, EF2000 CAS, CH47F, E3A, MQ9 |
| `Britain_AirfieldCommandSet` | `CommandSet_Britain.ini` | same + Typhoon, F35B |
| `France_AirfieldCommandSet` | `CommandSet_France.ini` | same + Rafale |
| `Germany_AirfieldCommandSet` | `CommandSet_Germany.ini` | same + Eurofighter |
| `Italy_AirfieldCommandSet` | `CommandSet_Italy.ini` | NATO-clone six |
| `Sweden_AirfieldCommandSet` | `CommandSet_Sweden.ini` | NATO-clone six |
| `SouthKorea_AirfieldCommandSet` | `CommandSet_SouthKorea.ini` | same + F15K |
| `Taiwan_AirfieldCommandSet` | `CommandSet_Taiwan.ini` | same + F16V |
| `UN_AirfieldCommandSet` | `CommandSet_UN.ini` | NATO-clone six |

Iraq-clone overlay set (Mig-29A, Mirage F1, Su-25K, Mi-8T, IL-76 + extras):

`Egypt_`, `India_`, `Pakistan_`, `SaudiArabia_`, `UAE_`, `Ukraine_`, `Libya_`, `Syria_`, `SouthAfrica_`, `Vietnam_` each have `*_AirfieldCommandSet` plus `_1` `_2` `_3` tech variants in their own `CommandSet_<Faction>.ini`.

Turkey has a unique domestic roster in `CommandSet_Turkey.ini`: KAAN, F16V, Hurjet, T129, Anka3, TB2, Akinci, Mi-28NE, Mi-35M3, Mi-8T, Tu-22M3, AWACS, Kizilelma.

Israel overlay airfield set (`CommandSet_Israel_Integrity.ini`) only wires AirF Raptor/Comanche/Aurora + rally/sell. Full Israel air lives on DATA-big `AirF_AmericaAirfieldCommandSet`.

### 2.6 Overlay `CommandSet.ini` vs DATA-big (same names — dangerous)

Overlay `patch/Data/INI/CommandSet.ini` **redefines** stock names including `AmericaAirfieldCommandSet`. Slot 5 in overlay `CommandSet.ini` is `Command_ConstructTEODAmericaJetB2` (DATA big uses `Command_ConstructAmericaJetB2Spirit`).

`ZZZZ_USA_Airfield_TEOD_B2_Production.ini` and related ZZZZ files redefine the same five USA airfield set names again. Last-loaded definition wins among loose overlay files; **redefining a name that INIZH already loaded crashes**.

Do not add a sixth definition of `AmericaAirfieldCommandSet`.

---

## 3. Aircraft objects that are actually functional in DATA big

**Definition used here (all must be true):**

1. Object is defined in packed `_SPEC_DATA_ONE.big`.
2. `KindOf` contains `AIRCRAFT` and `SELECTABLE` (not STRUCTURE, PROJECTILE, HULK, or system dummy).
3. A `CommandButton` `Object =` this name is referenced by a DATA-big CommandSet (`ON_SET`).
4. `Model =` stem exists as `Art\W3D\<Model>.W3D` in packed ART.

These are the units a packed-DATA-only install can actually produce if the matching CommandSet is the live set.

### 3.1 USA (`Side = America`) — on a DATA CommandSet + ART present

| Object | Model | Typical producer |
|---|---|---|
| `AmericaJetRaptor` | `US_F16CJ_blk52` | Airfield 1 |
| `AmericaVehicleComanche` | `US_AH64E` | Airfield 2 |
| `AmericaJetAurora` | `US_F15E` | Airfield 3 |
| `AmericaJetA10C` | `US_A10C` | Airfield 4 |
| `AmericaJetB2Spirit` | `US_B1R` | Airfield 5 (DATA name; mesh is B-1R) |
| `AmericaJetF-16C_AG` | `US_F16CMB50` | Airfield 6 |
| `AmericaJetF-15E_AA` | `US_F15C` | Airfield 7 |
| `AmericaJetF-22A_AA` | `US_F22A` | Airfield 8 |
| `AmericaHelicopterUH60` | `US_UH60` | Airfield 10 / CC 12 |
| `AmericaJetEA18G` | `US_EA18G` | Airfield 11 |
| `AmericaJetB52H` | `US_B52H` | Airfield 12 |
| `AmericaJetB1R` | `US_B1R` | Airfield 13 |
| `AmericaJetE3AWACS` | `US_E3G` | Airfield 16 (invisible slot) |
| `AmericaJetF35C` | `US_F35A` | Airfield 17 (invisible slot) |
| `AmericaJetF35C_AA` | `US_F35A` | Airfield 18 (invisible slot) |
| `AmericaHelicopterAH64E` | `US_AH64E` | T-sets |
| `AmericaVehicleChinook` | `US_CH47F` | other sets |
| `AmericaHelicopterCh47F_AI` | `US_CH47F` | CC AI slot 17 |
| `AmericaJetFA18E` | `US_FA18E` | button exists / navy-related |
| `AmericaJetFA18F` | `US_FA18F` | button exists / navy-related |
| `AmericaJetAircraftCarrierRaptor` | `PSCarRapt` | carrier set — **model NOT in packed ART** (donor-only `PSCarRapt`) |

**Present in DATA, ART OK, but NOT on DATA airfield set:**  
`AmericaJetStealthFighter` (`US_F22A`, F-22 AG), `AmericaJetSpectreGunship` (`US_AC130W`), `AmericaJetF-16C_AA` (`US_F-16Cblk52` — **that exact stem is missing from packed ART**), loadout variants `AmericaJetF16CMB50_*`, `AmericaJetF15E_GBU72`.

### 3.2 Russia — on a DATA CommandSet + ART present

| Object | Model |
|---|---|
| `RussiaJetSu75Checkmate` | `RUS_SU57` |
| `RussiaJetSu35S` | `RUS_SU35S` |
| `RussiaJetSu30SM2` | `RUS_SU30SM2` |
| `RussiaJetSU25T` | `RUS_SU25T` |
| `RussiaJetSu34` | `RUS_SU34` |
| `RussiaJetSu35AG` | `RUS_SU35S` |
| `RussiaJetSU24M2` | `RUS_SU24M2` |
| `RussiaJetSu47Recon` | `RUS_SU35S` |
| `RussiaJetMig31K` | `RUS_MIG31K` |
| `RussiaHelicopterMi28N` | `RUS_MI28N` |
| `RussiaHelicopterKA52` | `RUS_Ka52M2` |
| `RussiaJetSU24MP` | `RUS_SU24MP` |
| `RussiaJetTu22M3M` | `RUS_TU22M3M` |
| `RussiaJetSu57AA` | `RUS_SU57` |
| `RussiaHelicopterMi8AMTSh` | `RUS_MI8MTV5` |
| `RussiaDroneOrlan10` | `RUS_Orlan10` |
| `Russia_SU24MP_AI` | `RUS_SU24MP` |

**DATA object exists, ART OK, not on main airfield set:** `RussiaJetSu57` (AG, `RUS_SU57`), `RussiaJetMig35` / `Mig35M`, `RussiaHelicopterKA52C` / `KA52U`, loiter/UCAS variants, `RUS_A50_AWACS`.

### 3.3 China / PLA — on `PLAAirfieldCommandSet` + ART

| Object | Model |
|---|---|
| `ChinaJetJ20B_AG` | `CHI_J20B` |
| `ChinaJetJ50` | `CHI_J20B` |
| `ChinaJetJ16D` | `Chi_J16D` |
| `ChinaHelicopterWZ10ME` | `CHI_WZ10ME` |
| `ChinaAircraftKJ500` | `RUS_A50` |
| `ChinaJetJ16B_Bunker` | `CHI_J20B` |
| `ChinaJetJ20B_AA` | `CHI_J20B` |
| `ChinaJetJH7B_HeavyBunker` | `CHI_JH7A2` |
| `ChinaJetJH7A2` | `CHI_JH7A2` |
| `ChinaHelicopterZ18A` | `CHI_Z18A` |
| `ChinaJetJ10C` | `CHI_J10C` |
| `ChinaJetJ20B_AA_AI` | `CHI_J20B` |

### 3.4 GLA / Arabic Alliance + DATA Egypt (GLA-side)

| Object | Model |
|---|---|
| `ArabicArmy_F15SA` / `_AA` | `Arb_F15SA` |
| `ArabicArmy_AH64D_K` | `Arb_AH64D` |
| `ArabJetEF2000AA` / `ArabicArmy_EF2000` | `Arb_EF2000` |
| `ArabicArmy_F16C_E` | `Arb_F16C_B60` |
| `ArabicArmy_Su35` | `Egy_SU35` |
| `ArabicArmy_Su30MKA` | `Arb_Su30MKA` |
| `ArabicArmy_Su-24MR` | `Irq_Su24MR` |
| `Arab_Su-24MK` | `Irq_Su24Mk` |
| `Arab_UH60` | `US_UH60` |
| `EgyptJetF16C` | `Egy_F16C` |
| `EgyptJetMig29M2` | `Egy_Mig29M2` |
| `EgyptJetRafaleDM` / `_AA` | `Egy_RafaleM` |
| `EgyptVehicleAH64` | `Egy_AH64D` |
| `EgyptVehicleCh47` | `US_CH47F` |
| `EgyptVehicleKA52` | `Arb_Ka52` |
| `EgyptVehicleMi17` | `Egy_MI17` |
| `EgypgtDroneRq20B` | `RUS_Orlan10` |

### 3.5 Iraq

| Object | Model |
|---|---|
| `Iraq_Su-25K` | `Irq_Su25k` |
| `Iraq_Su-24MK` | `Irq_Su24Mk` |
| `Iraq_Mig-23ML` | `MiG-23bn_Irq` |
| `Iraq_Mi-35M3` | `Iraq_Mi-35M3` |
| `Iraq_Mi-28NE` | `Irq_MI28NE` |
| `Iraq_Mig-29A` | `Irq_Mig29A` |
| `Iraq_Mig-25BM` | `Iraq_Mig-25bm` |
| `Iraq_Tu-22M3` / `_AI` | `Iraq_Tu22m3` |
| `Iraq_Su-22M3` | `Irq_SU22M3` |
| `Iraq_Su-24MR` | `Irq_Su24MR` |
| `Iraq_Mi-8T` | `Irq_Mi8T` |
| `Iraq_MirageF1_Bq` | `Irq_MirageF1_Bq` |
| `IraqDronesAbabil200Recon` | `Irq_Ababil200` |

`Iraq_Adnan1` (AWACS) is selectable AIRCRAFT but not on the airfield set.

### 3.6 Iran

| Object | Model |
|---|---|
| `IranJetF14A` | `Iran_F14A` |
| `IranJetMig29A` | `Irn_Mig29A` |
| `IranJetSU22` | `Irn_SU22M2` |
| `IranJetSU24M` | `Irq_Su24Mk` |
| `IranJetSU25K` | `Irq_Su25k` |
| `IranHelicopterPanha2091` | `iran_panha2091` |
| `IranHelicopterMi8` | `Irn_MI8A` |
| `IranJetJ10CE` | `CHI_J10C` |
| `IranJetSu47Berkut` | `RUS_SU35S` |
| `IranJetSu57E` | `RUS_SU57` |
| `IranJetJ20E` | `CHI_J20B` |
| `IranJetMiG41` | `RUS_MIG31K` |
| `IranDroneShahed121` / `Ababil5` | `Irn_Shahed121` |
| `IranDroneFotros` | `RUS_Orion2` |
| `IranDroneOghabEW` | `RUS_Orlan10` |

### 3.7 NATO

| Object | Model |
|---|---|
| `NatoJetRafaleF3` | `Egy_RafaleM` |
| `NatoJetF35C` / `_AA` | `US_F35A` |
| `NatoJetEF2000T4` / `_AA` / `_CAS` | `NAT_EF2000T4` |
| `NatoJetEA18G` | `US_EA18G` |
| `NatoJetF16DBlk52` | `US_F16D_B52` |
| `NatoHelicopterAH64E` | `US_AH64E` |
| `NatoJetTornadoECR` | `US_EA18G` |
| `NatoJetE3AAWACS` | `US_E3G` |
| `NatoHelicopterUH60` | `US_UH60` |
| `NatoHelicopterCH47F` | `US_CH47F` |

### 3.8 AmericaAirForceGeneral / Israel-in-DATA

| Object | Model |
|---|---|
| `AirF_AmericaJetRaptor` | `Isr_F16I` |
| `AirF_AmericaVehicleComanche` | `ISR_AH64D` |
| `AirF_AmericaJetAurora` | `Isr_F15I` |
| `AirF_AmericaJetStealthFighter` | `US_F35A` |
| `IsraelJetF35I_AA` | `US_F35A` |
| `Israel_F16I_AG` | `Isr_F16I` |
| `IsraelJetF15IRaamDeepStrike` | `Isr_F15I` |
| `IsraelJetF35IAdirPenetrator` | `US_F35A` |
| `IsraelJetF16ISufaPrecision` | `Isr_F16I` |
| `IsraelJetF15BazHeavyBomber` | `Isr_F15I` |
| `IsraelJetG550Eitam` | `US_E3G` |
| `Israel_F15I_AA` | `Isr_F15I` |
| `AFG_AmericaVehicleChinook` | `US_UH60` |

`AirF_AmericaJetSpectreGunship1/2/3` use `AVSGunship` — **not in packed ART** (donor-only).

### 3.9 North Korea (DATA)

On `NorthKorea_AirfieldCommandSet`:  
`NorthKoreaHelicopterWZ10ME`, `NorthKoreaJetMig29S`, `NorthKoreaJetJ10B`, `NorthKoreaJetMig31K`, `NorthKoreaJetSu25T`, `NorthKoreaJetSu24M2`, `NorthKoreaJetJH7A`, `NorthKoreaJetTu22M3M`, `NorthKoreaJetJ20B`, `NorthKoreaHelicopterMi28N`, `NorthKoreaHelicopterKa52M`.  
All reuse Russia/PLA ART stems (`RUS_*` / `CHI_*`).  
**These objects are defined twice** (Iraq-folder copies under `North Korea\` and `Data\INI\Object\Specter\North Korea\`).

### 3.10 Overlay-only aircraft (not in DATA big)

Not “DATA-big functional.” Listed so future edits do not treat them as packed-DATA units.

**Japan (safe unique names, packed ART models):**  
`Japan_JetF35C` (`US_F35A`), `Japan_JetEF2000T4` / `_CAS` (`NAT_EF2000T4`), `Japan_JetF16DBlk52` (`US_F16D_B52`), `Japan_HelicopterCH47F` (`US_CH47F`), `Japan_E3A` (`US_E3G`), `Japan_MQ9` (`CHI_CH5` stand-in; packed ART; not `US_MQ9`).

**Same NATO-clone pattern:** Britain / France / Germany / Italy / Sweden / SouthKorea / Taiwan / UN `*_JetF35C`, `*_JetEF2000T4`, `*_JetF16DBlk52`, `*_HelicopterCH47F`, `*_E3A` plus faction extras (Typhoon, Rafale, F15K, F16V, F35B).

**Iraq-clone overlay air:** Egypt / India / Pakistan / Saudi / UAE / Ukraine / Libya / Syria / SouthAfrica / Vietnam `*_Mig-29A`, `*_MirageF1_Bq`, `*_Su-25K`, `*_Mi-8T`, `*_IL-76` plus extras (Tejas, JF17, F15SA, F16Blk60, Su24MK, Bayraktar, etc.). All reuse packed ART stems.

**USA overlay extras (not in 349 MB DATA big):**  
`AmericaJetAuterF22` (`LSFF22` — **donor-only, not in packed ART**), `AmericaJetB21Clean` (`AVB21_A` — in ART), `AmericaJetV22Visual` (`AVOsprey` — in ART), `AmericaJetB2` (`AVB3bmbr` — in ART), overlay F35C retargets to `LSFUSAF35A` / `AVF-35` (see §5).

Turkey has a large overlay-only air roster; every listed Turkey air object in the overlay scan uses a packed-ART stand-in (`US_F22A`, `US_F16CMB50`, `RUS_*`, etc.), not a dedicated Turkey W3D.

---

## 4. Aircraft models available in packed ART big

Packed ART (`art_data` 524 MB): **2,787 files** — `Art\W3D` 1,242, `Art\Textures` 1,285, `Art\Terrain` 260.

Below are **airframe / rotary / UAV / AWACS / bomber hulls** present as `Art\W3D\<Name>.W3D`. Damage (`_D`), rubble (`_R`), and weapon-only meshes are omitted unless they are the only hull.

### 4.1 USA / NATO / stock-style

`US_A10C`  
`US_AC130W`  
`US_AH64D`  
`US_AH64E`  
`US_B1R`  
`US_B52H`  
`US_C130H`  
`US_CH47F`  
`US_E3G`  
`US_EA18G`  
`US_F15C`  
`US_F15E`  
`US_F15EX`  
`US_F16CJ_blk52`  
`US_F16CMB50`  
`US_F16D_B52`  
`US_F22A`  
`US_F35A`  
`US_FA18E`  
`US_FA18F`  
`US_MQ9`  
`US_UH60`  
`NAT_EF2000T4`  
`NAT_CENTB2`  
`AVB21` / `AVB21_A`  
`AVB3bmbr`  
`AVOsprey`  
`AVStealth`  
`E3`

**Buildings in packed ART:** `US_AirField`, `US_Command`.

### 4.2 Russia

`RUS_A50`  
`RUS_IL76MD90A`  
`RUS_Ka52`  
`RUS_Ka52M1`  
`RUS_Ka52M2`  
`RUS_Ka52M3`  
`RUS_MI17R`  
`RUS_MI28N`  
`RUS_MI8MTV5`  
`RUS_MIG31K`  
`RUS_Mig35`  
`RUS_Orion2`  
`RUS_Orlan10`  
`RUS_SU24M2`  
`RUS_SU24MP`  
`RUS_SU25T`  
`RUS_SU25TU`  
`RUS_SU30SM2`  
`RUS_SU34`  
`RUS_SU35S`  
`RUS_SU39`  
`RUS_SU57`  
`RUS_TU160M2`  
`RUS_TU22M3M`  
`RUS_Airfield`

### 4.3 China / PLA

`CHI_J10C`  
`Chi_J16D`  
`CHI_J20B`  
`CHI_JH7A2`  
`CHI_WZ10ME`  
`CHI_Z18A`  
`CHI_GJ11`  
`CHI_CH5`  
`Chi_Airfield`

### 4.4 Arabic / Egypt

`Arb_AH64D`  
`Arb_C130H`  
`Arb_CH47F`  
`Arb_E3A`  
`Arb_EF2000`  
`Arb_F15SA`  
`Arb_F16C_B60`  
`Arb_Ka52`  
`Arb_Rafale_M`  
`Arb_Su30MKA`  
`Arb_SU35`  
`Arb_Airfield`  
`Egy_AH64D`  
`Egy_F16C`  
`Egy_MI17`  
`Egy_Mig29M2`  
`Egy_RafaleM`  
`Egy_SU35`

### 4.5 Iraq / Iran / Israel

`Iraq_IL-76`  
`Iraq_Mi-35M3`  
`Iraq_Mig-25bm`  
`Iraq_Tu22M3` / `Iraq_Tu22m3` / `Irq_TU22M3`  
`Iraq_Ababil200` / `Irq_Ababil200`  
`Irq_MI28NE`  
`Irq_MI8T` / `Irq_Mi8T`  
`Irq_Mig29A`  
`Irq_MirageF1_Bq`  
`Irq_SU22M3`  
`Irq_SU24MK` / `Irq_Su24Mk`  
`Irq_SU24MR` / `Irq_Su24MR`  
`Irq_Su25k`  
`Irq_TU16K` / `Irq_Tu16K`  
`Irq_B340`  
`MiG-23bn_Irq`  
`Iraq_Adnan1`  
`Irq_Airfield`  
`Iran_F14A`  
`Iran_Panha2091` / `iran_panha2091`  
`Irn_MI8A`  
`Irn_Mig29A`  
`Irn_SU22M2`  
`Irn_Su24M`  
`Irn_Su25`  
`Irn_Shahed121`  
`Irn_Shahed136`  
`iran_airfield`  
`ISR_AH64D`  
`Isr_F15I`  
`Isr_F16I`  
`Isr_Airfield`

### 4.6 Confirmed ABSENT from packed ART (commonly mistaken as present)

| Stem | In packed ART? | In DONOR? |
|---|---|---|
| `AVF-35` | **No** | **No** (only `AVF35glass.tga` in donor) |
| `LSFUSAF35A` | **No** | **Yes** (`LSFUSAF35A` / `d` / `k`) |
| `LSFF22` | **No** | **Yes** (`LSFF22` / `d` / `k`) |
| `AMF22A` | **No** | **Yes** |
| `AVSGunship` | **No** | **Yes** |
| `AVChinook` | **No** | **Yes** |
| `AVRaptor` (stock ZH name) | **No** as hull (only related leftovers) | stock ZH ART, not this packed ART |
| `AVComanche` | **No** | **Yes** |
| `AVAurora` | **No** | **Yes** |
| `AVWarthog` | **No** | **Yes** |
| `NVMIG` / `NVHELIX` | **No** | **Yes** (`NVMig` / `NVHelix`) |
| `PSCarRapt` | **No** | **Yes** |
| `US_F-16Cblk52` | **No** | **No** (typo vs `US_F16CJ_blk52`) |

Packed ART **does** contain `US_F22A`, `US_F35A`, `RUS_SU57`, `US_AirField`, `US_Command`, `AVB21`/`AVB21_A`, `AVOsprey`.

---

## 5. Donor-only models not available in packed ART

Donor archive: **12,161 W3D**, **12,152 unique stems**.  
Overlap with packed ART stems: **57**.  
Donor stems **not** in packed ART: **12,095**.

**Rule:** a donor W3D is invisible to the game until it is copied into packed `_SPEC_ART_ONE.big` or loose `Art/W3D` + textures.

### 5.1 Donor-only models actually referenced by current INI

| Model | Referenced by | Packed ART |
|---|---|---|
| `LSFF22` | Overlay `AmericaJetAuterF22` | Missing |
| `LSFUSAF35A` | Overlay `F35C.ini` retarget | Missing |
| `AVF-35` | Overlay `F35C_AA.ini` retarget | Missing **and** missing from donor |
| `AVSGunship` | DATA `AirF_AmericaJetSpectreGunship1/2/3` | Missing |
| `AVChinook` | DATA `AFG_AmericaVehicleChinook_R` | Missing |
| `PSCarRapt` | DATA `AmericaJetAircraftCarrierRaptor` | Missing |
| `NVMig` / `NVMIG` | DATA `Infa_ChinaJetMIG` | Missing |
| `NVHelix` / `NVHELIX` | DATA `Infa_ChinaVehicleHelix` | Missing |

### 5.2 Notable donor aircraft families (not in packed ART)

These are safe to **copy into ART** if a future unit needs them. Do not `Model =` them until copied.

**Stock ZH airframes (donor has them; packed Specter ART replaced them with `US_*` / `RUS_*`):**  
`AVRaptor*`, `AVStealth*` (partial — packed has `AVStealth`), `AVAurora*`, `AVComanche*`, `AVChinook*`, `AVWarthog*`, `AVSGunship*`, `AVB3bmbr` extras.

**LSF / AMF high-detail jets:**  
`LSFF22` / `LSFF22d` / `LSFF22k`  
`LSFUSAF35A` / `LSFUSAF35Ad` / `LSFUSAF35Ak`  
`AMF22A` / `AMF22A_r`  
`LSFF16` / `LSFF16C` / `LSFF16I` / `LSFF15K`  
`LSFEA18G` / `LSFEF2000` / `LSFEUEF2000`  
`LSFA10` / `LSFAV8B` / `LSFAJS37`  
`LSFCHNH6` / `LSFChinaJ8B` / `LSFCNSU30mkk`  
`LSFIDRafale` / `LSFIDMirage2K` / `LSFidMiG29` / `LSFIDMig21`  
`LSFIQSu24` / `LSFIQSu25` / `LSFiqMIG29` / `LSFIqMig25` / `LSFIQF1`  
`LSFIranF5` / `LSFIRAH1J`

Full donor-only air-like stem count under a tight aircraft regex: **1,152** (includes LSF tanks/buildings that share the LSF prefix). Treat donor as a parts closet, not a loadable ART tree.

---

## 6. Duplicate names

### 6.1 Overlay Object names (crash / last-wins risk)

| Object | Files |
|---|---|
| `AmericaAirfield` | `ZZZZZZZZ_ZZZZ_USA_AIRFIELD_B2_RUNTIME.ini` **and** `Object/…/Buildings/Airfield.ini` |
| `AmericaAirfield_T` | same ZZZZ runtime **and** `Airfield_T.ini` |
| `AmericaJetB2` | 7 files (ZZZZ runtime, visual-only, force-unlock, TEOD, TEOD object, DRAW_ONLY, AVB3 draw) |
| `AmericaJetB2Spirit` | 6 files (ZZZZ, unlock, TEOD, `USA_System.ini`, airfield unlock, AAB) |
| `Iraq_Worker` | Iraq folder **and** North Korea copy |
| `MK-84` | B2 payload file **and** `USA_WeaponObjects.ini` |
| `NorthKorea_PowerPlant` | `NorthKorea_Systems.ini` **and** `Iraq_PowerPlant.ini` |
| `R11_CH_Explosion` | 9 faction `*_Systems.ini` copies (Egypt, India, Libya, Pakistan, Saudi, SouthAfrica, Syria, Ukraine, Vietnam) |

### 6.2 Overlay CommandButton names

| CommandButton | Files |
|---|---|
| `Command_ConstructAmericaJetA10C` | `CommandButton.ini`, `CommandButton_USA_AirForce.ini` |
| `Command_ConstructAmericaJetB1R` | `CommandButton.ini`, HeavyAircraft unlock, `CommandButton_USA_AirForce.ini` |
| `Command_ConstructAmericaJetB2Spirit` | `CommandButton.ini` + ZZZZ/TEOD + USA_AirForce |
| `Command_ConstructAmericaJetB52H` | `CommandButton.ini`, HeavyAircraft, USA_AirForce |
| `Command_ConstructAmericaJetE3AWACS` | `CommandButton.ini`, HeavyAircraft |
| `Command_ConstructAmericaJetEA18` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaJetF-15E_AA` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaJetF-16C_AG` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaJetF-22A_AA` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaJetF35C` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaJetF35C_AA` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaVehicleUH60` | `CommandButton.ini`, USA_AirForce |
| `Command_ConstructAmericaStrategyCenter` | `CommandButton.ini`, AAB unlock, StrategyCenter restore |
| `Command_ConstructAmericaStrategyCenter_T` | same |
| `Command_ConstructPatch_America_AC130Spectre` | AirForceExpansion + HeavyAircraft |
| `Command_ConstructPatch_America_B2` | HeavyAircraft + ZZZZ/TEOD |
| `Command_ConstructTEODAmericaJetB2` | `CommandButton.ini` + ZZZZ/TEOD |
| `Command_ConstructRussiaAirfield_T` | **twice inside** `CommandButton.ini` |
| `Command_ConstructRussiaArtillery2S7M` | twice inside `CommandButton.ini` |
| `Command_ConstructRussiaTankT90A` | twice inside `CommandButton.ini` |
| `Command_ConstructRussiaVehicleS500` | twice inside `CommandButton.ini` |
| `Command_ConstructRussiaWarFactory_T` | twice inside `CommandButton.ini` |

`CommandButton_USA_AirForce.ini` must not be packed into DATA or loaded as a second definition of those stock button names.

### 6.3 Overlay CommandSet names

| CommandSet | Files |
|---|---|
| `AmericaAirfieldCommandSet` | `CommandSet.ini` + 3 ZZZZ/TEOD files |
| `AmericaAirfieldCommandSet_T` | same |
| `AmericaAirfieldCommandSet_T1` | same |
| `AmericaAirfieldCommandSet_T2` | same |
| `AmericaAirfieldCommandSet_T3` | same |

### 6.4 DATA-big internal duplicates

- **~250 Object names** defined in both `Data\INI\Object\Specter\Iraq Army\…` and a parallel `North Korea\…` copy of the same Iraq files (workers, hulks, projectiles, air units, airfields). Engine `already defined` risk if both paths load.
- **5 CommandButtons** defined twice in the same DATA `CommandButton.ini` (Russia construct buttons listed above).
- DATA CommandSet names are unique inside the packed `CommandSet.ini`.

### 6.5 Stock / INIZH names that must never be redefined in a second file

Never create a second `CommandSet` or `CommandButton` block for:

- `AmericaAirfieldCommandSet` (+ `_T` `_T1` `_T2` `_T3`)
- `AmericaCommandCenterCommandSet`
- `America_LargeAirBaseCommandSet` (once a single winning definition exists)
- Any `Command_ConstructAmericaJet*` / stock upgrade / sell / rally name already in INIZH or packed `CommandButton.ini`
- Stock objects: `AmericaAirfield`, `AmericaCommandCenter`, `AmericaJetRaptor`, `AmericaVehicleComanche`, `AmericaJetAurora`, `AmericaJetStealthFighter`, and other ZH/Specter core Object names

---

## 7. Safe modification rulebook

Japan is the approved safe pattern. USA stock-name edits are the proven crash / empty-bar pattern.

### 7.1 Hard rules

1. **Never overwrite stock/core INI names.** Do not reuse `AmericaAirfieldCommandSet`, `AmericaCommandCenterCommandSet`, INIZH button names, or packed `CommandSet.ini` / `CommandButton.ini` block names in a second file.
2. **Never create a duplicate Object name.** Search overlay `Object ` and DATA-big objects before adding. `Japan_JetF35C` is safe; `AmericaJetF35C` already exists.
3. **Never `Model =` a donor W3D** unless that stem exists in packed ART **or** the W3D + textures will be copied into `Art/W3D` and `Art/Textures` (and preferably packed ART) in the same change.
4. **Never reference `AVF-35`.** It is in neither packed ART nor donor W3D.
5. **Never pack `CommandButton_USA_AirForce.ini`** or any file that re-declares stock CommandButton names.
6. **Do not edit** overlay `CommandSet.ini` / `CommandButton.ini` to add faction aircraft. Those filenames collide with INIZH / packed cores.
7. Official packer will **not** overlay-replace `Weapon.ini`, `CommandButton.ini`, `CommandSet.ini`, `Armor.ini`, `Locomotor.ini`. Put new weapons in `Weapon_<Faction>.ini`.
8. ControlBar shows slots **1–14** only. Put new produce buttons in 1–12; keep 13 rally and 14 sell on Japan-style sets.
9. Loose `Data/INI` beats every BIG. A bad unique-name file can still crash parse; a duplicate-name file will crash on `already defined`.

### 7.2 Japan-style add: new aircraft on an existing overlay faction

Worked example: Japan F-35.

| Piece | Japan name | Reuses |
|---|---|---|
| Object | `Japan_JetF35C` in `Japan_F35A.ini` | Model `US_F35A` (packed ART) |
| Weapon | `Japan_Weapon_AAM4B_F35J` in `Weapon_Japan.ini` | unique weapon name |
| Button | `Command_ConstructJapan_JetF35C` in `CommandButton_FactionExpansion_Armies.ini` | unique button |
| Set | `Japan_AirfieldCommandSet` in `CommandSet_Japan.ini` slot 1 | unique set |
| Building | `Japan_Airfield` → that set | unique object |
| Player | `FactionJapan` / Side `Japan` | unique template |

Checklist for a new jet on Japan (or Britain/France/…):

1. Confirm the W3D stem is in packed ART (§4) or copy donor → ART first.
2. New `Object <Faction>_Jet<Type>` — name unused in overlay and DATA.
3. `Side = <Faction>`. Unique weapons if needed (`Weapon_<Faction>.ini`).
4. New `CommandButton Command_Construct<Faction>_Jet<Type>` in a **faction or expansion** button file, not `CommandButton.ini`.
5. Add the button to that faction’s **existing unique** `*_AirfieldCommandSet` in a free visible slot (5–12 on Japan; 13–14 reserved).
6. Do not touch `AmericaAirfield`, `AmericaAirfieldCommandSet`, or INIZH names.

### 7.3 Japan-style add: new faction

1. `PlayerTemplate Faction<Name>` in `PlayerTemplate_SpecterPatch.ini` only (do not edit DATA `PlayerTemplate.ini`).
2. Unique `StartingBuilding` (`<Name>_MilitaryHQ`).
3. Unique buildings: `<Name>_CommandCenter`, `<Name>_Airfield`, war factory, etc.
4. Unique CommandSets in `CommandSet_<Name>.ini` only.
5. Unique CommandButtons in `CommandButton_<Name>.ini` or `CommandButton_FactionExpansion_Armies.ini`.
6. Unique sciences / shortcut sets.
7. Reuse packed-ART W3Ds (`US_AirField`, `US_F35A`, `NAT_EF2000T4`, `Irq_*`, `RUS_*`, …).
8. Clone Japan (NATO mesh + unique IDs) or Egypt/Iraq-clone overlay, not USA stock files.

### 7.4 Forbidden / failed pattern (USA Air Force lesson)

Do **not**:

- Invent `AmericaAirfieldCommandSet_USAAirForce` and point `AmericaAirfield` at it. Live USA airfield still uses INIZH `AmericaAirfieldCommandSet`. Unique set is unused; unique buttons vanish when INIZH wins `CommandButton.ini`.
- Copy INIZH sets into a second file under the **same** CommandSet names.
- Claim file-check PASS as in-game proof.

Patching the **single winning** INIZH `CommandSet.ini` / `CommandButton.ini` (via later `INIZHZ.big` or loose copies of those exact paths) is a stock-core edit, not a Japan-safe add. Only do that when the task is explicitly “change the live USA bar,” and still never duplicate those names in extra files.

### 7.5 ART copy rule (when a donor mesh is required)

Allowed sequence:

1. Confirm stem is **absent** from packed ART (§4.6).
2. Confirm stem **exists** in donor (`Art/w3d/<Stem>.W3D` plus `d`/`k` and DDS/TGA).
3. Copy W3D + textures into packed ART (or loose `Art/` that the installer deploys).
4. Only then set `Model = <Stem>` on a **new unique Object**.

Never ship an Object that points at `LSFF22`, `LSFUSAF35A`, or `AVF-35` without step 3. `AVF-35` cannot complete this sequence (no W3D in donor).

Safe default: keep `US_F35A` / `US_F22A` / `RUS_SU57` as Japan did.

### 7.6 Pre-edit search (mandatory)

Before adding any name, search:

- Overlay: `^Object <Name>`, `^CommandButton <Name>`, `^CommandSet <Name>`
- DATA big equivalent (this report §§3 and 6)
- Packed ART stem list (§4)
- Donor-only list (§5) if the model is not in §4

If the name exists, pick a new unique name. Do not “fix” a stock object by re-declaring it.

### 7.7 Recommended file homes for new work

| Kind | Put it here | Never here |
|---|---|---|
| New faction Object | `patch/Data/INI/Object/Specter/<Faction>/…` | `FactionBuilding.ini`, ZZZZ_* runtime |
| New CommandSet | `CommandSet_<Faction>.ini` | `CommandSet.ini`, ZZZZ_USA_* |
| New CommandButton | `CommandButton_<Faction>.ini` or `CommandButton_FactionExpansion_Armies.ini` | `CommandButton.ini`, `CommandButton_USA_AirForce.ini` |
| New Weapon | `Weapon_<Faction>.ini` | `Weapon.ini` |
| New PlayerTemplate | `PlayerTemplate_SpecterPatch.ini` | DATA `PlayerTemplate.ini` |
| New W3D | packed ART or installer-copied `Art/W3D` | donor-only reference |

---

## Appendix A — Working packed-ART chains (reference)

**USA F-22 AA (DATA, packed ART):**  
`AmericaJetF-22A_AA` → `US_F22A` → `Art\W3D\US_F22A.W3D` → airfield slot 8 `Command_ConstructAmericaJetF-22A_AA`.

**USA F-22 AG (DATA object + ART, not on DATA airfield set):**  
`AmericaJetStealthFighter` → `US_F22A` → button `Command_ConstructAmericaJetStealthFighter` (INIZH airfield slot 4, not DATA-big slot 8).

**USA F-35 (DATA object + ART, invisible slots 17–18):**  
`AmericaJetF35C` / `_AA` → `US_F35A`. Overlay F35C.ini may retarget to `LSFUSAF35A` / `AVF-35` (unsafe without ART copy).

**Russia Su-57 AA (DATA, packed ART):**  
`RussiaJetSu57AA` → `RUS_SU57` → airfield slot 14.

**Japan F-35 (overlay, Japan-safe):**  
`Japan_JetF35C` → `US_F35A` → `Command_ConstructJapan_JetF35C` → `Japan_AirfieldCommandSet` slot 1 → `Japan_Airfield`.

---

## Appendix B — Archive facts

| Archive | Size | Files | Role |
|---|---|---|---|
| `_SPEC_DATA_ONE.big` | 349,348,307 | 1,430 | Functional packed DATA |
| `_SPEC_ART_ONE.big` (art_data rar) | 524,800,955 | 2,787 | Functional packed ART |
| DONOR_Art rar | — | 23,118 (12,161 W3D) | Offline mesh closet |
| Overlay `patch/Art` | — | 6 TGA only | Icons, not airframes |

End of baseline. Use this file as the name/model authority for future aircraft and faction work.
