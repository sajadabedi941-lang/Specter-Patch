# Construct-button images: new cameos actually packed

Reference: SPE.part001.rar–SPE.part058.rar, git `aac7ffc1`.  
Source DATA: Iraq-radar `_SPEC_DATA_ONE.big` (`43854413…`).  
Source ART: repo split zip `_SPEC_ART_ONE.zip` + `.z01`–`.z09` (`445,953,809` bytes).

**In-game UI was not tested.** Generals Zero Hour is not in this environment. Images were confirmed inside the rebuilt BIGs (TGA decode + last-win INI), not on a live control bar.

## Root cause

Replacing PNG/DDS in the repo is not enough. The live chain is:

`CommandSet` → `CommandButton` → `ButtonImage` → `MappedImage` → `Texture = *.tga` → `Art\Textures\*.tga` inside the effective ART BIG.

DATA already last-won the added construct buttons to new MappedImages:

| Button class | Effective ButtonImage | MappedImage Texture |
|---|---|---|
| Global Market building (dozer) | `Button_GlobalMarket` | `Button_GlobalMarket.tga` |
| Global Market shop AD/radar | `specbtn_mic_*` | `specbtn_mic_*.tga` |
| Four radar drones | `specbtn_heron` / `specbtn_mq4` / `specbtn_orlan10` / `specbtn_shahedlnchr` | matching `.tga` |

Those TGA files were **absent** from `_SPEC_ART_ONE.big` (0 `specbtn_*`, 0 `Button_GlobalMarket`). SAGE then shows the object's `SelectPortrait` atlas cameo (`irq_mic`, `rus_s400r`, `Nat_heron`, …). That is the old image in the build/buy menu.

Native factory AD/radar `UNIT_BUILD` buttons still named those atlas MappedImages (`rus_s400r`, `pla_hq9b`, `us_thaad`, …), so even a packed `specbtn_mic_s400.tga` would not reach Russia's S-400 factory button until `ButtonImage` last-wins.

`SelectPortrait` is intentionally unchanged. Construct buttons do not reuse the unit model or portrait.

## BIG hashes

| File | Size | SHA-256 |
|---|---|---|
| Prior DATA `_SPEC_DATA_ONE.big` (Iraq radar) | 373,920,910 | `43854413bf3cf8a1a942b2b271328dd33ff44a5d5962e5a451ccf73fa720ab8d` |
| This DATA `_SPEC_DATA_ONE.big` | 373,937,384 | `afc804de8a92cb4ba4b527d07f84898f26704b39a548c2b2f0e6c6bb3be08b07` |
| Prior ART `_SPEC_ART_ONE.big` | 445,953,809 | (split zip in repo) |
| This ART `_SPEC_ART_ONE.big` | 447,200,634 | `e796fadcae1d0184a1e79e95e32a986782562c8040c13720873916a98fe9631f` |

DATA entries 3558 → 3559. ART entries 2683 → 2702 (19 new 128×128 32-bit TGA). Header still BIGF; size field matches file length.

New DATA last-win: `Data\INI\CommandButton_ZZZZ_ZZZZConstructCameos.ini` (after `CommandButton_ZZZZ_ZZZ92N6E.ini`).

## Four drones (from real CommandSets)

Objects: `SpecterRadar_Heron`, `SpecterRadar_MQ4`, `SpecterRadar_Orlan10`, `SpecterRadar_ShahedLauncher`.  
Buttons (unchanged names): `Command_ConstructSpecterRadarHeron` / `MQ4` / `Orlan10` / `ShahedLauncher`.

Countries whose radar CommandSet last-win contains all four:

Britain, France, Germany, India, Iraq, Italy, Japan, Libya, Pakistan, Saudi Arabia, South Africa, South Korea, Sweden, Syria, Turkey, UAE, Ukraine, Vietnam.

Iraq uses `CommandSet_ZZZZ_ZZZIraqRadar.ini` (Spy Satellite still off; four drones kept). Others use `CommandSet_ZZZZ_SpySatelliteRadar.ini`.

Not on this four-drone overlay (own radar drone lineups left alone): America, China, Iran, Israel, Nato, North Korea, Russia.

