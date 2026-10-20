# Supply Centre buy-list restore (France / America / China / Russia)

Static last-win audit inside the packed DATA BIG. This is not an in-game test.

## Baseline

| Item | Value |
| --- | --- |
| HEAD used as source | `f05d4402` construct-button DATA BIG |
| Source DATA | `patch/Release/CONSTRUCT_BUTTON_IMAGES/_SPEC_DATA_ONE.big` |
| Source SHA-256 | `afc804de8a92cb4ba4b527d07f84898f26704b39a548c2b2f0e6c6bb3be08b07` |
| Output DATA | `patch/Release/SUPPLY_CENTRE_BUY_LIST/_SPEC_DATA_ONE.big` |
| Output size | 373955679 bytes |
| Output SHA-256 | `be2f27b7c0d2ce233789909b029d24f2d14a34a6540fed4a71186c3c46095cd4` |
| ART BIG | not modified |

Effective last-wins were taken from `_SPEC_DATA_ONE.big` plus the shipped overlay `0_SPECTER_CountrySupplyIncome.big` (unique paths still parse; same-path `SupplyCenter.ini` is last-won by SPEC DATA because `_` sorts after `0`).

## Shared design (not invented)

NATO/EU Supply Centres already buy the CH47F harvester helicopter from the building (`Britain` / `Germany` / `Italy` / `Nato` / `Sweden` / `Turkey` / `Ukraine`). China-side factions buy a supply truck. Russia overlay design buys a Russia-side supply truck plus Mi-8.

War Factory / Airfield / Helicopter Base rosters were left unchanged. Combat helicopters (Tiger, NH90, Caracal) stay on France Helicopter Base / Heavy Air Base. `Command_ConstructRussia_Mi-17` stays commented: Object `Russia_Mi-17` is not defined.

---

## France

**Building:** `FranceSupplyCenter`  
`Data\INI\Object\Specter\French Armed Forces\Buildings\SupplyCenter.ini`  
`CommandSet = FranceSupplyCenterCommandSet`

**Root cause:** `FranceSupplyCenterCommandSet` last-won as sell-only (`14 = Command_Sell`). The construct button and object already existed (`Command_ConstructFranceHelicopterCH47F` → `FranceHelicopterCH47F`). Overlay spawn already named `FranceHelicopterCH47F`, but the buy slot was never filled. Combat helicopters are produced at `France_HelicopterBaseCommandSet` / `France_HeavyAirBaseCommandSet`, not here.

**Designed buy list:** CH47F only (same NATO Supply Centre pattern). No extra aircraft added.

**Fix:** last-win `FranceSupplyCenterCommandSet` slot 1 = `Command_ConstructFranceHelicopterCH47F`, slot 14 = `Command_Sell`.

**Validation:** button Object = `FranceHelicopterCH47F` (defined). No slot collisions.

---

## America / USA

**Building:** `AmericaSupplyCenter`  
`Data\INI\Object\Specter\United States Of America\Buildings\SupplyCenter.ini`  
`CommandSet = AmericaSupplyCenterCommandSet`

**Root cause:** Accepted overlay `0_SPECTER_CountrySupplyIncome.big` assigned `AmericaSupplyCenterCommandSet_CountryIncome` with `Command_ConstructAmericaSupplyChinook_USA` → `AmericaSupplyChinook_USA`. SPEC DATA same-path last-win restored `AmericaSupplyCenterCommandSet` pointing at `AmericaVehicleChinook` and left the overlay CommandSet unused. The overlay harvester object/button lived only on unique overlay paths, so installing SPEC DATA alone (or SPEC last-winning the building) did not keep that buy chain.

**Designed buy list:** USA Chinook harvester (`AmericaSupplyChinook_USA`) + existing AI M-ATV on slot 16. No new airframes.

**Fix:** last-win both `AmericaSupplyCenterCommandSet` and `AmericaSupplyCenterCommandSet_CountryIncome` to the overlay buttons; pack Object `AmericaSupplyChinook_USA` and its construct button into SPEC DATA.

**Validation:** button Object = `AmericaSupplyChinook_USA` (defined, Side=America). Slots 1 / 13 / 14 / 16 unique.

---

## China

**Building:** `ChinaSupplyCenter`  
`Data\INI\Object\Specter\PLA\Buildings\SupplyCenter.ini`  
`CommandSet = ChinaSupplyCenterCommandSet`

**Root cause:** Overlay retargeted the building to `ChinaSupplyCenterCommandSet_CountryIncome`. SPEC same-path last-win restored the original CommandSet name. The truck button itself was already `Command_ConstructChinaVehicleSupplyTruck` → `ChinaVehicleSupplyTruck`. Commented overlay lines (`Russia_Mi-17`, Lancet) were not part of the current design (`Russia_Mi-17` object missing).

**Designed buy list:** China supply truck only. No aircraft added.

**Fix:** last-win both China Supply Centre CommandSet names to slot 1 = `Command_ConstructChinaVehicleSupplyTruck`, 13 rally, 14 sell. Truck object/stats not rewritten.

**Validation:** button Object = `ChinaVehicleSupplyTruck` (defined). No slot collisions. Mi-17 not added.

---

## Russia

**Building:** `RussiaSupplyCenter`  
`Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\SupplyCenter.ini`  
`CommandSet = RussiaSupplyCenterCommandSet`

**Root cause:** SPEC last-win CommandSet slot 1 = `Command_ConstructChinaVehicleSupplyTruck` (`Side = China`). Overlay design replaced that with `Command_ConstructRussiaSupplyTruck_CountryIncome` → `RussiaSupplyTruck_CountryIncome` (`Side = Russia`) and kept Mi-8 on slot 2. SPEC same-path last-win dropped the Russia-side truck.

**Designed buy list:** Russia supply truck + `RussiaHelicopterMi8AMTSh`. No extra jets. Mi-17 not added.

**Fix:** last-win both Russia Supply Centre CommandSet names to those two UNIT_BUILD buttons; pack Object `RussiaSupplyTruck_CountryIncome` and its construct button into SPEC DATA.

**Validation:** truck Object defined (Side=Russia). Mi-8 Object defined. Slots 1 / 2 / 14 unique.

---

## Packing / last-win files added

| BIG path | Role |
| --- | --- |
| `Data\INI\CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini` | last CommandSet file in the archive |
| `Data\INI\CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini` | USA Chinook + Russia truck UNIT_BUILD |
| `Data\INI\Object\zzzzz_SpecterSupplyCentreBuy\AmericaSupplyChinook_USA.ini` | overlay harvester object |
| `Data\INI\Object\zzzzz_SpecterSupplyCentreBuy\RussiaSupplyTruck_CountryIncome.ini` | overlay harvester object |

Entries 3559 → 3563. ART BIG not rebuilt.

## Preserved last-wins (byte-identical vs source DATA)

Iraq radar CommandSet/Object, 92N6E / HT-233 construct buttons, four SpecterRadar drone buttons, Global Market MIC S-400 buttons, and other-country Supply Centre CommandSets (`Britain`, `Germany`, `Italy`, `Nato`, `Sweden`, `Turkey`, `Ukraine`, `Iran`, `Iraq`, `Japan`) were compared against the construct-button source BIG and left unchanged.