Native country Heron / MQ-4 / Shahed launcher buttons (`Command_ConstructSwedenDroneHeron`, `Command_ConstructAmericaDroneMQ4`, `Command_ConstructIranVehicleShahedLauncher`, …) still use `Nat_heron` / `us_mq4` / `irn_shahedlncher`. Those are different objects.

## Comparative button table

Last-wins: MappedImage from `SpecterUavMicCameos_Images.INI` / `IraqConstructFix_Images.INI`. TGA last-win is unique (only copy, in `_SPEC_ART_ONE.big`). Packed = yes for every row.

### A. Global Market building (dozer construct)

Shop product buttons are **not** these. `SelectPortrait` stays `irq_mic`.

| Country / unit | CommandButton | ButtonImage | Texture | ART BIG | Last-win |
|---|---|---|---|---|---|
| Iraq / Iraq_MIC | Command_ConstructIraq_MIC | Button_GlobalMarket | Button_GlobalMarket.tga | `_SPEC_ART_ONE.big` | CommandButton.ini |
| America, Britain, China, France, Germany, India, Iran, Israel, Italy, Japan, Libya, Nato, North Korea, Pakistan, Russia, Saudi Arabia, South Africa, South Korea, Sweden, Syria, Turkey, UAE, Ukraine, Vietnam / `*_GlobalStore` | Command_Construct*_GlobalStore | Button_GlobalMarket | Button_GlobalMarket.tga | `_SPEC_ART_ONE.big` | CommandButton_ZZZZ_ZGlobalStoreExpand.ini or ZGlobalStoreFive.ini |

### B. Global Market shop AD / radar (buy menu)

CommandSet last-win: `Iraq_MICCommandSet` / `2` / `3` in `CommandSet_ZZZZ_IraqMicToWfRadarAd.ini`. ButtonImage names were already `specbtn_mic_*`; only the TGA was missing.

| Unit | CommandButton | ButtonImage | Texture |
|---|---|---|---|
| Arrow | Command_ConstructIraq_MIC_Arrow | specbtn_mic_arrow | specbtn_mic_arrow.tga |
| Israel AN/TPY-2 | Command_ConstructIraq_MIC_AN_TPY2 | specbtn_mic_tpy2 | specbtn_mic_tpy2.tga |
| 92N6E | Command_ConstructIraq_MIC_92N6R | specbtn_mic_92n6r | specbtn_mic_92n6r.tga |
| S-400 | Command_ConstructIraq_MIC_S400 | specbtn_mic_s400 | specbtn_mic_s400.tga |
| Pantsir-S1M | Command_ConstructIraq_MIC_PantsirS1M | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |
| Krasukha-4 | Command_ConstructIraq_MIC_Krasukha4 | specbtn_mic_krasukha | specbtn_mic_krasukha.tga |
| 96L6-TSP | Command_ConstructIraq_MIC_96L6TSP | specbtn_mic_96l6tsp | specbtn_mic_96l6tsp.tga |
| S-500 | Command_ConstructIraq_MIC_S500 | specbtn_mic_s500 | specbtn_mic_s500.tga |
| HQ-9 | Command_ConstructIraq_MIC_HQ9 | specbtn_mic_hq9 | specbtn_mic_hq9.tga |
| HT-233 | Command_ConstructIraq_MIC_HT233 | specbtn_mic_ht233 | specbtn_mic_ht233.tga |
| TRML-4D | Command_ConstructIraq_MIC_TRML4D | specbtn_mic_trml4d | specbtn_mic_trml4d.tga |
| IRIS-T | Command_ConstructIraq_MIC_IRIST | specbtn_mic_irist | specbtn_mic_irist.tga |
| US AN/TPY-2 | Command_ConstructIraq_MIC_US_AN_TPY2 | specbtn_mic_ustpy2 | specbtn_mic_ustpy2.tga |
| THAAD | Command_ConstructIraq_MIC_THAAD | specbtn_mic_thaad | specbtn_mic_thaad.tga |

### C. Four drones (radar production)

| Unit | CommandButton | ButtonImage | Texture |
|---|---|---|---|
| Heron | Command_ConstructSpecterRadarHeron | specbtn_heron | specbtn_heron.tga |
| MQ-4 | Command_ConstructSpecterRadarMQ4 | specbtn_mq4 | specbtn_mq4.tga |
| Orlan-10 | Command_ConstructSpecterRadarOrlan10 | specbtn_orlan10 | specbtn_orlan10.tga |
| Shahed launcher | Command_ConstructSpecterRadarShahedLauncher | specbtn_shahedlnchr | specbtn_shahedlnchr.tga |

### D. Native country AD / radar construct (factory / war factory)

`ButtonImage` only, via `CommandButton_ZZZZ_ZZZZConstructCameos.ini`. `SelectPortrait` still atlas. `RussiaVehicle55K6E` still `rus_92n6r`.

| Country / unit | CommandButton | Old ButtonImage | Final ButtonImage | Texture |
|---|---|---|---|---|
| USA / US_AN_TPY2 | Command_ConstructAmericaVehicleAN_TPY2 | us_tpy2 | specbtn_mic_ustpy2 | specbtn_mic_ustpy2.tga |
| USA / US_THAAD | Command_ConstructAmericaVehicleTHAAD | us_thaad | specbtn_mic_thaad | specbtn_mic_thaad.tga |
| USA / US_THAAD_Site_AI | Command_ConstructAmericaVehicleTHAAD_AI | us_thaad | specbtn_mic_thaad | specbtn_mic_thaad.tga |
| GLA/Arab / Arab_Krasukha-4 | Command_ConstructArab_Krasukha-4 | arb_krasukha4e | specbtn_mic_krasukha | specbtn_mic_krasukha.tga |
| Arab / Arb_92N6E | Command_ConstructArb_92N6E | irq_92N6E | specbtn_mic_92n6r | specbtn_mic_92n6r.tga |
| Arab / Arb_Pantsir | Command_ConstructArb_Pantsir | arb_pantsirs1 | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |
| China / ChinaVehicleHQ9 | Command_ConstructChinaVehicleHQ9 | pla_hq9b | specbtn_mic_hq9 | specbtn_mic_hq9.tga |
| China / ChinaVehicleHT233 | Command_ConstructChinaVehicleHT233 | pla_ht233 | specbtn_mic_ht233 | specbtn_mic_ht233.tga |
| China / ChinaVehicleKrasukha4 | Command_ConstructChinaVehicleKrasukha4 | rus_krasukha4 | specbtn_mic_krasukha | specbtn_mic_krasukha.tga |
| Iran / IranVehiclePantsirS1M | Command_ConstructIranVehiclePantsirS1M | irn_pantsir | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |
| Israel / Israel_AN_TPY2 | Command_ConstructIsrael_AN_TPY2 | isi_tpy2 | specbtn_mic_tpy2 | specbtn_mic_tpy2.tga |
| Israel / Israel_Arrow | Command_ConstructIsrael_Arrow | isi_arrow | specbtn_mic_arrow | specbtn_mic_arrow.tga |
| Russia / RussiaVehicle92N6R | Command_ConstructRussiaVehicle92N6R | rus_92n6r | specbtn_mic_92n6r | specbtn_mic_92n6r.tga |
| Russia / 92N6E alias → RussiaVehicle92N6R | Command_ConstructRussian_92N6E | rus_92n6r | specbtn_mic_92n6r | specbtn_mic_92n6r.tga |
| Russia / 92N6E AI alias | Command_ConstructRussian_92N6E_AI | rus_92n6r | specbtn_mic_92n6r | specbtn_mic_92n6r.tga |
| Russia / RussiaVehicle96L6TSP | Command_ConstructRussiaVehicle96L6TSP | rus_96l6tsp | specbtn_mic_96l6tsp | specbtn_mic_96l6tsp.tga |
| Russia / RussiaVehicleKrasukha4 | Command_ConstructRussiaVehicleKrasukha4 | rus_krasukha4 | specbtn_mic_krasukha | specbtn_mic_krasukha.tga |
| Russia / Russia_Krasukha-4 | Command_ConstructRussia_Krasukha-4 | rus_krasukha4 | specbtn_mic_krasukha | specbtn_mic_krasukha.tga |
| Russia / RussiaVehiclePantsirS1M | Command_ConstructRussiaVehiclePantsirS1M | rus_pantsirs1m | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |
| Russia / Russia_PantsirS1M | Command_ConstructRussian_PantsirS1M | rus_pantsirs1m | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |
| Russia / RussiaVehicleS400 | Command_ConstructRussiaVehicleS400 | rus_s400r | specbtn_mic_s400 | specbtn_mic_s400.tga |
| Russia / Russia_S400_Real | Command_ConstructRussian_S400 | rus_s400r | specbtn_mic_s400 | specbtn_mic_s400.tga |
| Russia / Russia_S400_AI | Command_ConstructRussian_S400_AI | rus_s400r | specbtn_mic_s400 | specbtn_mic_s400.tga |
| Russia / RussiaVehicleS500 | Command_ConstructRussiaVehicleS500 | rus_s400r (wrong atlas) | specbtn_mic_s500 | specbtn_mic_s500.tga |
| Nato / NatoVehicleIRIST | Command_ConstructNatoVehicleIRIST | Nat_irist | specbtn_mic_irist | specbtn_mic_irist.tga |
| Nato / NatoVehicleTRML4D | Command_ConstructNatoVehicleTRML4D | Nat_trml4d | specbtn_mic_trml4d | specbtn_mic_trml4d.tga |
| EU5 / Specter_EU5_IRIST | Command_ConstructSpecterEU5_IRIST | Nat_irist | specbtn_mic_irist | specbtn_mic_irist.tga |
| EU5 / Specter_EU5_TRML4D | Command_ConstructSpecterEU5_TRML4D | Nat_trml4d | specbtn_mic_trml4d | specbtn_mic_trml4d.tga |
| Britain, France, Germany, Italy, Sweden, Turkey, Ukraine IRIST / TRML4D vehicles | Command_Construct*VehicleIRIST / TRML4D | Nat_irist / Nat_trml4d | specbtn_mic_irist / specbtn_mic_trml4d | matching TGA |
| UAE / UAEVehiclePantsir | Command_ConstructUAEVehiclePantsir | us_m6 | specbtn_mic_pantsir | specbtn_mic_pantsir.tga |

`Command_ConstructRussian_92N6E` still builds `RussiaVehicle92N6R` (92N6E radar-link alias kept).

## What was not changed

- Cost, build time, CommandSet slots, weapons, models, interceptor stats
- Pantsir-S1M / Krasukha-4 gameplay
- 92N6E / HT-233 DataLink + OCL last-wins
- Iraq radar Spy Satellite removal and P30 map fix
- `SelectPortrait` / production-queue identity of other units
- Generic `Button_AirDefense` dozer *sites* (IRISTSamSite, Hq9_Site, …)
- Native country Heron/MQ-4/Shahed *other* objects
- GM shop ButtonImage *names* (already `specbtn_mic_*`)

## Validation (BIG / INI only)

- Each packed TGA is 128×128 uncompressed 32-bit SAGE TGA; 19 distinct SHA-256 hashes
- Decoded `specbtn_mic_s400.tga`, `Button_GlobalMarket.tga`, `specbtn_heron.tga` match the uploaded construct art (upright)
- MappedImage Texture names match packed ART paths (case-insensitive)
- GM building ButtonImage is `Button_GlobalMarket`, not a shop `specbtn_mic_*`
- Shop buttons still `specbtn_mic_*`
- Four-drone CommandSets still the four SpecterRadar construct commands
- `Command_SpySatelliteScan` remains for other buildings

Install: replace both `_SPEC_DATA_ONE.big` and `_SPEC_ART_ONE.big` in the game folder. Loose PNG/DDS/INI is not the install.

Rebuild:

```
python3 patch/tools/big/patch_spec_construct_button_images.py \
  --src-data patch/Release/IRAQ_RADAR_SPY_MAP/_SPEC_DATA_ONE.big \
  --src-art /path/_SPEC_ART_ONE.big \
  --patch-root patch \
  --out-dir patch/Release/CONSTRUCT_BUTTON_IMAGES
```
