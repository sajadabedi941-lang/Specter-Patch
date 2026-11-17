# SPECTER — فهرست اسامی یکتای تجهیزات زمینی

منبع: Release [`complete-equipment-database`](https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/complete-equipment-database) — فایل `SPECTER_COMPLETE_EQUIPMENT_DATABASE.csv`.
SHA-256 منبع: `f56b9eeaba39748c89f3055e38e7475422641f1b7288c6f5a65024dad19e6633`

فقط خواندنی. هیچ فایل DATA / ART / BIG / CommandSet تغییر نکرد. Zero Hour اجرا نشد.

قواعد یکتاسازی (از DATA، بدون حدس نام):

- نسخه‌های CombatMode / PackMode / Deployed / ABM / AI همان Object پایه با آن یکی شده‌اند.
- کلون‌های کشوری وقتی **خانوادهٔ نام داخلی + مدل W3D + دسته** یکی باشد یک ردیف‌اند، حتی اگر CSF عنوان کمی متفاوت بدهد.
- مدل مشترک به‌تنهایی باعث ادغام نشد (مثلاً NASAMS و SkySabre و Khordad روی یک مدل SAM جدا ماندند).
- شباهت اسمی به‌تنهایی باعث حذف نشد.
- تجهیزات خارج از منو و ناقص حذف نشدند؛ وضعیت‌شان ثبت شد.

## تعداد تجهیزات یکتا

| دسته | تعداد یکتا |
|---|---:|
| تانک‌ها | 67 |
| نفربرها و IFVها | 48 |
| خودروهای زرهی | 184 |
| پدافندها | 116 |
| توپخانه | 24 |
| راکت‌اندازها | 23 |
| پرتابگرهای موشک بالستیک و کروز | 296 |
| رادارها و جنگ الکترونیک | 30 |
| خودروهای پشتیبانی | 7 |
| تجهیزات و پرتابگرهای پهپادی | 17 |
| **جمع** | **812** |

## تانک‌ها

تعداد یکتا: **67**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | AFT-10 | `ChinaTankAFT10` | ChinaTankAFT10_AI | China | فعال در منوی ساخت |
| 2 | Al-Khalid | `PakistanTankAlKhalid` | — | Pakistan | خارج از منو |
| 3 | Al-Zarrar | `PakistanTankAlZarrar` | — | Pakistan | خارج از منو |
| 4 | AMX-30B2 | `FranceTankAMX30` | — | France | خارج از منو |
| 5 | Arjun | `IndiaTankArjun` | — | India | خارج از منو |
| 6 | AssadBabel-2 | `Iraq_AssadBabel-2` | IraqTankAssadBabel2_AI, Slth_GLATankMarauder | Iraq, GLAStealthGeneral | فعال در منوی ساخت |
| 7 | C1 Ariete | `ItalyTankArieteC1` | — | Italy | خارج از منو |
| 8 | C2 Ariete | `ItalyTankAriete` | — | Italy | خارج از منو |
| 9 | Challenger 2 | `BritainTankChallenger2` | — | Britain | خارج از منو |
| 10 | Challenger 2 TES | `BritainTankChallenger2TES` | — | Britain | خارج از منو |
| 11 | Dragon Tank | `ChinaTankDragon` | Infa_ChinaTankDragon | China, ChinaInfantryGeneral | فعال در منوی ساخت |
| 12 | Japan_PokpungHo_RussiaTankT90A23 | `Japan_PokpungHo_RussiaTankT90A23` | NorthKorea_PokpungHo_RussiaTankT90A23, SouthKorea_PokpungHo_RussiaTankT90A23, Vietnam_PokpungHo_RussiaTankT90A23 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 13 | K1A2 | `SouthKoreaTankK1A1` | — | SouthKorea | خارج از منو |
| 14 | K2 Black Panther | `SouthKoreaTankK1A2` | — | SouthKorea | خارج از منو |
| 15 | Karrar MBT | `IranTankKarrar` | — | Iran | فعال در منوی ساخت |
| 16 | Leclerc | `FranceTankLeclerc` | — | France | خارج از منو |
| 17 | Leclerc UAE | `UAETankLeclerc` | — | UAE | خارج از منو |
| 18 | Leopard 2A4 | `TurkeyTankLeopard2A4` | — | Turkey | خارج از منو |
| 19 | Leopard 2A6 | `GermanyTankLeopard2A6` | — | Germany | خارج از منو |
| 20 | Leopard 2A7 | `GermanyTankLeopard2A7` | — | Germany | خارج از منو |
| 21 | Leopard 2A7+ | `NatoTankLeopard2A7Plus` | BritainTankLeopard2A7Plus, FranceTankLeopard2A7Plus, GermanyTankLeopard2A7Plus, ItalyTankLeopard2A7Plus, SwedenTankLeopard2A7Plus, TurkeyTankLeopard2A7Plus, UkraineTankLeopard2A7Plus | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 22 | M1A1S Abrams MBT | `EgyptTankM1A1S` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 23 | M1A2 | `AmericaTankCrusader` | — | America | فعال در منوی ساخت |
| 24 | M1A2 | `AmericaTankM1A2_GC` | — | America | خارج از منو |
| 25 | M1A2 | `GLATankMarauder` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 26 | M1A2 Abrams | `SaudiArabiaTankM1A2S` | — | SaudiArabia | خارج از منو |
| 27 | M1A2S Abrams | `SaudiArabiaTankM1A2` | — | SaudiArabia | خارج از منو |
| 28 | M2A3 BUSK III | `AmericaTankMicrowave` | — | America | فعال در منوی ساخت |
| 29 | M60T Sabra | `TurkeyTankM60T` | — | Turkey | خارج از منو |
| 30 | Merkava MK4 | `Israel_MerkavaMk4` | — | Israel | فعال در منوی ساخت |
| 31 | Neptune | `UkraineTankT64BV` | — | Ukraine | خارج از منو |
| 32 | NorthKorea_PokpungHo | `NorthKorea_PokpungHo` | Japan_PokpungHo, SouthKorea_PokpungHo, Vietnam_PokpungHo | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 33 | Olifant Mk1B | `SouthAfricaTankOlifant1B` | — | SouthAfrica | خارج از منو |
| 34 | Olifant Mk2 | `SouthAfricaTankOlifant` | — | SouthAfrica | خارج از منو |
| 35 | RussiaTankT90A23 | `RussiaTankT90A23` | — | Russia | خارج از منو |
| 36 | RussiaTankT90M | `RussiaTankT90M` | — | Russia | خارج از منو |
| 37 | RussiaTankT90SM | `RussiaTankT90SM` | — | Russia | خارج از منو |
| 38 | RussiaTankT90SM1 | `RussiaTankT90SM1` | — | Russia | خارج از منو |
| 39 | Scorpion | `GLALightTank` | — | Arabic Alliance, GLA | خارج از منو |
| 40 | Strv 121 | `SwedenTankStrv121` | — | Sweden | خارج از منو |
| 41 | Strv 122 | `SwedenTankStrv122` | — | Sweden | خارج از منو |
| 42 | Strv 122B+ | `SwedenTankStrv122B` | — | Sweden | خارج از منو |
| 43 | T-54M3 | `VietnamTankT54M3` | — | Vietnam | خارج از منو |
| 44 | T-62 | `LibyaTankT62` | — | Libya | خارج از منو |
| 45 | T-62 | `SyriaTankT62` | — | Syria | خارج از منو |
| 46 | T-72 | `LibyaTankT72` | — | Libya | خارج از منو |
| 47 | T-72 | `SyriaTankT72` | — | Syria | خارج از منو |
| 48 | T-72 Ajeya | `IndiaTankT72Ajeya` | — | India | خارج از منو |
| 49 | T-72A Obr.1982 | `Slth_GLATankScorpion2` | — | GLAStealthGeneral | خارج از منو |
| 50 | T-72A obr.1984 | `Iraq_T-72` | Egypt_T-72, India_T-72, Libya_T-72, Pakistan_T-72, SaudiArabia_T-72, SouthAfrica_T-72, Syria_T-72, UAE_T-72 | Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 51 | T-72AMT | `UkraineTankT72AMT` | — | Ukraine | خارج از منو |
| 52 | T-72B3 Obr.2016 MBT | `RussiaTankT72B16` | — | Russia | خارج از منو |
| 53 | T-72B3 Obr.2016 MBT | `RussiaTankT72B36` | — | Russia | خارج از منو |
| 54 | T-72B3 Obr.2023 MBT | `RussiaTankT72B23` | — | Russia | خارج از منو |
| 55 | T-80BVM Obr.2015 MBT | `RussiaTankT80BVM15` | — | Russia | خارج از منو |
| 56 | T-80BVM Obr.2023 MBT | `RussiaTankT80BVM23` | — | Russia | خارج از منو |
| 57 | T-84 | `UkraineTankT84` | — | Ukraine | خارج از منو |
| 58 | T-90 Bhishma | `IndiaTankT90S` | — | India | خارج از منو |
| 59 | T-90A MBT | `RussiaTankT90A` | — | Russia, China | فعال در منوی ساخت |
| 60 | T-90S | `EgyptTankT90MS` | VietnamTankT90S | Arabic Alliance, GLA, Vietnam | فعال در منوی ساخت |
| 61 | T-90S | `GLATankScorpion` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 62 | T14 Armata MBT | `RussiaTankT14` | — | Russia | فعال در منوی ساخت |
| 63 | Type 10 | `JapanTankType10` | — | Japan | خارج از منو |
| 64 | Type 90 | `JapanTankType90` | — | Japan | خارج از منو |
| 65 | Z3 MBT | `IranTankZ3MBT` | IranTankZ3MBTAi | Iran | فعال در منوی ساخت |
| 66 | ZBD-04 | `ChinaTankZBD04` | ChinaTankZBD04_AI | China | فعال در منوی ساخت |
| 67 | ZTZ99A2 | `ChinaTankBattleMaster` | — | China | فعال در منوی ساخت |

## نفربرها و IFVها

تعداد یکتا: **48**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | Assault Troop Transport | `Infa_ChinaVehicleTroopCrawler` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 2 | BMP-1 | `LibyaVehicleBMP1` | — | Libya | خارج از منو |
| 3 | BMP-1 | `SyriaVehicleBMP1` | — | Syria | خارج از منو |
| 4 | Bmp-1p | `Iraq_BMP-1` | Egypt_BMP-1, India_BMP-1, Libya_BMP-1, Pakistan_BMP-1, SaudiArabia_BMP-1, SouthAfrica_BMP-1, Syria_BMP-1, UAE_BMP-1 | Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 5 | Bmp-1p | `Slth_GLAVehicleCombatBike` | — | GLAStealthGeneral | فعال در منوی ساخت |
| 6 | BMP-2 | `IndiaVehicleBMP2` | — | India | خارج از منو |
| 7 | BMP-2 | `UkraineVehicleBMP2` | — | Ukraine | خارج از منو |
| 8 | BMP-2 | `VietnamVehicleBMP1` | — | Vietnam | خارج از منو |
| 9 | Bmp-2k | `Iraq_BMP-2` | Iraq_Bmp2K | Iraq | فعال در منوی ساخت |
| 10 | BMP-3 | `UAEVehicleBMP3` | — | UAE | خارج از منو |
| 11 | BMP-3 Kornet | `UAEVehicleBMP3AT` | — | UAE | خارج از منو |
| 12 | BMP-3M | `GLAVehicleToxinTruck` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 13 | BMP-3M IFV | `RussiaTankBMP3` | — | Russia | فعال در منوی ساخت |
| 14 | BMP-3M IFV | `RussiaTankBMP3MV` | — | Russia | خارج از منو |
| 15 | BMP1A | `IranVehicleBMP1A` | IranVehicleBMP1A_AI | Iran | فعال در منوی ساخت |
| 16 | BMP2A | `IranVehicleBMP2` | IranVehicleBMP2A_AI | Iran | فعال در منوی ساخت |
| 17 | BTR-4 | `UkraineVehicleBTR4` | — | Ukraine | خارج از منو |
| 18 | BTR-80 | `SyriaVehicleBTR` | — | Syria | خارج از منو |
| 19 | BTR-80 | `VietnamVehicleBTR80` | — | Vietnam | خارج از منو |
| 20 | BTR-82A Motorized Squad | `RussiaVehicleBTR82A` | — | Russia | فعال در منوی ساخت |
| 21 | BTR-90 | `Iraq_BTR-90` | Egypt_BTR-90, India_BTR-90, Libya_BTR-90, Pakistan_BTR-90, SaudiArabia_BTR-90, Slth_GLAVehicleTechnical, SouthAfrica_BTR-90, Syria_BTR-90, UAE_BTR-90 | Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, GlaStealthGeneral, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 22 | BTR60 | `IranVehicleBTR60` | IranVehicleBTR60_AI | Iran | فعال در منوی ساخت |
| 23 | Combat Cycle | `GLAVehicleCombatBike` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 24 | IsraelVehicleEitanAFV | `IsraelVehicleEitanAFV` | — | Israel | فعال در منوی ساخت |
| 25 | K200A1 | `SouthKoreaVehicleK200APC` | — | SouthKorea | خارج از منو |
| 26 | K21 IFV | `SouthKoreaVehicleK21` | — | SouthKorea | خارج از منو |
| 27 | M-1296 | `AmericaVehicleM1296` | — | America | فعال در منوی ساخت |
| 28 | M1126 Stryker | `AmericaVehicleHumvee` | AmericaVehicleM1126 | America | فعال در منوی ساخت |
| 29 | M1128 Stryker SG | `AmericaVehicle_M1128` | — | America | فعال در منوی ساخت |
| 30 | M2 Bradley | `SaudiArabiaVehicleM2` | — | SaudiArabia | خارج از منو |
| 31 | M2A3 | `ArabVehicleM2A3BuskII` | — | Arabic Alliance, GLA | خارج از منو |
| 32 | M2A3 Bradley | `EgyptVehicleYPR765` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 33 | Namer IFV | `AirF_AmericaTankMicrowave` | — | Israel | فعال در منوی ساخت |
| 34 | NorthKorea_M2010APC | `NorthKorea_M2010APC` | Japan_M2010APC, SouthKorea_M2010APC, Vietnam_M2010APC | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 35 | Puma | `GermanyVehiclePuma` | — | Germany | خارج از منو |
| 36 | Puma IFV | `NatoTankPuma` | NatoTankPumaMech, BritainTankPuma, BritainTankPumaMech, FranceTankPuma, FranceTankPumaMech, GermanyTankPuma, GermanyTankPumaMech, ItalyTankPuma, ItalyTankPumaMech, SwedenTankPuma, SwedenTankPumaMech, TurkeyTankPuma, TurkeyTankPumaMech, UkraineTankPuma, UkraineTankPumaMech | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 37 | Saad | `PakistanVehicleTalhaIFV` | — | Pakistan | خارج از منو |
| 38 | T-155 Firtina | `TurkeyVehicleFirtina` | — | Turkey | خارج از منو |
| 39 | T15 Armata IFV | `RussianTankT15` | — | Russia | فعال در منوی ساخت |
| 40 | Talha | `PakistanVehicleTalhaAPC` | — | Pakistan | خارج از منو |
| 41 | Troop Crawler | `ChinaVehicleTroopCrawlerEmpty` | — | China | خارج از منو |
| 42 | Tulpar IFV | `TurkeyVehicleACV15` | — | Turkey | خارج از منو |
| 43 | Type 88 SSM | `JapanVehicleType12Btry` | — | Japan | خارج از منو |
| 44 | Type 89 IFV | `JapanVehicleType89` | — | Japan | خارج از منو |
| 45 | Type 96 WAPC | `JapanVehicleType96` | — | Japan | خارج از منو |
| 46 | VBCI | `FranceVehicleVBCI` | — | France | خارج از منو |
| 47 | VBCI APC | `NatoVehicleVBCI` | Specter_EU5_VBCI, BritainVehicleVBCI, GermanyVehicleVBCI, ItalyVehicleVBCI, SwedenVehicleVBCI, TurkeyVehicleVBCI, UkraineVehicleVBCI | Ukraine, Nato, Britain, Germany, Italy, Sweden, Turkey | فعال در منوی ساخت |
| 48 | Warrior | `BritainVehicleWarrior` | — | Britain | خارج از منو |

## خودروهای زرهی

تعداد یکتا: **184**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | 2S22 Bohdana | `UkraineVehicleBohdana` | — | Ukraine | خارج از منو |
| 2 | 2S3 Akatsiya | `VietnamVehicle2S3` | — | Vietnam | خارج از منو |
| 3 | 2S6 Tunguska | `IndiaVehicleTunguska` | — | India | خارج از منو |
| 4 | 2S6M1 Tunguska | `GLAVehicleQuadCannon` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 5 | 35D6 | `UkraineVehicleP18` | — | Ukraine | خارج از منو |
| 6 | 36D6 | `VietnamVehicle36D6` | — | Vietnam | خارج از منو |
| 7 | 9K-317 Buk-M2 | `RussiaVehicle9K317` | JapanFinal_KN06_RussiaVehicle9K317, NKFinal_KN06_RussiaVehicle9K317, SouthKoreaFinal_KN06_RussiaVehicle9K317, VietnamFinal_KN06_RussiaVehicle9K317 | Russia, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 8 | 9K-317 BukM2 | `EgyptVehicle9K317` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 9 | 9K-317M Buk-M3 | `RussiaVehicle9K317M` | — | Russia | خارج از منو |
| 10 | 9K135 Kornet | `SyriaVehicleKornet` | — | Syria | خارج از منو |
| 11 | 9P122 Malyutka | `LibyaVehicleATGM` | — | Libya | خارج از منو |
| 12 | 9P148 Konkurs | `VietnamVehicleKonkurs` | — | Vietnam | خارج از منو |
| 13 | 9S-19M2 Engagment Radar | `EgyptVehicle9S19M2` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 14 | A-100 | `PakistanVehicleA100` | — | Pakistan | خارج از منو |
| 15 | ACV-15 TOW | `TurkeyVehicleACVTOW` | — | Turkey | خارج از منو |
| 16 | Ajax | `BritainVehicleAjax` | — | Britain | خارج از منو |
| 17 | Akash | `IndiaVehicleAkash` | — | India | خارج از منو |
| 18 | Al-Hadeed | `PakistanVehicleARV` | — | Pakistan | خارج از منو |
| 19 | Al-Haitham | `Iraq_AlHaitham` | — | Iraq | خارج از منو |
| 20 | Altay | `TurkeyVehicleAltay` | — | Turkey | خارج از منو |
| 21 | Ambulance | `AmericaVehicleMedic` | — | America | خارج از منو |
| 22 | AMX-10RC | `FranceVehicleAMX10RC` | — | France | خارج از منو |
| 23 | AN/MPQ-53 | `SaudiArabiaVehicleMPQ53` | — | SaudiArabia | خارج از منو |
| 24 | ArabVehicleJiny | `ArabVehicleJiny` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 25 | Archer | `SwedenVehicleArcher` | — | Sweden | خارج از منو |
| 26 | Ariete ARV | `ItalyVehicleARV` | — | Italy | خارج از منو |
| 27 | AS90 | `BritainVehicleAS90` | — | Britain | خارج از منو |
| 28 | AT-1K Raybolt | `SouthKoreaVehicleK21AT` | — | SouthKorea | خارج از منو |
| 29 | B1 Centauro | `ItalyVehicleCentauro` | — | Italy | خارج از منو |
| 30 | Baktar-Shikan | `PakistanVehicleBaktar` | — | Pakistan | خارج از منو |
| 31 | Battle Bus | `GLAVehicleBattleBus` | — | Arabic Alliance, GLA | خارج از منو |
| 32 | Battleship | `AmericaVehicleBattleShipDemo` | AmericaVehicleBattleShip, AmericaVehicleBattleShipUSSBender | America | خارج از منو |
| 33 | Battleship | `AmericaVehicleBattleShipReal` | — | America | خارج از منو |
| 34 | Bgbv 120 | `SwedenVehicleBgbv120` | — | Sweden | خارج از منو |
| 35 | Bomb Truck | `GLAVehicleBombTruck` | — | Arabic Alliance, GLA | خارج از منو |
| 36 | Bora Missile | `TurkeyVehicleBora` | — | Turkey | خارج از منو |
| 37 | Boxer | `GermanyVehicleBoxer` | — | Germany | خارج از منو |
| 38 | BPz3 Buffel | `GermanyVehicleBuffel` | — | Germany | خارج از منو |
| 39 | BRDM-2 | `SyriaVehicleBRDM` | — | Syria | خارج از منو |
| 40 | BRDM-2 | `UkraineVehicleBRDM` | — | Ukraine | خارج از منو |
| 41 | BRDM-2 | `VietnamVehicleBRDM` | — | Vietnam | خارج از منو |
| 42 | BREM-1 | `LibyaVehicleBREM` | — | Libya | خارج از منو |
| 43 | BREM-1 | `SyriaVehicleBREM` | — | Syria | خارج از منو |
| 44 | BREM-1 | `UkraineVehicleBREM` | — | Ukraine | خارج از منو |
| 45 | BREM-1 | `VietnamVehicleBREM` | — | Vietnam | خارج از منو |
| 46 | Buk-M1 | `UkraineVehicleBuk` | — | Ukraine | خارج از منو |
| 47 | Buk-M2 | `SyriaVehicleBuk` | — | Syria | خارج از منو |
| 48 | Cactus | `SouthAfricaVehicleCactus` | — | SouthAfrica | خارج از منو |
| 49 | Casspir | `SouthAfricaVehicleCasspir` | — | SouthAfrica | خارج از منو |
| 50 | Centauro 105 | `ItalyVehicleCentauroAT` | — | Italy | خارج از منو |
| 51 | Centauro II | `ItalyVehicleCentauro2` | — | Italy | خارج از منو |
| 52 | Combat Cycle | `GLAVehicleCombatBikeTerrorist` | GLAVehicleCombatBikeRocket | Arabic Alliance, GLA | فعال در منوی ساخت |
| 53 | Cortale MK3 | `NatoVehicleCortaleMK3` | BritainVehicleCortaleMK3, FranceVehicleCortaleMK3, GermanyVehicleCortaleMK3, ItalyVehicleCortaleMK3, SwedenVehicleCortaleMK3, TurkeyVehicleCortaleMK3, UkraineVehicleCortaleMK3 | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 54 | CRARRV | `BritainVehicleCRARRV` | — | Britain | خارج از منو |
| 55 | CV90 | `SwedenVehicleCV90` | — | Sweden | خارج از منو |
| 56 | CV90 Recce | `SwedenVehicleCV90R` | — | Sweden | خارج از منو |
| 57 | CV90120 | `SwedenVehicleCV90AT` | — | Sweden | خارج از منو |
| 58 | Dardo | `ItalyVehicleDardo` | — | Italy | خارج از منو |
| 59 | EBRC Jaguar | `FranceVehicleJaguar` | — | France | خارج از منو |
| 60 | EE-9 Cascavel | `LibyaVehicleBRDM` | — | Libya | خارج از منو |
| 61 | Egypt_M1A1 | `Egypt_M1A1` | — | Egypt | خارج از منو |
| 62 | EgyptVehicle9S19M2CombatMode | `EgyptVehicle9S19M2CombatMode` | — | Arabic Alliance, GLA | خارج از منو |
| 63 | EgyptVehicle9S19M2PackMode | `EgyptVehicle9S19M2PackMode` | — | Arabic Alliance, GLA | خارج از منو |
| 64 | Fennek | `GermanyVehicleFennek` | — | Germany | خارج از منو |
| 65 | Freccia | `ItalyVehicleVBM` | — | Italy | خارج از منو |
| 66 | FV102 Striker | `BritainVehicleStriker` | — | Britain | خارج از منو |
| 67 | G6 Rhino | `SouthAfricaVehicleG6` | — | SouthAfrica | خارج از منو |
| 68 | G6 Rhino | `UAEVehicleG6` | — | UAE | خارج از منو |
| 69 | GenericMultiEngageModeObject2 | `GenericMultiEngageModeObject2` | — | Unknown | خارج از منو |
| 70 | Gepard | `GermanyVehicleGepard` | — | Germany | خارج از منو |
| 71 | Gepard | `UkraineVehicleGepard` | — | Ukraine | خارج از منو |
| 72 | Giraffe | `BritainVehicleGiraffe` | — | Britain | خارج از منو |
| 73 | Giraffe AMB | `SwedenVehicleGiraffe` | — | Sweden | خارج از منو |
| 74 | GLAVehicleTechnical_Org | `GLAVehicleTechnical_Org` | — | Arabic Alliance, GLA | خارج از منو |
| 75 | Ground Master 200 | `FranceVehicleGM200` | — | France | خارج از منو |
| 76 | Hisar | `TurkeyVehicleHisar` | — | Turkey | خارج از منو |
| 77 | Hrim-2 | `UkraineVehicleHrim2` | — | Ukraine | خارج از منو |
| 78 | Hwasong-7 TEL | `NorthKorea_Hwasong7` | EgyptVehicleHwasong7, Japan_Hwasong7, SouthKorea_Hwasong7, Vietnam_Hwasong7 | Arabic Alliance, GLA, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 79 | Hyunmoo Missile | `SouthKoreaVehicleHyunmoo` | — | SouthKorea | خارج از منو |
| 80 | Hyunmoo-3 | `SouthKoreaVehicleHyunmoo2B` | — | SouthKorea | خارج از منو |
| 81 | IranLauncherKhordad15_AAM | `IranLauncherKhordad15_AAM` | — | Iran | خارج از منو |
| 82 | IranVehicleHoveyzeh | `IranVehicleHoveyzeh` | — | Iran | فعال در منوی ساخت |
| 83 | IranVehicleMajid | `IranVehicleMajid` | — | Iran | فعال در منوی ساخت |
| 84 | Iraq_S75D_Launcher | `Iraq_S75D_Launcher` | — | Iraq | خارج از منو |
| 85 | IraqVehicleS125_AAM | `IraqVehicleS125_AAM` | — | Iraq | خارج از منو |
| 86 | Japan_Chonma5 | `Japan_Chonma5` | NorthKorea_Chonma5, SouthKorea_Chonma5, Vietnam_Chonma5 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 87 | Japan_KN06 | `Japan_KN06` | NorthKorea_KN06, SouthKorea_KN06, Vietnam_KN06 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 88 | Japan_M1992SPAAG | `Japan_M1992SPAAG` | NorthKorea_M1992SPAAG, SouthKorea_M1992SPAAG, Vietnam_M1992SPAAG | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 89 | Japan_M2020 | `Japan_M2020` | NorthKorea_M2020, SouthKorea_M2020, Vietnam_M2020 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 90 | Japan_Pongae3 | `Japan_Pongae3` | NorthKorea_Pongae3, SouthKorea_Pongae3, Vietnam_Pongae3 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 91 | Japan_Pongae4_RussiaVehicle9K317M | `Japan_Pongae4_RussiaVehicle9K317M` | NorthKorea_Pongae4_RussiaVehicle9K317M, SouthKorea_Pongae4_RussiaVehicle9K317M, Vietnam_Pongae4_RussiaVehicle9K317M | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 92 | Japan_Pongae5 | `Japan_Pongae5` | NorthKorea_Pongae5, SouthKorea_Pongae5, Vietnam_Pongae5 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 93 | Jobaria MLS | `UAEVehicleJobaria` | — | UAE | خارج از منو |
| 94 | K-300P Bastion | `VietnamVehicleBastion` | — | Vietnam | خارج از منو |
| 95 | K239 Chunmoo | `SouthKoreaVehicleChunmoo` | — | SouthKorea | خارج از منو |
| 96 | K288 ARV | `SouthKoreaVehicleK288` | — | SouthKorea | خارج از منو |
| 97 | K30 Biho | `SouthKoreaVehicleK30` | — | SouthKorea | خارج از منو |
| 98 | K806 White Tiger | `SouthKoreaVehicleK200` | — | SouthKorea | خارج از منو |
| 99 | K9 Thunder | `SouthKoreaVehicleK9` | — | SouthKorea | خارج از منو |
| 100 | K9 Vajra | `IndiaVehicleK9Vajra` | — | India | خارج از منو |
| 101 | Kalkan | `TurkeyVehicleKalkan` | — | Turkey | خارج از منو |
| 102 | Kaplan-20 | `TurkeyVehicleKaplan` | — | Turkey | خارج از منو |
| 103 | Kirpi | `TurkeyVehicleKirpi` | — | Turkey | خارج از منو |
| 104 | KM-SAM | `SouthKoreaVehicleCheongung` | — | SouthKorea | خارج از منو |
| 105 | Korkut | `TurkeyVehicleKorkut` | — | Turkey | خارج از منو |
| 106 | LAV-25 | `SaudiArabiaVehicleLAV25` | — | SaudiArabia | خارج از منو |
| 107 | LAV-AT | `SaudiArabiaVehicleLAVAT` | — | SaudiArabia | خارج از منو |
| 108 | Leclerc ARV | `UAEVehicleLeclercARV` | — | UAE | خارج از منو |
| 109 | Leclerc DNG | `FranceVehicleDNG` | — | France | خارج از منو |
| 110 | Lvkv 90 | `SwedenVehicleLvkv90` | — | Sweden | خارج از منو |
| 111 | LY-80 | `PakistanVehicleLY80` | — | Pakistan | خارج از منو |
| 112 | M113 | `LibyaVehicleM113` | — | Libya | خارج از منو |
| 113 | M2A3 BUSK III | `AmericaVehicleM2A3Busk3` | AmericaVehicleM2A3BuskIIIMech2 | America | خارج از منو |
| 114 | M2A3 BUSK III Mechanized | `AmericaVehicleM2A3BuskIIIMech` | — | America | فعال در منوی ساخت |
| 115 | M88 ARV | `SaudiArabiaVehicleM88` | — | SaudiArabia | خارج از منو |
| 116 | M88 ARV | `TurkeyVehicleM88` | — | Turkey | خارج از منو |
| 117 | MARS II | `GermanyVehicleMARS` | — | Germany | خارج از منو |
| 118 | Mastiff | `BritainVehicleMastiff` | — | Britain | خارج از منو |
| 119 | Mistral | `FranceVehicleMistral` | — | France | خارج از منو |
| 120 | Mohafiz | `PakistanVehicleMohafiz` | — | Pakistan | خارج از منو |
| 121 | Nag | `IndiaVehicleNag` | — | India | خارج از منو |
| 122 | NAMICA | `IndiaVehicleNAMICA` | — | India | خارج از منو |
| 123 | Nasr | `PakistanVehicleNasr` | — | Pakistan | خارج از منو |
| 124 | Nimr Ajban | `UAEVehicleNimr` | — | UAE | خارج از منو |
| 125 | Nimr Hafeet | `UAEVehiclePatria` | — | UAE | خارج از منو |
| 126 | NorthKorea_ChonmaHo | `NorthKorea_ChonmaHo` | Japan_ChonmaHo, SouthKorea_ChonmaHo, Vietnam_ChonmaHo | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 127 | NorthKorea_Hwasong15BB | `NorthKorea_Hwasong15BB` | Japan_Hwasong15BB, SouthKorea_Hwasong15BB, Vietnam_Hwasong15BB | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 128 | NorthKorea_Hwasong5 | `NorthKorea_Hwasong5` | Japan_Hwasong5, SouthKorea_Hwasong5, Vietnam_Hwasong5 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 129 | NorthKorea_KN09 | `NorthKorea_KN09` | Japan_KN09, SouthKorea_KN09, Vietnam_KN09 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 130 | NorthKorea_KN23 | `NorthKorea_KN23` | Japan_KN23, SouthKorea_KN23, Vietnam_KN23 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 131 | NorthKorea_M1985 | `NorthKorea_M1985` | Japan_M1985, SouthKorea_M1985, Vietnam_M1985 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 132 | NorthKorea_Pongae2 | `NorthKorea_Pongae2` | Japan_Pongae2, SouthKorea_Pongae2, Vietnam_Pongae2 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 133 | NorthKorea_Pongae4 | `NorthKorea_Pongae4` | Japan_Pongae4, SouthKorea_Pongae4, Vietnam_Pongae4 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 134 | NorthKorea_Songun915 | `NorthKorea_Songun915` | Japan_Songun915, SouthKorea_Songun915, Vietnam_Songun915 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 135 | NorthKorea_VTT323 | `NorthKorea_VTT323` | Japan_VTT323, SouthKorea_VTT323, Vietnam_VTT323 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 136 | Nuke Cannon | `Infa_ChinaVehicleNukeLauncher` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 137 | Olifant ARV | `SouthAfricaVehicleARV` | — | SouthAfrica | خارج از منو |
| 138 | Oshkosh M-ATV | `ArabVehicleM1240A1` | — | America | خارج از منو |
| 139 | P-18 | `SyriaVehicleP18` | — | Syria | خارج از منو |
| 140 | Patgb 203 | `SwedenVehiclePatgb203` | — | Sweden | خارج از منو |
| 141 | Pinaka | `IndiaVehiclePinaka` | — | India | خارج از منو |
| 142 | Prahaar | `IndiaVehiclePrahaar` | — | India | خارج از منو |
| 143 | PzH 2000 | `GermanyVehiclePzH2000` | — | Germany | خارج از منو |
| 144 | PzH 2000 | `ItalyVehiclePzH2000` | — | Italy | خارج از منو |
| 145 | Rabdan | `UAEVehicleRabdan` | — | UAE | خارج از منو |
| 146 | Rajendra | `IndiaVehicleRajendra` | — | India | خارج از منو |
| 147 | RAT-31DL | `ItalyVehicleRAT31` | — | Italy | خارج از منو |
| 148 | RBS-15 | `SwedenVehicleRBS15` | — | Sweden | خارج از منو |
| 149 | Rooikat | `SouthAfricaVehicleRooikat` | — | SouthAfrica | خارج از منو |
| 150 | Rooikat 76 | `SouthAfricaVehicleRooikat76` | — | SouthAfrica | خارج از منو |
| 151 | Safir 105 | `IranVehicleJeep105` | — | Iran | فعال در منوی ساخت |
| 152 | SAMP/T | `FranceVehicleSAMPT` | — | France | خارج از منو |
| 153 | SAMP/T | `ItalyVehicleSAMPT` | — | Italy | خارج از منو |
| 154 | SIDAM 25 | `ItalyVehicleSIDAM` | — | Italy | خارج از منو |
| 155 | Stugna-P | `UkraineVehicleStugna` | — | Ukraine | خارج از منو |
| 156 | Supply Truck | `ChinaVehicleSupplyTruck` | RussiaSupplyTruck_CountryIncome, Infa_ChinaVehicleSupplyTruck | China, Russia, ChinaInfantryGeneral | فعال در منوی ساخت |
| 157 | Supply Truck | `IranVehicleUral375` | — | Iran | فعال در منوی ساخت |
| 158 | T-300 Kasirga | `TurkeyVehicleKasirga` | — | Turkey | خارج از منو |
| 159 | Tata Kestrel | `IndiaVehicleKestrel` | — | India | خارج از منو |
| 160 | Technical | `GLAVehicleTechnical` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 161 | Technical | `GLAVehicleTechnicalChassisOne` | Slth_GLAVehicleTechnicalChassisOne | Arabic Alliance, GLA, GLAStealthGeneral | خارج از منو |
| 162 | Thutlwa | `SouthAfricaVehicleThutlwa` | — | SouthAfrica | خارج از منو |
| 163 | Toophan ATGM Jeep | `IranVehicleJeepToophan` | — | Iran | فعال در منوی ساخت |
| 164 | Trojan AVRE | `BritainVehicleTrojan` | — | Britain | خارج از منو |
| 165 | Tuwaiq-2 | `SaudiArabiaVehicleLAV` | — | SaudiArabia | خارج از منو |
| 166 | Type 03 Chu-SAM | `JapanVehicleChuSAM` | — | Japan | خارج از منو |
| 167 | Type 11 ARV | `JapanVehicleType11ARV` | — | Japan | خارج از منو |
| 168 | Type 12 SSM | `JapanVehicleType12` | — | Japan | خارج از منو |
| 169 | Type 16 MCV | `JapanVehicleType16` | — | Japan | خارج از منو |
| 170 | Type 87 SPAAG | `JapanVehicleType87` | — | Japan | خارج از منو |
| 171 | Type 96 MPMS | `JapanVehicleType16AT` | — | Japan | خارج از منو |
| 172 | Type 99 SPH | `JapanVehicleType99` | — | Japan | خارج از منو |
| 173 | UAE_AlKhalid | `UAE_AlKhalid` | India_AlKhalid, Libya_AlKhalid, Pakistan_AlKhalid, SaudiArabia_AlKhalid, SouthAfrica_AlKhalid, Syria_AlKhalid | India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 174 | Ural-375 | `UAE_Ural375_Supply` | Iraq_Ural375_Supply, Iraq_Ural375_Supply_AI, Egypt_Ural375_Supply, India_Ural375_Supply, Japan_Ural375_Supply, Libya_Ural375_Supply, NorthKorea_Ural375_Supply, Pakistan_Ural375_Supply, SaudiArabia_Ural375_Supply, SouthAfrica_Ural375_Supply, SouthKorea_Ural375_Supply, Syria_Ural375_Supply, Vietnam_Ural375_Supply | Iraq, Arabic Alliance, GLAStealthGeneral, Egypt, India, Japan, Libya, NorthKorea, Pakistan, SaudiArabia, SouthAfrica, SouthKorea, Syria, UAE, Vietnam | فعال در منوی ساخت |
| 175 | VAB HOT | `FranceVehicleVABHOT` | — | France | خارج از منو |
| 176 | Valkiri | `SouthAfricaVehicleValkiri` | — | SouthAfrica | خارج از منو |
| 177 | VBMR Griffon | `FranceVehicleVAB` | — | France | خارج از منو |
| 178 | Wiesel TOW | `GermanyVehicleWieselAT` | — | Germany | خارج از منو |
| 179 | Ystervark | `SouthAfricaVehicleYstervark` | — | SouthAfrica | خارج از منو |
| 180 | ZSU-23 Shilka | `Slth_GLAVehicleQuadCannon` | — | GLAStealthGeneral | فعال در منوی ساخت |
| 181 | ZSU-23 Shilka | `UAE_ZSU-23-4` | Iraq_ZSU-23-4, Egypt_ZSU-23-4, India_ZSU-23-4, Libya_ZSU-23-4, Pakistan_ZSU-23-4, SaudiArabia_ZSU-23-4, SouthAfrica_ZSU-23-4, Syria_ZSU-23-4 | Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 182 | ZSU-23-4 | `LibyaVehicleShilka` | — | Libya | خارج از منو |
| 183 | ZSU-23-4 | `SyriaVehicleShilka` | — | Syria | خارج از منو |
| 184 | ZSU-23-4 | `VietnamVehicleShilka` | — | Vietnam | خارج از منو |

## پدافندها

تعداد یکتا: **116**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | 100mm BDC | `Iraq_100mmCannon_Site` | — | Iraq | خارج از منو |
| 2 | 100mm Cannon | `Iraq_100mmCannon` | — | Iraq | فعال در منوی ساخت |
| 3 | 2K12 Kub | `LibyaVehicleSA6` | — | Libya | خارج از منو |
| 4 | 55K6E S-400 Command Unit | `RussiaVehicle55K6E` | — | Russia, China | فعال در منوی ساخت |
| 5 | 92N6R Mobile Radar | `RussiaVehicle92N6R` | Russia_92N6R_CombatMode, Russia_92N6R, Russia_92N6R_PackMode, Iraq_MIC_92N6R | Russia, Iraq, China, Iran, America, Israel | فعال در منوی ساخت |
| 6 | AirF_AmericaVehicleMedic | `AirF_AmericaVehicleMedic` | — | Israel | فعال در منوی ساخت |
| 7 | AirF_AmericaVehicleSentryDrone | `AirF_AmericaVehicleSentryDrone` | — | Israel | فعال در منوی ساخت |
| 8 | AmericaRadarAN/TPY2 | `AmericaRadarAN/TPY2` | — | America | خارج از منو |
| 9 | AmericaVehicleM1126_M1_Shorad | `AmericaVehicleM1126_M1_Shorad` | — | America | فعال در منوی ساخت |
| 10 | AN/TPY2 | `US_AN_TPY2` | US_AN_TPY2_CombatMode, Iraq_MIC_AN_TPY2, Iraq_MIC_US_AN_TPY2, Israel_AN_TPY2 | America, Iraq, Russia, China, Iran, Israel | فعال در منوی ساخت |
| 11 | ArabVehicleS300PMU2Launcher_AAM | `ArabVehicleS300PMU2Launcher_AAM` | — | Arabic Alliance, GLA | خارج از منو |
| 12 | ArabVehicleS300PMU2Launcher_ABM | `ArabVehicleS300PMU2Launcher_ABM` | — | Arabic Alliance, GLA | خارج از منو |
| 13 | ArabVehicleS300PMU2Launcher_ACM | `ArabVehicleS300PMU2Launcher_ACM` | — | Arabic Alliance, GLA | خارج از منو |
| 14 | Arb_S300PMU2AI_Installation | `Arb_S300PMU2AI_Installation` | — | Arabic Alliance, Iraq, GLA | فعال در منوی ساخت |
| 15 | Arrow AAML | `Israel_Arrow` | Iraq_MIC_Arrow, Israel_Arrow_CombatMode, Israel_Arrow_PackMode | Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 16 | Avenger | `SaudiArabiaVehicleAvenger` | — | SaudiArabia | خارج از منو |
| 17 | Bavar-373 | `IranLauncherBavarAI_ABM` | — | Iran | خارج از منو |
| 18 | Boxer Skyranger | `GermanyVehicleBoxerAA` | — | Germany | خارج از منو |
| 19 | Bunker | `SpecterBuildingFOB` | Specter_CombatTrench | Unknown | خارج از منو |
| 20 | C-RAM Base Defense | `UAE_CRAM` | AmericaPatriotBattery, IsraelBuildingC-RAM, India_CRAM, Japan_CRAM, Libya_CRAM, NorthKorea_CRAM, Pakistan_CRAM, SaudiArabia_CRAM, SouthAfrica_CRAM, SouthKorea_CRAM, Syria_CRAM, Vietnam_CRAM | America, Israel, India, Japan, Libya, NorthKorea, Pakistan, SaudiArabia, SouthAfrica, SouthKorea, Syria, UAE, Vietnam | فعال در منوی ساخت |
| 21 | Centauro-B2 | `NatoVehicleCentauroB2` | BritainVehicleCentauroB2, FranceVehicleCentauroB2, GermanyVehicleCentauroB2, ItalyVehicleCentauroB2, SwedenVehicleCentauroB2, TurkeyVehicleCentauroB2, UkraineVehicleCentauroB2, Specter_EU5_CentauroB2 | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 22 | EgyptVehicleS300VMCombatMode | `EgyptVehicleS300VMCombatMode` | — | Arabic Alliance, GLA | خارج از منو |
| 23 | EgyptVehicleS300VMPackMode | `EgyptVehicleS300VMPackMode` | — | Arabic Alliance, GLA | خارج از منو |
| 24 | Falaq Defense | `IranFalaqTrench` | — | Iran | فعال در منوی ساخت |
| 25 | Fortified Bunker | `Infa_ChinaBunker` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 26 | Gattling Cannon | `ChinaGattlingCannon` | — | China | فعال در منوی ساخت |
| 27 | Gattling Cannon | `Infa_ChinaGattlingCannon` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 28 | Gattling Tank | `ChinaTankGattling` | Infa_ChinaTankGattling | China, ChinaTankGeneral | فعال در منوی ساخت |
| 29 | GJ-11 UAV Command Vehicle | `ChinaVehicleGJ11Launcher` | — | China | فعال در منوی ساخت |
| 30 | HAROP | `IsraelDroneHarop` | — | Israel | فعال در منوی ساخت |
| 31 | HQ-9/P | `PakistanVehicleHQ9P` | — | Pakistan | خارج از منو |
| 32 | HQ9 | `ChinaVehicleHQ9` | ChinaVehicleHQ9_CombatMode, ChinaVehicleHQ9_PackMode, Iraq_MIC_HQ9, JapanFinal_Pongae6ABM_ChinaVehicleHQ9_CombatMode, JapanFinal_Pongae6ABM_ChinaVehicleHQ9_PackMode, NKFinal_Pongae6ABM_ChinaVehicleHQ9_CombatMode, NKFinal_Pongae6ABM_ChinaVehicleHQ9_PackMode, SouthKoreaFinal_Pongae6ABM_ChinaVehicleHQ9_CombatMode, SouthKoreaFinal_Pongae6ABM_ChinaVehicleHQ9_PackMode, VietnamFinal_Pongae6ABM_ChinaVehicleHQ9_CombatMode, VietnamFinal_Pongae6ABM_ChinaVehicleHQ9_PackMode | China, Iraq, Russia, Iran, America, Israel, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 33 | HQ9 | `ChinaVehicleHq9_AAM_AI` | ChinaVehicleHq9_ABM_AI | China | خارج از منو |
| 34 | HT-233 Radar | `ChinaVehicleHT233` | ChinaVehicleHT233_CombatMode, ChinaVehicleHT233_PackMode, Iraq_MIC_HT233 | China, Iraq, Russia, Iran, America, Israel | فعال در منوی ساخت |
| 35 | InfantryDefenceTrench1 | `InfantryDefenceTrench1` | — | Unknown | خارج از منو |
| 36 | InfantryDefenceTrench2 | `InfantryDefenceTrench2` | — | Unknown | خارج از منو |
| 37 | InfantryDefenceTrenchF12 | `InfantryDefenceTrenchF12` | — | Unknown | خارج از منو |
| 38 | IranLauncherKhordad15_ABM | `IranLauncherKhordad15_ABM` | — | Iran | خارج از منو |
| 39 | IranVehicleDezfulPenetrator | `IranVehicleDezfulPenetrator` | — | Iran | فعال در منوی ساخت |
| 40 | IranVehicleZolfagharM | `IranVehicleZolfagharM` | — | Iran | فعال در منوی ساخت |
| 41 | Iraq_DefenseSite | `Iraq_DefenseSite` | Japan_DefenseSite, NorthKorea_DefenseSite, SouthKorea_DefenseSite, Vietnam_DefenseSite | Iraq, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 42 | Iraq_ZPU4 | `Iraq_ZPU4` | — | Iraq | خارج از منو |
| 43 | IraqFahad3Launcher_ABM_AI | `IraqFahad3Launcher_ABM_AI` | — | Iraq | خارج از منو |
| 44 | IraqVehicleFahad250_ABM | `IraqVehicleFahad250_ABM` | — | Iraq | خارج از منو |
| 45 | IRIS-T | `GermanyVehicleIRIST` | GermanyVehicleIRIST_CombatMode, GermanyVehicleIRIST_PackMode | Germany | خارج از منو |
| 46 | IRIS-T SAM Site | `NatoIRISTSamSite` | EgyptIRISTSamSite, BritainIRISTSamSite, FranceIRISTSamSite, GermanyIRISTSamSite, ItalyIRISTSamSite, SwedenIRISTSamSite, TurkeyIRISTSamSite, UkraineIRISTSamSite | Arabic Alliance, GLA, Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 47 | IRIS-T SLS | `SwedenVehicleIRIST` | SwedenVehicleIRIST_CombatMode, SwedenVehicleIRIST_PackMode | Sweden | خارج از منو |
| 48 | IRIS-T SLX | `NatoVehicleIRIST` | NatoVehicleIRIST_CombatMode, NatoVehicleIRIST_PackMode, BritainVehicleIRIST, BritainVehicleIRIST_CombatMode, BritainVehicleIRIST_PackMode, FranceVehicleIRIST, FranceVehicleIRIST_CombatMode, FranceVehicleIRIST_PackMode, ItalyVehicleIRIST, ItalyVehicleIRIST_CombatMode, ItalyVehicleIRIST_PackMode, Specter_EU5_IRIST, TurkeyVehicleIRIST, TurkeyVehicleIRIST_CombatMode, TurkeyVehicleIRIST_PackMode, UkraineVehicleIRIST, UkraineVehicleIRIST_CombatMode, UkraineVehicleIRIST_PackMode, Iraq_MIC_IRIST | Nato, Britain, France, Italy, Ukraine, Turkey, Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 49 | Irondome | `ISI_IroneDome` | ISI_IroneDome_ABM | Israel | خارج از منو |
| 50 | Israel_AD_Barak8 | `Israel_AD_Barak8` | — | Israel | ناقص |
| 51 | Israel_AD_IronDome | `Israel_AD_IronDome` | — | Israel | خارج از منو |
| 52 | IsraelTPY2CombatMode | `IsraelTPY2CombatMode` | — | Israel | خارج از منو |
| 53 | Japan_Hq9_Site | `Japan_Hq9_Site` | China_Hq9_Site, NorthKorea_Hq9_Site, SouthKorea_Hq9_Site, Vietnam_Hq9_Site | China, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 54 | Japan_Pongae2_RussiaTankTorM2MV | `Japan_Pongae2_RussiaTankTorM2MV` | NorthKorea_Pongae2_RussiaTankTorM2MV, SouthKorea_Pongae2_RussiaTankTorM2MV, Vietnam_Pongae2_RussiaTankTorM2MV | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 55 | Japan_Pongae6ABM | `Japan_Pongae6ABM` | NorthKorea_Pongae6ABM, SouthKorea_Pongae6ABM, Vietnam_Pongae6ABM | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 56 | Kashtan Base Defense | `RussiaKashtan` | — | Russia | فعال در منوی ساخت |
| 57 | Khordad-15 SAM Site | `IranKhordad15SamSite` | — | Iran | فعال در منوی ساخت |
| 58 | M1120 Thaad | `US_THAAD` | US_THAAD_CombatMode, US_THAAD_PackMode, Iraq_MIC_THAAD | America, Iraq, Russia, China, Iran, Israel | فعال در منوی ساخت |
| 59 | M6A1 LineBacker | `AmericaTankAvenger` | — | America | فعال در منوی ساخت |
| 60 | M6A1 LineBacker | `AmericaVehicleM6A1` | — | America | خارج از منو |
| 61 | Mantis | `NatoMantis` | BritainMantis, FranceMantis, GermanyMantis, ItalyMantis, SwedenMantis, TurkeyMantis, UkraineMantis | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 62 | MIM104E | `ArabVehicleMIM104ELauncher_AAM` | ArabVehicleMIM104ELauncher_ABM | Arabic Alliance, GLA | خارج از منو |
| 63 | MIM104F Patriot | `AmericaMobileSamSiteMIM104F` | — | America | خارج از منو |
| 64 | MIM104F Patriot | `America_MIM104F` | — | America | فعال در منوی ساخت |
| 65 | MIM104F Patriot | `America_MIM104F_Launcher` | America_MIM104F_ABM_Launcher | America | خارج از منو |
| 66 | Namer AA | `AirF_AmericaTankAvenger` | — | Israel | فعال در منوی ساخت |
| 67 | NatoNASAMSIII | `NatoNASAMSIII` | BritainNASAMSIII, FranceNASAMSIII, GermanyNASAMSIII, ItalyNASAMSIII, SwedenNASAMSIII, TurkeyNASAMSIII, UkraineNASAMSIII | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 68 | NatoSAMPTNG | `NatoSAMPTNG` | BritainSAMPTNG, FranceSAMPTNG, GermanySAMPTNG, ItalySAMPTNG, SwedenSAMPTNG, TurkeySAMPTNG, UkraineSAMPTNG | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | خارج از منو |
| 69 | NatoSkyranger30 | `NatoSkyranger30` | BritainSkyranger30, FranceSkyranger30, GermanySkyranger30, ItalySkyranger30, SwedenSkyranger30, TurkeySkyranger30, UkraineSkyranger30 | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 70 | NatoSkySabre | `NatoSkySabre` | BritainSkySabre, FranceSkySabre, GermanySkySabre, ItalySkySabre, SwedenSkySabre, TurkeySkySabre, UkraineSkySabre | Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 71 | NatoVehicleIRIST_SLM_Launcher | `NatoVehicleIRIST_SLM_Launcher` | EgyptVehicleIRIST_SLM_Launcher, EgyptVehicleIRIST_SLM_Launcher_ABM, NatoVehicleIRIST_SLM_Launcher_ABM, BritainVehicleIRIST_SLM_Launcher, BritainVehicleIRIST_SLM_Launcher_ABM, FranceVehicleIRIST_SLM_Launcher, FranceVehicleIRIST_SLM_Launcher_ABM, GermanyVehicleIRIST_SLM_Launcher, GermanyVehicleIRIST_SLM_Launcher_ABM, ItalyVehicleIRIST_SLM_Launcher, ItalyVehicleIRIST_SLM_Launcher_ABM, SwedenVehicleIRIST_SLM_Launcher, SwedenVehicleIRIST_SLM_Launcher_ABM, TurkeyVehicleIRIST_SLM_Launcher, TurkeyVehicleIRIST_SLM_Launcher_ABM, UkraineVehicleIRIST_SLM_Launcher, UkraineVehicleIRIST_SLM_Launcher_ABM | Arabic Alliance, GLA, Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | خارج از منو |
| 72 | Oshkosh M-ATV | `AmericaVehicleSentryDrone` | AirF_AmericaVehicleHumvee, AmericaVehicleM-ATV_AI | Israel, America | فعال در منوی ساخت |
| 73 | Pantsir S1 | `Arb_Pantsir` | UAEVehiclePantsir | Arabic Alliance, GLA, UAE | فعال در منوی ساخت |
| 74 | Pantsir S1M | `IranVehiclePantsirS1M` | — | Iran | فعال در منوی ساخت |
| 75 | Pantsir-S2 SPAAAG | `RussiaVehiclePantsirS1M` | Iraq_MIC_PantsirS1M | Russia, Iraq | فعال در منوی ساخت |
| 76 | Patriot Missile System | `AirF_AmericaPatriotBattery` | — | Israel | فعال در منوی ساخت |
| 77 | Patriot PAC-3 | `SaudiArabiaVehiclePatriot` | — | SaudiArabia | خارج از منو |
| 78 | Patriot PAC-3 | `UAEVehiclePatriot` | — | UAE | خارج از منو |
| 79 | PGZ-04 SPAAAG | `ChinaTankPGZ04` | — | China | فعال در منوی ساخت |
| 80 | Raptor | `SouthAfrica_Raptor` | — | SouthAfrica | فعال در منوی ساخت |
| 81 | Roland-3K | `IraqVehicleRoland3K` | Egypt_VehicleRoland3K, India_VehicleRoland3K, Libya_VehicleRoland3K, Pakistan_VehicleRoland3K, SaudiArabia_VehicleRoland3K, SouthAfrica_VehicleRoland3K, Syria_VehicleRoland3K, UAE_VehicleRoland3K | Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 82 | RussiaS400Deployed | `RussiaS400Deployed` | RussiaS400Deployed_ABM | Russia | خارج از منو |
| 83 | RussiaVehicleS400_AAM_AI | `RussiaVehicleS400_AAM_AI` | — | Russia | خارج از منو |
| 84 | S-300PMU1 | `VietnamVehicleS300` | — | Vietnam | خارج از منو |
| 85 | S-300VM TEL | `EgyptVehicleS300VM` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 86 | S-400 SAM Site | `RussiaS400Site_AI` | — | Russia | فعال در منوی ساخت |
| 87 | S-500 TEL | `RussiaVehicleS500` | Iraq_MIC_S500, RussiaVehicleS500CombatMode, RussiaVehicleS500PackMode | Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 88 | S300 PMU2 | `Arabic_S300PMU2` | Arabic_S300PMU2_CombatMode, Arabic_S300PMU2_PackMode, Iraq_MIC_S300 | Arabic Alliance, GLA, Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 89 | S400R | `RussiaVehicleS400` | Iraq_MIC_S400, RussiaVehicleS400_ABM_AI | Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 90 | S400R | `Russia_S400_ABM_PackMode` | Russia_S400_ABM_CombatMode, Russia_S400_CombatMode, Russia_S400_PackMode | Russia | خارج از منو |
| 91 | SA-6 Gainfull | `Iraq_SA-6` | — | Iraq | فعال در منوی ساخت |
| 92 | SA-6 Gainfull | `Slth_GLAVehicleToxinTruck` | — | GLAStealthGeneral | فعال در منوی ساخت |
| 93 | Sam-8 OSA | `Iraq_Sam8` | Slth_GLAVehicleBattleBus | Iraq, GlaStealthGeneral | فعال در منوی ساخت |
| 94 | Sky Sabre | `BritainVehicleSkySabre` | — | Britain | خارج از منو |
| 95 | Speaker Tower | `Infa_ChinaSpeakerTower` | ChinaSpeakerTower | China, ChinaInfantryGeneral | فعال در منوی ساخت |
| 96 | stationary Sa-2 site | `UAE_Sam2` | Iraq_Sam2, Egypt_Sam2, India_Sam2, Japan_Sam2, Libya_Sam2, NorthKorea_Sam2, Pakistan_Sam2, SaudiArabia_Sam2, SouthAfrica_Sam2, SouthKorea_Sam2, Syria_Sam2, Vietnam_Sam2 | Iraq, Egypt, India, Japan, Libya, NorthKorea, Pakistan, SaudiArabia, SouthAfrica, SouthKorea, Syria, UAE, Vietnam | فعال در منوی ساخت |
| 97 | Stinger Site | `GLAStingerSite` | — | Arabic Alliance, Iraq, GLA | فعال در منوی ساخت |
| 98 | Stinger Site | `GLAStingerSiteNoHole` | — | Arabic Alliance, GLA | خارج از منو |
| 99 | Stormer HVM | `BritainVehicleStormer` | — | Britain | خارج از منو |
| 100 | THAAD | `SaudiArabiaVehiclePatriotBtry` | — | SaudiArabia | خارج از منو |
| 101 | THAAD | `US_M1120AI_Launcher` | US_M1120AI_Launcher_ABM | America | خارج از منو |
| 102 | Tor-M2 | `ChinaTankTorM2` | — | China | فعال در منوی ساخت |
| 103 | Tor-M2M | `RussiaTankTorM2M` | — | Russia | فعال در منوی ساخت |
| 104 | Tor-M2M | `RussiaTankTorM2MV` | JapanFinal_Pongae5_RussiaTankTorM2MV, NKFinal_Pongae5_RussiaTankTorM2MV, SouthKoreaFinal_Pongae5_RussiaTankTorM2MV, VietnamFinal_Pongae5_RussiaTankTorM2MV | Russia, Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 105 | Tor1M | `Arab_Tor1M` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 106 | Tor1M | `IranTankTor1M` | — | Iran | فعال در منوی ساخت |
| 107 | Tunnel Network | `GLASneakAttackTunnelNetwork` | Slth_GLASneakAttackTunnelNetwork | Arabic Alliance, GLA, GLAStealthGeneral | فعال در منوی ساخت |
| 108 | Tunnel Network | `GLASneakAttackTunnelNetworkStart` | — | Arabic Alliance, GLA | خارج از منو |
| 109 | Tunnel Network | `GLATunnelNetwork` | — | Arabic Alliance, Iraq, GLA | فعال در منوی ساخت |
| 110 | Tunnel Network | `GLATunnelNetworkNoSpawn` | — | Arabic Alliance, GLA | خارج از منو |
| 111 | Tunnel Network | `Slth_GLATunnelNetwork` | — | Iraq | فعال در منوی ساخت |
| 112 | UAE_AD_AntiDrone | `UAE_AD_AntiDrone` | India_AD_AntiDrone, Libya_AD_AntiDrone, Pakistan_AD_AntiDrone, SaudiArabia_AD_AntiDrone, SouthAfrica_AD_AntiDrone, Syria_AD_AntiDrone | India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 113 | UAE_AD_MD | `UAE_AD_MD` | Egypt_AD_MD, India_AD_MD, Libya_AD_MD, Pakistan_AD_MD, SaudiArabia_AD_MD, SouthAfrica_AD_MD, Syria_AD_MD | Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 114 | UAE_AD_SAM | `UAE_AD_SAM` | Egypt_AD_SAM, India_AD_SAM, Libya_AD_SAM, Pakistan_AD_SAM, SaudiArabia_AD_SAM, SouthAfrica_AD_SAM, Syria_AD_SAM | Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 115 | UAE_AD_SHORAD | `UAE_AD_SHORAD` | Egypt_AD_SHORAD, India_AD_SHORAD, Libya_AD_SHORAD, Pakistan_AD_SHORAD, SaudiArabia_AD_SHORAD, SouthAfrica_AD_SHORAD, Syria_AD_SHORAD | Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 116 | US_THAAD_Site_AI | `US_THAAD_Site_AI` | — | America, Israel | فعال در منوی ساخت |

## توپخانه

تعداد یکتا: **24**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | 2A-65 152mm Artillary Position | `Russia2A65Site` | — | Russia | فعال در منوی ساخت |
| 2 | 2S-33SM2 MSTA-S 152mm SPG | `RussiaArtillery2S19M2` | — | Russia | فعال در منوی ساخت |
| 3 | 2S-7M Malka 203mm SPG | `RussiaArtillery2S7M` | — | Russia, China | فعال در منوی ساخت |
| 4 | 2S1 Gvozdika | `LibyaVehicle2S1` | — | Libya | خارج از منو |
| 5 | 2S1 Gvozdika | `SyriaVehicle2S1` | — | Syria | خارج از منو |
| 6 | 2S1 SPG | `Iraq_2S1` | Slth_GLAVehicleBombTruck | Iraq, GLAStealthGeneral | فعال در منوی ساخت |
| 7 | Al-Raad | `Iraq_AlAbbas` | — | Iraq | فعال در منوی ساخت |
| 8 | AmericaTankM109A7 | `AmericaTankM109A7` | — | America | فعال در منوی ساخت |
| 9 | Bunker | `ChinaBunker` | — | China | فعال در منوی ساخت |
| 10 | Caesar | `FranceVehicleCaesar` | — | France | خارج از منو |
| 11 | Caesar | `NatoVehicleCaesar` | BritainVehicleCaesar, GermanyVehicleCaesar, ItalyVehicleCaesar, Specter_EU5_Caesar, SwedenVehicleCaesar, TurkeyVehicleCaesar, UkraineVehicleCaesar | Nato, Britain, Germany, Italy, Ukraine, Sweden, Turkey | فعال در منوی ساخت |
| 12 | D-30 122mm Howitzer | `ArabicArmy_D30` | — | Arabic Alliance, Iraq, GLA | فعال در منوی ساخت |
| 13 | D-30 122mm Howitzer | `IranD30Post` | Iraq_D30_Howitzer, Japan_D30_Howitzer, NorthKorea_D30_Howitzer, SouthKorea_D30_Howitzer, Vietnam_D30_Howitzer | Iran, Iraq, Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 14 | IranVehicleRaadBaran | `IranVehicleRaadBaran` | — | Iran | فعال در منوی ساخت |
| 15 | M-109A7 155mm Artillary | `AmericaTankPaladin` | — | America | فعال در منوی ساخت |
| 16 | M109A2 | `PakistanVehicleM109` | — | Pakistan | خارج از منو |
| 17 | M109A6 Paladin | `Israel_M109A6` | — | Israel | فعال در منوی ساخت |
| 18 | M109A6 Paladin | `SaudiArabiaVehicleM109` | — | SaudiArabia | خارج از منو |
| 19 | M777 Base Defense | `NatoM777` | AmericaFireBase, AirF_AmericaFireBase, BritainM777, FranceM777, GermanyM777, India_FireBase, ItalyM777, Libya_FireBase, Pakistan_FireBase, SaudiArabia_FireBase, SouthAfrica_FireBase, SwedenM777, Syria_FireBase, TurkeyM777, UAE_FireBase, UkraineM777 | America, Israel, Nato, Britain, France, Germany, India, Italy, Libya, Pakistan, SaudiArabia, SouthAfrica, Sweden, Syria, Turkey, UAE, Ukraine | فعال در منوی ساخت |
| 20 | PLZ-05 152mm SPG | `ChinaVehiclePLZ05` | — | China | فعال در منوی ساخت |
| 21 | Ra'ad | `Pakistan_Raad` | — | Pakistan | فعال در منوی ساخت |
| 22 | Raad M2EK | `IranRaadM2EK` | — | Iran | فعال در منوی ساخت |
| 23 | Raad SPG | `IranVehicleRaadSPG` | — | Iran | فعال در منوی ساخت |
| 24 | Rocket Buggy | `GLAVehicleRocketBuggy` | — | Arabic Alliance, GLA | فعال در منوی ساخت |

## راکت‌اندازها

تعداد یکتا: **23**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | BM-21 Grad | `Iraq_BM-21` | IranVehicleBM21, Egypt_BM-21, India_BM-21, Libya_BM-21, Pakistan_BM-21, SaudiArabia_BM-21, Slth_GLAVehicleRocketBuggy, SouthAfrica_BM-21, Syria_BM-21, UAE_BM-21 | Iran, Iraq, Egypt, India, Libya, Pakistan, SaudiArabia, GLAStealthGeneral, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 2 | BM-21 Grad | `LibyaVehicleBM21` | — | Libya | خارج از منو |
| 3 | BM-21 Grad | `SyriaVehicleBM21` | — | Syria | خارج از منو |
| 4 | BM-21 Grad | `VietnamVehicleBM21` | — | Vietnam | خارج از منو |
| 5 | BM30 Smerch | `ArabicArmy_Bm30` | — | Arabic Alliance, GLA | فعال در منوی ساخت |
| 6 | BM30 Smerch | `RussiaVehicleBm30` | RussiaVehicleBm30_Deployed | Russia | فعال در منوی ساخت |
| 7 | HIMARS | `SaudiArabiaVehicleASTROS` | — | SaudiArabia | خارج از منو |
| 8 | HIMARS | `UAEVehicleHIMARS` | — | UAE | خارج از منو |
| 9 | HIMARS | `UkraineVehicleHIMARS` | — | Ukraine | خارج از منو |
| 10 | Inferno Cannon | `Infa_ChinaVehicleInfernoCannon` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 11 | IsraelArtillaryPulsPredatorHawk | `IsraelArtillaryPulsPredatorHawk` | — | Israel | خارج از منو |
| 12 | Japan_KN09_ChinaVehiclePHL03_CLS | `Japan_KN09_ChinaVehiclePHL03_CLS` | NorthKorea_KN09_ChinaVehiclePHL03_CLS, SouthKorea_KN09_ChinaVehiclePHL03_CLS, Vietnam_KN09_ChinaVehiclePHL03_CLS | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 13 | M-142 HIMARS | `AmericaVehicleM142` | — | America | فعال در منوی ساخت |
| 14 | M-142 HIMARS | `NatoVehicleM142` | BritainVehicleM142, FranceVehicleM142, GermanyVehicleM142, ItalyVehicleM142, Specter_EU5_M142, SwedenVehicleM142, TurkeyVehicleM142, UkraineVehicleM142 | Nato, Britain, France, Germany, Italy, Ukraine, Sweden, Turkey | فعال در منوی ساخت |
| 15 | M270 | `FranceVehicleLRU` | — | France | خارج از منو |
| 16 | M270 GMLRS | `BritainVehicleGMLRS` | — | Britain | خارج از منو |
| 17 | M270 MLRS | `EgyptVehicleM270` | — | America, Arabic Alliance | فعال در منوی ساخت |
| 18 | M270 MLRS | `ItalyVehicleM270` | — | Italy | خارج از منو |
| 19 | M270 MLRS | `JapanVehicleM270` | — | Japan | خارج از منو |
| 20 | PHL-03 MLRS | `ChinaVehiclePHL03` | ChinaVehiclePHL03_CLS | China | فعال در منوی ساخت |
| 21 | PULS | `SwedenVehiclePULS` | — | Sweden | خارج از منو |
| 22 | TOS-1A | `SyriaVehicleTOS1A` | — | Syria | خارج از منو |
| 23 | Tos1A Buratino | `RussiaTankTos1A` | — | Russia | فعال در منوی ساخت |

## پرتابگرهای موشک بالستیک و کروز

تعداد یکتا: **296**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | 9K52 Luna-M | `LibyaVehicleScudBtry` | — | Libya | خارج از منو |
| 2 | 9P117 | `Iraq_R11ScudB` | — | Iraq | فعال در منوی ساخت |
| 3 | Ababeel | `Pakistan_AbabeelMRV` | — | Pakistan | فعال در منوی ساخت |
| 4 | Abdali | `Pakistan_Abdali` | — | Pakistan | فعال در منوی ساخت |
| 5 | Adler | `Germany_Adler` | — | Germany | فعال در منوی ساخت |
| 6 | Agni-I | `India_Agni1` | — | India | فعال در منوی ساخت |
| 7 | Agni-III | `India_Agni3` | — | India | فعال در منوی ساخت |
| 8 | Agni-P | `India_AgniP` | — | India | فعال در منوی ساخت |
| 9 | Agni-V | `India_Agni5` | — | India | فعال در منوی ساخت |
| 10 | AirF_AmericaVehicleTomahawk | `AirF_AmericaVehicleTomahawk` | — | Israel | فعال در منوی ساخت |
| 11 | Akhdar | `Libya_Akhdar` | — | Libya | فعال در منوی ساخت |
| 12 | Al Ain | `UAE_AlAin` | — | UAE | فعال در منوی ساخت |
| 13 | Al Watan | `UAE_AlWatan` | — | UAE | فعال در منوی ساخت |
| 14 | Al-Abbas | `Iraq_Alhussaien` | IraqVehicleAlabbasLauncher, Iraq_Alhussaien_AI | Iraq | فعال در منوی ساخت |
| 15 | Al-Abbas | `UAE_Alhussaien` | Egypt_Alhussaien, India_Alhussaien, Libya_Alhussaien, Pakistan_Alhussaien, SaudiArabia_Alhussaien, SouthAfrica_Alhussaien, Syria_Alhussaien | Egypt, India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 16 | Al-Basrah | `Iraq_AlBasrah` | — | Iraq | فعال در منوی ساخت |
| 17 | Al-Fahd500 | `Iraq_AlFahd500` | — | Iraq | فعال در منوی ساخت |
| 18 | Al-Hussein II | `Iraq_AlHusseinII` | — | Iraq | فعال در منوی ساخت |
| 19 | Al-Mansour | `Iraq_AlMansour` | — | Iraq | فعال در منوی ساخت |
| 20 | Al-Najm | `Iraq_AlNajm` | — | Iraq | فعال در منوی ساخت |
| 21 | Al-Nasir | `Iraq_AlNasir` | — | Iraq | فعال در منوی ساخت |
| 22 | Al-Samoud II | `Iraq_AlSamoudII` | — | Iraq | فعال در منوی ساخت |
| 23 | Al-Wa'd | `SaudiArabia_AlWad` | — | SaudiArabia | فعال در منوی ساخت |
| 24 | Albatros | `Spain_Albatros` | — | Spain, Nato | فعال در منوی ساخت |
| 25 | ALCM | `America_ALCM` | — | America | فعال در منوی ساخت |
| 26 | Anadolu | `Turkey_Anadolu` | — | Turkey | فعال در منوی ساخت |
| 27 | Aquila | `Italy_Aquila` | — | Italy | فعال در منوی ساخت |
| 28 | Armada | `Spain_Armada` | — | Spain, Nato | فعال در منوی ساخت |
| 29 | ASMPA | `France_ASMPA` | — | France | فعال در منوی ساخت |
| 30 | ATACMS | `America_ATACMS` | — | America | فعال در منوی ساخت |
| 31 | ATACMS | `SaudiArabiaVehicleATACMS` | — | SaudiArabia | خارج از منو |
| 32 | ATACMS | `UAEVehicleThunder` | — | UAE | خارج از منو |
| 33 | Atmaca | `Turkey_Atmaca` | — | Turkey | فعال در منوی ساخت |
| 34 | Aurora | `Sweden_Aurora` | — | Sweden | فعال در منوی ساخت |
| 35 | Babur | `Pakistan_Babur` | — | Pakistan | فعال در منوی ساخت |
| 36 | Baekho | `SouthKorea_Baekho` | — | SouthKorea | فعال در منوی ساخت |
| 37 | Barada | `Syria_Barada` | — | Syria | فعال در منوی ساخت |
| 38 | Barq | `SaudiArabia_Barq` | — | SaudiArabia | فعال در منوی ساخت |
| 39 | Barq | `UAE_Barq` | — | UAE | فعال در منوی ساخت |
| 40 | Bateleur | `SouthAfricaVehicleBateleur` | — | SouthAfrica | خارج از منو |
| 41 | Bavar-373 | `IranBavarSiteAI` | — | Iran | خارج از منو |
| 42 | Bavar-373 | `IranLauncherBavarAI_AAM` | — | Iran | خارج از منو |
| 43 | Bavar-373 | `Iran_Bavar` | Iran_Bavar_CombatMode, Iran_Bavar_PackMode | Iran | فعال در منوی ساخت |
| 44 | Berserk | `Sweden_Berserk` | — | Sweden | فعال در منوی ساخت |
| 45 | Blackbuck | `Britain_Blackbuck` | — | Britain | فعال در منوی ساخت |
| 46 | Bozkurt | `Turkey_Bozkurt` | — | Turkey | فعال در منوی ساخت |
| 47 | BrahMos | `India_BrahMos` | — | India | فعال در منوی ساخت |
| 48 | Bulava | `Russia_Bulava` | — | Russia | فعال در منوی ساخت |
| 49 | Buraq | `UAE_Buraq` | — | UAE | فعال در منوی ساخت |
| 50 | Bạch Đằng | `Vietnam_BachDang` | — | Vietnam | فعال در منوی ساخت |
| 51 | Castilla | `Spain_Castilla` | — | Spain, Nato | فعال در منوی ساخت |
| 52 | Cenk | `Turkey_Cenk` | — | Turkey | فعال در منوی ساخت |
| 53 | Cheonma | `SouthKorea_Cheonma` | — | SouthKorea | فعال در منوی ساخت |
| 54 | Cheonwang | `SouthKorea_Cheonwang` | — | SouthKorea | فعال در منوی ساخت |
| 55 | Cid | `Spain_Cid` | — | Spain, Nato | فعال در منوی ساخت |
| 56 | CJ10 | `China_CJ10` | — | China | فعال در منوی ساخت |
| 57 | Cửu Long | `Vietnam_CuuLong` | — | Vietnam | فعال در منوی ساخت |
| 58 | D5 | `America_D5` | — | America | فعال در منوی ساخت |
| 59 | Delilah | `Israel_Delilah` | — | Israel | فعال در منوی ساخت |
| 60 | Dezful | `Iran_Dezful` | — | Iran | فعال در منوی ساخت |
| 61 | DF-12 | `ChinaVehicleDF12` | — | China | فعال در منوی ساخت |
| 62 | DF-17 | `ChinaVehicleDF17` | — | China | فعال در منوی ساخت |
| 63 | DF-21C | `ChinaVehicleDF21C` | — | China | فعال در منوی ساخت |
| 64 | DF-41 Mobile ICBM Launcher | `Factory_DF41Once` | ChinaVehicleDF41, ChinaVehicleDF41_AI | China, Iraq | فعال در منوی ساخت |
| 65 | DF15 | `China_DF15` | — | China | فعال در منوی ساخت |
| 66 | DF16 | `China_DF16` | — | China | فعال در منوی ساخت |
| 67 | DF26 | `China_DF26` | — | China | فعال در منوی ساخت |
| 68 | DF31 | `China_DF31` | — | China | فعال در منوی ساخت |
| 69 | DF5B | `China_DF5B` | — | China | فعال در منوی ساخت |
| 70 | Dhafra | `UAE_Dhafra` | — | UAE | فعال در منوی ساخت |
| 71 | Dnipro | `Ukraine_Dnipro` | — | Ukraine | فعال در منوی ساخت |
| 72 | Donar | `Germany_Donar` | — | Germany | فعال در منوی ساخت |
| 73 | ELSA | `Germany_ELSA` | — | Germany | فعال در منوی ساخت |
| 74 | Emad | `Iran_Emad` | — | Iran | فعال در منوی ساخت |
| 75 | Escorial | `Spain_Escorial` | — | Spain, Nato | فعال در منوی ساخت |
| 76 | Etna | `Italy_Etna` | — | Italy | فعال در منوی ساخت |
| 77 | EXTRA | `Israel_EXTRA` | — | Israel | فعال در منوی ساخت |
| 78 | Fahad-3 TEL | `IraqVehicleFahad3` | IraqVehicleFahad3_CombatMode, IraqVehicleFahad3_PackMode | Iraq | فعال در منوی ساخت |
| 79 | Fajr | `Libya_Fajr` | — | Libya | فعال در منوی ساخت |
| 80 | Fajr | `SaudiArabia_Fajr` | — | SaudiArabia | فعال در منوی ساخت |
| 81 | Falcon | `UAE_Falcon` | — | UAE | فعال در منوی ساخت |
| 82 | Fateh 313 | `IranVehicleFateh313` | — | Iran | فعال در منوی ساخت |
| 83 | Fattah MSRBM | `IranVehicleFattah` | — | Iran | فعال در منوی ساخت |
| 84 | Fenrir | `Sweden_Fenrir` | — | Sweden | فعال در منوی ساخت |
| 85 | Fezzan | `Libya_Fezzan` | — | Libya | فعال در منوی ساخت |
| 86 | FireShadow | `Britain_FireShadow` | — | Britain | فعال در منوی ساخت |
| 87 | Folgore | `Italy_Folgore` | — | Italy | فعال در منوی ساخت |
| 88 | Freccia | `Italy_Freccia` | — | Italy | فعال در منوی ساخت |
| 89 | Fūjin | `Japan_Fujin` | — | Japan | فعال در منوی ساخت |
| 90 | Gaulle | `France_Gaulle` | — | France | فعال در منوی ساخت |
| 91 | Geommu | `SouthKorea_Geommu` | — | SouthKorea | فعال در منوی ساخت |
| 92 | Gezgin | `Turkey_Gezgin` | — | Turkey | فعال در منوی ساخت |
| 93 | Ghadr | `Iran_Ghadr` | — | Iran | فعال در منوی ساخت |
| 94 | Ghauri | `Pakistan_Ghauri` | — | Pakistan | فعال در منوی ساخت |
| 95 | Ghaznavi | `Pakistan_Ghaznavi` | — | Pakistan | فعال در منوی ساخت |
| 96 | Gokturk | `Turkey_Gokturk` | — | Turkey | فعال در منوی ساخت |
| 97 | Great Man-Made River | `Libya_GreatManMadeRiver` | — | Libya | فعال در منوی ساخت |
| 98 | Grom | `Ukraine_Grom` | — | Ukraine | فعال در منوی ساخت |
| 99 | Gungnir | `Sweden_Gungnir` | — | Sweden | فعال در منوی ساخت |
| 100 | Hades | `France_Hades` | — | France | فعال در منوی ساخت |
| 101 | Haeryong | `SouthKorea_Haeryong` | — | SouthKorea | فعال در منوی ساخت |
| 102 | Haetsal | `SouthKorea_Haetsal` | — | SouthKorea | فعال در منوی ساخت |
| 103 | Hajar | `SaudiArabia_Hajar` | — | SaudiArabia | فعال در منوی ساخت |
| 104 | Halcon | `Spain_Halcon` | — | Spain, Nato | فعال در منوی ساخت |
| 105 | Hayate | `Japan_Hayate` | — | Japan | فعال در منوی ساخت |
| 106 | Hispania | `Spain_Hispania` | — | Spain, Nato | فعال در منوی ساخت |
| 107 | Homs | `Syria_Homs` | — | Syria | فعال در منوی ساخت |
| 108 | Hormuz | `Iran_Hormuz` | — | Iran | فعال در منوی ساخت |
| 109 | Hrim | `Ukraine_Hrim` | — | Ukraine | فعال در منوی ساخت |
| 110 | Hwarang | `SouthKorea_Hwarang` | — | SouthKorea | فعال در منوی ساخت |
| 111 | Hwasong-10 | `NorthKorea_Hwasong10` | — | NorthKorea | فعال در منوی ساخت |
| 112 | Hwasong-12 | `NorthKorea_Hwasong12` | — | NorthKorea | فعال در منوی ساخت |
| 113 | Hwasong-14 | `NorthKorea_Hwasong14` | — | NorthKorea | فعال در منوی ساخت |
| 114 | Hwasong-15 | `NorthKorea_Hwasong15` | — | NorthKorea | فعال در منوی ساخت |
| 115 | Hwasong-17 | `NorthKorea_Hwasong17` | — | NorthKorea | فعال در منوی ساخت |
| 116 | Hwasong-6 | `NorthKorea_Hwasong6` | — | NorthKorea | فعال در منوی ساخت |
| 117 | Hùng Vương | `Vietnam_HungVuong` | — | Vietnam | فعال در منوی ساخت |
| 118 | Hồng Hà | `Vietnam_HongHa` | — | Vietnam | فعال در منوی ساخت |
| 119 | Iberia | `Spain_Iberia` | — | Spain, Nato | فعال در منوی ساخت |
| 120 | Ingwe | `SouthAfrica_Ingwe` | — | SouthAfrica | فعال در منوی ساخت |
| 121 | IranDroneShahed136AIGV1 | `IranDroneShahed136AIGV1` | — | Iran | خارج از منو |
| 122 | IranDroneShahed136AIGV2 | `IranDroneShahed136AIGV2` | — | Iran | خارج از منو |
| 123 | IranDroneShahed136AIGV3 | `IranDroneShahed136AIGV3` | — | Iran | خارج از منو |
| 124 | IranDroneShahed238 | `IranDroneShahed238` | — | Iran | فعال در منوی ساخت |
| 125 | IranVehicleFattah2 | `IranVehicleFattah2` | — | Iran | فعال در منوی ساخت |
| 126 | IraqFahad3Launcher_AAM_AI | `IraqFahad3Launcher_AAM_AI` | — | Iraq | خارج از منو |
| 127 | IraqFahad3SamSite | `IraqFahad3SamSite` | — | Iraq | فعال در منوی ساخت |
| 128 | Iskander | `Russia_Iskander` | — | Russia | فعال در منوی ساخت |
| 129 | Iskander M | `Arb_9K720SV1` | Arb_9K720M_AI, GLAVehicleScudLauncher | Arabic Alliance, GLA | فعال در منوی ساخت |
| 130 | Iskander TEL | `RussiaVehicle9K720` | — | Russia | فعال در منوی ساخت |
| 131 | Jamahiriya | `Libya_Jamahiriya` | — | Libya | فعال در منوی ساخت |
| 132 | JASSM | `America_JASSM` | — | America | فعال در منوی ساخت |
| 133 | Jericho2 | `Israel_Jericho2` | — | Israel | فعال در منوی ساخت |
| 134 | Jericho3 | `Israel_Jericho3` | — | Israel | فعال در منوی ساخت |
| 135 | JFS-M | `Germany_JFSM` | — | Germany | فعال در منوی ساخت |
| 136 | Jindallae | `SouthKorea_Jindallae` | — | SouthKorea | فعال در منوی ساخت |
| 137 | JL2 | `China_JL2` | — | China | فعال در منوی ساخت |
| 138 | JL3 | `China_JL3` | — | China | فعال در منوی ساخت |
| 139 | Kalibr | `Russia_Kalibr` | — | Russia | فعال در منوی ساخت |
| 140 | Karoo | `SouthAfrica_Karoo` | — | SouthAfrica | فعال در منوی ساخت |
| 141 | KEPD-350 | `Germany_KEPD` | — | Germany | فعال در منوی ساخت |
| 142 | Keren | `Israel_Keren` | — | Israel | فعال در منوی ساخت |
| 143 | Khaibar | `Syria_Khaibar` | — | Syria | فعال در منوی ساخت |
| 144 | Khalid Ibn Alwaleed | `Arab_Khalid` | Arab_Khalid_AI | Arabic Alliance, GLA | فعال در منوی ساخت |
| 145 | Khalij | `Iran_Khalij` | — | Iran | فعال در منوی ساخت |
| 146 | Kheibar | `Iran_Kheibar` | — | Iran | فعال در منوی ساخت |
| 147 | Khormshar ICBM | `IranVehicleKhormshar` | IranVehicleKhormshar_AI, Factory_KhormsharOnce | Iran, Iraq | فعال در منوی ساخت |
| 148 | Khorram | `Iran_Khorram` | — | Iran | فعال در منوی ساخت |
| 149 | Kinzhal | `Russia_Kinzhal` | — | Russia | فعال در منوی ساخت |
| 150 | KN-02 | `NorthKorea_KN02` | — | NorthKorea | فعال در منوی ساخت |
| 151 | KN-24 | `NorthKorea_KN24` | — | NorthKorea | فعال در منوی ساخت |
| 152 | KN-25 | `NorthKorea_KN25` | — | NorthKorea | فعال در منوی ساخت |
| 153 | Kozak | `Ukraine_Kozak` | — | Ukraine | فعال در منوی ساخت |
| 154 | Kurogane | `Japan_Kurogane` | — | Japan | فعال در منوی ساخت |
| 155 | Kyiv | `Ukraine_Kyiv` | — | Ukraine | فعال در منوی ساخت |
| 156 | Kōryū | `Japan_Koryu` | — | Japan | فعال در منوی ساخت |
| 157 | Liwa | `UAE_Liwa` | — | UAE | فعال در منوی ساخت |
| 158 | LORA | `Israel_LORA` | — | Israel | فعال در منوی ساخت |
| 159 | LRASM | `America_LRASM` | — | America | فعال در منوی ساخت |
| 160 | Luna | `Syria_Luna` | — | Syria | فعال در منوی ساخت |
| 161 | Lạc Việt | `Vietnam_LacViet` | — | Vietnam | فعال در منوی ساخت |
| 162 | M-142 ATACMS | `Specter_EU5_M142ATACMS` | NatoVehicleM142ATACMS, BritainVehicleM142ATACMS, FranceVehicleM142ATACMS, GermanyVehicleM142ATACMS, ItalyVehicleM142ATACMS, SwedenVehicleM142ATACMS, TurkeyVehicleM142ATACMS, UkraineVehicleM142ATACMS | Nato, Britain, France, Germany, Italy, Ukraine, Sweden, Turkey | فعال در منوی ساخت |
| 163 | M1057T BGM-109 Launcher | `US_M1075T_BGM109` | — | America | فعال در منوی ساخت |
| 164 | M270 MLRS | `AmericaVehicleTomahawk` | — | America | فعال در منوی ساخت |
| 165 | M51A | `France_M51A` | — | France | فعال در منوی ساخت |
| 166 | Maginot | `France_Maginot` | — | France | فعال در منوی ساخت |
| 167 | Marte | `Italy_Marte` | — | Italy | فعال در منوی ساخت |
| 168 | MdCN | `France_MdCN` | — | France | فعال در منوی ساخت |
| 169 | Mezyad | `UAE_Mezyad` | — | UAE | فعال در منوی ساخت |
| 170 | MGM134 | `US_M1075I_Trident` | US_M1075I_Trident_AI | America | فعال در منوی ساخت |
| 171 | Midgard | `Sweden_Midgard` | — | Sweden | فعال در منوی ساخت |
| 172 | Mokopa | `SouthAfrica_Mokopa` | — | SouthAfrica | فعال در منوی ساخت |
| 173 | Mugunghwa | `SouthKorea_Mugunghwa` | — | SouthKorea | فعال در منوی ساخت |
| 174 | Murzuq | `Libya_Murzuq` | — | Libya | فعال در منوی ساخت |
| 175 | MX | `America_MX` | — | America | فعال در منوی ساخت |
| 176 | Najm | `SaudiArabia_Najm` | — | SaudiArabia | فعال در منوی ساخت |
| 177 | Nasr | `Pakistan_Nasr` | — | Pakistan | فعال در منوی ساخت |
| 178 | Neptune | `Ukraine_Neptune` | — | Ukraine | فعال در منوی ساخت |
| 179 | Nirbhay | `India_Nirbhay` | — | India | فعال در منوی ساخت |
| 180 | Norrsken | `Sweden_Norrsken` | — | Sweden | فعال در منوی ساخت |
| 181 | Odesa | `Ukraine_Odesa` | — | Ukraine | فعال در منوی ساخت |
| 182 | Odin | `Germany_Odin` | — | Germany | فعال در منوی ساخت |
| 183 | Oniks | `Russia_Oniks` | — | Russia | فعال در منوی ساخت |
| 184 | Orouba | `Libya_Orouba` | — | Libya | فعال در منوی ساخت |
| 185 | Overberg | `SouthAfrica_Overberg` | — | SouthAfrica | فعال در منوی ساخت |
| 186 | Pelayo | `Spain_Pelayo` | — | Spain, Nato | فعال در منوی ساخت |
| 187 | Perseus | `Britain_Perseus` | — | Britain | فعال در منوی ساخت |
| 188 | PershingII | `America_PershingII` | — | America | فعال در منوی ساخت |
| 189 | Pfeil | `Germany_Pfeil` | — | Germany | فعال در منوی ساخت |
| 190 | PK | `America_PK` | — | America | فعال در منوی ساخت |
| 191 | Pluton | `France_Pluton` | — | France | فعال در منوی ساخت |
| 192 | Polaris | `Britain_Polaris` | — | Britain | فعال در منوی ساخت |
| 193 | Polarstern | `Germany_Polarstern` | — | Germany | فعال در منوی ساخت |
| 194 | Popeye | `Israel_Popeye` | — | Israel | فعال در منوی ساخت |
| 195 | Prahaar | `India_Prahaar` | — | India | فعال در منوی ساخت |
| 196 | Pralay | `India_Pralay` | — | India | فعال در منوی ساخت |
| 197 | Prithvi | `India_Prithvi` | — | India | فعال در منوی ساخت |
| 198 | PrSM | `America_PrSM` | — | America | فعال در منوی ساخت |
| 199 | Pukguksong-2 | `NorthKorea_Pukguksong2` | — | NorthKorea | فعال در منوی ساخت |
| 200 | Qader | `Iran_Qader` | — | Iran | فعال در منوی ساخت |
| 201 | Qalamoun | `Syria_Qalamoun` | — | Syria | فعال در منوی ساخت |
| 202 | Qamar | `UAE_Qamar` | — | UAE | فعال در منوی ساخت |
| 203 | Qasr | `SaudiArabia_Qasr` | — | SaudiArabia | فعال در منوی ساخت |
| 204 | Qiam | `Iran_Qiam` | — | Iran | فعال در منوی ساخت |
| 205 | R-17 | `Syria_R17` | — | Syria | فعال در منوی ساخت |
| 206 | Raijin | `Japan_Raijin` | — | Japan | فعال در منوی ساخت |
| 207 | Rampage | `Israel_Rampage` | — | Israel | فعال در منوی ساخت |
| 208 | Ratel | `SouthAfricaVehicleRatel` | — | SouthAfrica | خارج از منو |
| 209 | Ratel ZT3 | `SouthAfricaVehicleZT3` | — | SouthAfrica | خارج از منو |
| 210 | RBS15 | `Sweden_RBS15` | — | Sweden | فعال در منوی ساخت |
| 211 | Resolution | `Britain_Resolution` | — | Britain | فعال در منوی ساخت |
| 212 | Rimal | `SaudiArabia_Rimal` | — | SaudiArabia | فعال در منوی ساخت |
| 213 | Rocks | `Israel_Rocks` | — | Israel | فعال در منوی ساخت |
| 214 | Roma | `Italy_Roma` | — | Italy | فعال در منوی ساخت |
| 215 | RS24 Yars | `RussiaVehicleRS24` | Russia_RS24_Yars_AI, Factory_RS24YarsOnce | Russia, China, Iraq | فعال در منوی ساخت |
| 216 | RSA-2 | `SouthAfrica_RSA2` | — | SouthAfrica | فعال در منوی ساخت |
| 217 | RSA-3 | `SouthAfrica_RSA3` | — | SouthAfrica | فعال در منوی ساخت |
| 218 | Rubis | `France_Rubis` | — | France | فعال در منوی ساخت |
| 219 | RussiaVehicle9K720K | `RussiaVehicle9K720K` | — | Russia, China | فعال در منوی ساخت |
| 220 | Saetta | `Italy_Saetta` | — | Italy | فعال در منوی ساخت |
| 221 | Sahm | `SaudiArabia_Sahm` | — | SaudiArabia | فعال در منوی ساخت |
| 222 | Sahra | `Libya_Sahra` | — | Libya | فعال در منوی ساخت |
| 223 | SamSiteLaunchControlRoom | `SamSiteLaunchControlRoom` | — | America | خارج از منو |
| 224 | Sancak | `Turkey_Sancak` | — | Turkey | فعال در منوی ساخت |
| 225 | Sapsan | `Ukraine_Sapsan` | — | Ukraine | فعال در منوی ساخت |
| 226 | Saqr | `SaudiArabia_Saqr` | — | SaudiArabia | فعال در منوی ساخت |
| 227 | SCALP | `FranceVehicleSCALPTEL` | — | France | خارج از منو |
| 228 | Scud | `SyriaVehicleScud` | — | Syria | خارج از منو |
| 229 | Scud Launcher | `GLAVehicleScudLauncherHiDef` | — | Arabic Alliance, GLAToxinGeneral | خارج از منو |
| 230 | SCUD Launcher | `Slth_GLAVehicleScudLauncher` | — | GLAStealthGeneral | خارج از منو |
| 231 | Scud-B | `LibyaVehicleScudB` | — | Libya | خارج از منو |
| 232 | Scud-B | `VietnamVehicleScud` | — | Vietnam | خارج از منو |
| 233 | Sentinel | `America_Sentinel` | — | America | فعال در منوی ساخت |
| 234 | Shahed-136 Suicide Drone | `IranDroneShahed136` | — | Iran | فعال در منوی ساخت |
| 235 | Shaheen-I | `Pakistan_Shaheen1` | — | Pakistan | فعال در منوی ساخت |
| 236 | Shaheen-II | `PakistanVehicleShaheen` | — | Pakistan | خارج از منو |
| 237 | Shaheen-II | `Pakistan_Shaheen2` | — | Pakistan | فعال در منوی ساخت |
| 238 | Shaheen-III | `Pakistan_Shaheen3` | — | Pakistan | فعال در منوی ساخت |
| 239 | Sham | `Syria_Sham` | — | Syria | فعال در منوی ساخت |
| 240 | Shaurya | `India_Shaurya` | — | India | فعال در منوی ساخت |
| 241 | Shavit | `Israel_Shavit` | — | Israel | فعال در منوی ساخت |
| 242 | Shiden | `Japan_Shiden` | — | Japan | فعال در منوی ساخت |
| 243 | Siegfried | `Germany_Siegfried` | — | Germany | فعال در منوی ساخت |
| 244 | Simorgh | `Iran_Simorgh` | — | Iran | فعال در منوی ساخت |
| 245 | Siraj | `UAE_Siraj` | — | UAE | فعال در منوی ساخت |
| 246 | Sirt | `Libya_Sirt` | — | Libya | فعال در منوی ساخت |
| 247 | Skerpioen | `SouthAfrica_Skerpioen` | — | SouthAfrica | فعال در منوی ساخت |
| 248 | Skybolt | `Britain_Skybolt` | — | Britain | فعال در منوی ساخت |
| 249 | Sleipnir | `Sweden_Sleipnir` | — | Sweden | فعال در منوی ساخت |
| 250 | SOM | `Turkey_SOM` | — | Turkey | فعال در منوی ساخت |
| 251 | Sovereign | `Britain_Sovereign` | — | Britain | فعال در منوی ساخت |
| 252 | Spear | `Britain_Spear` | — | Britain | فعال در منوی ساخت |
| 253 | Storm Shadow | `BritainVehicleStormShadowTEL` | — | Britain | خارج از منو |
| 254 | Storm Shadow | `ItalyVehicleStormShadowTEL` | — | Italy | خارج از منو |
| 255 | Stromboli | `Italy_Stromboli` | — | Italy | فعال در منوی ساخت |
| 256 | Sông Hồng | `Vietnam_SongHong` | — | Vietnam | فعال در منوی ساخت |
| 257 | Taebaek | `SouthKorea_Taebaek` | — | SouthKorea | فعال در منوی ساخت |
| 258 | Taurus | `GermanyVehicleTaurusTEL` | — | Germany | خارج از منو |
| 259 | Tayfun | `Turkey_Tayfun` | — | Turkey | فعال در منوی ساخت |
| 260 | Tenrai | `Japan_Tenrai` | — | Japan | فعال در منوی ساخت |
| 261 | Terrible | `France_Terrible` | — | France | فعال در منوی ساخت |
| 262 | Teseo | `Italy_Teseo` | — | Italy | فعال در منوی ساخت |
| 263 | Thăng Long | `Vietnam_ThangLong` | — | Vietnam | فعال در منوی ساخت |
| 264 | Tishreen | `Syria_Tishreen` | — | Syria | فعال در منوی ساخت |
| 265 | Tochka | `Russia_Tochka` | — | Russia | فعال در منوی ساخت |
| 266 | Tochka | `Syria_Tochka` | — | Syria | فعال در منوی ساخت |
| 267 | Topol | `Russia_Topol` | — | Russia | فعال در منوی ساخت |
| 268 | Trafalgar | `Britain_Trafalgar` | — | Britain | فعال در منوی ساخت |
| 269 | Tridente | `Spain_Tridente` | — | Spain, Nato | فعال در منوی ساخت |
| 270 | Triomphant | `France_Triomphant` | — | France | فعال در منوی ساخت |
| 271 | Tryzub | `Ukraine_Tryzub` | — | Ukraine | فعال در منوی ساخت |
| 272 | Trường Sơn | `Vietnam_TruongSon` | — | Vietnam | فعال در منوی ساخت |
| 273 | Type 12 Kai | `Japan_Type12Kai` | — | Japan | فعال در منوی ساخت |
| 274 | Type 88 Kai | `Japan_Type88Kai` | — | Japan | فعال در منوی ساخت |
| 275 | UAE_AbabeelTEL | `UAE_AbabeelTEL` | India_AbabeelTEL, Libya_AbabeelTEL, Pakistan_AbabeelTEL, SaudiArabia_AbabeelTEL, SouthAfrica_AbabeelTEL, Syria_AbabeelTEL | India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 276 | UAE_ShaheenTEL | `UAE_ShaheenTEL` | India_ShaheenTEL, Libya_ShaheenTEL, Pakistan_ShaheenTEL, SaudiArabia_ShaheenTEL, SouthAfrica_ShaheenTEL, Syria_ShaheenTEL | India, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | خارج از منو |
| 277 | Umbani | `SouthAfrica_Umbani` | — | SouthAfrica | فعال در منوی ساخت |
| 278 | Valkiri | `SouthAfrica_Valkiri` | — | SouthAfrica | فعال در منوی ساخت |
| 279 | Vanguard | `Britain_Vanguard` | — | Britain | فعال در منوی ساخت |
| 280 | VCM-01 | `Vietnam_VCM01` | — | Vietnam | فعال در منوی ساخت |
| 281 | VCM-02 | `Vietnam_VCM02` | — | Vietnam | فعال در منوی ساخت |
| 282 | Vesuvio | `Italy_Vesuvio` | — | Italy | فعال در منوی ساخت |
| 283 | Vidar | `Sweden_Vidar` | — | Sweden | فعال در منوی ساخت |
| 284 | Vilkha | `Ukraine_Vilkha` | — | Ukraine | فعال در منوی ساخت |
| 285 | Voevoda | `Russia_Voevoda` | — | Russia | فعال در منوی ساخت |
| 286 | Wadi | `SaudiArabia_Wadi` | — | SaudiArabia | فعال در منوی ساخت |
| 287 | Waha | `Libya_Waha` | — | Libya | فعال در منوی ساخت |
| 288 | Walküre | `Germany_Walkure` | — | Germany | فعال در منوی ساخت |
| 289 | Yakhont | `Syria_Yakhont` | — | Syria | فعال در منوی ساخت |
| 290 | Yamato | `Japan_Yamato` | — | Japan | فعال در منوی ساخت |
| 291 | Yars | `Russia_Yars` | — | Russia | فعال در منوی ساخت |
| 292 | Yggdrasil | `Sweden_Yggdrasil` | — | Sweden | فعال در منوی ساخت |
| 293 | Yildirim | `Turkey_Yildirim` | — | Turkey | فعال در منوی ساخت |
| 294 | YJ18 | `China_YJ18` | — | China | فعال در منوی ساخت |
| 295 | YJ21 | `China_YJ21` | — | China | فعال در منوی ساخت |
| 296 | Zircon | `Russia_Zircon` | — | Russia | فعال در منوی ساخت |

## رادارها و جنگ الکترونیک

تعداد یکتا: **30**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | 30N6E Mobile Radar | `ArabRadar30N6E_AI` | — | Arabic Alliance, GLA | خارج از منو |
| 2 | 30N6E Mobile Radar | `Arb_30N6E` | Arb_30N6E_CombatMode, Arb_30N6E_PackMode | Arabic Alliance, GLA | فعال در منوی ساخت |
| 3 | 59N6E RadarStation | `ArabRadar59N6ES` | — | Arabic Alliance, GLA | خارج از منو |
| 4 | 92N6E | `Iraq_92N6E_Site_AI` | — | Iraq | خارج از منو |
| 5 | 96-L6 TSP Engagment Radar | `RussiaVehicle96L6TSP` | Iraq_MIC_96L6TSP | Iraq, Russia, China, Iran, America, Israel | فعال در منوی ساخت |
| 6 | 96-L6 TSP Engagment Radar | `RussiaVehicle96L6TSPCombatMode` | — | Russia | خارج از منو |
| 7 | 96-L6 TSP Engagment Radar | `RussiaVehicle96L6TSPPackMode` | — | Russia | خارج از منو |
| 8 | AI_Radar_PowerDownLoop | `AI_Radar_PowerDownLoop` | — | Unknown | خارج از منو |
| 9 | AN/MPQ-65 | `UAEVehicleRadar` | — | UAE | خارج از منو |
| 10 | AN/MPQ65 Radar | `AmericaRadarAN/MPQ65` | — | America | خارج از منو |
| 11 | AN/MPQ65E | `ArabRadarAN/MPQ65E` | — | Arabic Alliance, GLA | خارج از منو |
| 12 | Attack Outpost | `Infa_ChinaVehicleListeningOutpost` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 13 | B-340 Engagment Radar | `IraqVehicleB340` | IraqVehicleB340_CombatMode, IraqVehicleB340_PackMode | Iraq | فعال در منوی ساخت |
| 14 | ECM Tank | `Infa_ChinaTankECM` | — | ChinaInfantryGeneral | فعال در منوی ساخت |
| 15 | HT-233 Radar | `ChinaRadarHT233_AI` | — | China | خارج از منو |
| 16 | IBIS-150 | `PakistanVehicleRadar` | — | Pakistan | خارج از منو |
| 17 | IranRadarKhordad15 | `IranRadarKhordad15` | — | Iran | خارج از منو |
| 18 | IsraelRadarIronDish | `IsraelRadarIronDish` | — | Israel | خارج از منو |
| 19 | J/TPS-P18 | `JapanVehicleRadar` | — | Japan | خارج از منو |
| 20 | Karrar2 | `Iraq_Karrar2` | IranVehicleKrasukha2 | Iran, Iraq | فعال در منوی ساخت |
| 21 | Krasukha 4 | `RussiaVehicleKrasukha4` | ChinaVehicleKrasukha4, Iraq_MIC_Krasukha4, RussiaVehicleListeningOutpost | China, Iraq, Russia, Iran, America, Israel | فعال در منوی ساخت |
| 22 | Krasukha 4E | `Arab_Krasukha-4` | GLAVehicleRadarVan | Arabic Alliance, GLA | فعال در منوی ساخت |
| 23 | Lamiaa | `Iraq_Lamiaa` | SpecterRadar_Lamina | Iraq | فعال در منوی ساخت |
| 24 | Meraj Radar | `Iran_Meraj` | Iran_Meraj_CombatMode, Iran_Meraj_PackMode | Iran | فعال در منوی ساخت |
| 25 | P-15 | `LibyaVehicleRadar` | — | Libya | خارج از منو |
| 26 | Radar Van | `Slth_GLAVehicleRadarVan` | — | GLAStealthGeneral | فعال در منوی ساخت |
| 27 | Sarab 3 | `Iraq_Sarab3` | SpecterRadar_Sarab3 | Iraq | فعال در منوی ساخت |
| 28 | TPS-830K | `SouthKoreaVehicleRadar` | — | SouthKorea | خارج از منو |
| 29 | TRML-4D | `GermanyVehicleTRML` | — | Germany | خارج از منو |
| 30 | TRML-4D | `NatoVehicleTRML4D` | Iraq_MIC_TRML4D, NatoVehicleTRML4D_CombatMode, NatoVehicleTRML4D_PackMode, BritainVehicleTRML4D, BritainVehicleTRML4D_CombatMode, BritainVehicleTRML4D_PackMode, FranceVehicleTRML4D, FranceVehicleTRML4D_CombatMode, FranceVehicleTRML4D_PackMode, GermanyVehicleTRML4D, GermanyVehicleTRML4D_CombatMode, GermanyVehicleTRML4D_PackMode, ItalyVehicleTRML4D, ItalyVehicleTRML4D_CombatMode, ItalyVehicleTRML4D_PackMode, Specter_EU5_TRML4D, SwedenVehicleTRML4D, SwedenVehicleTRML4D_CombatMode, SwedenVehicleTRML4D_PackMode, TurkeyVehicleTRML4D, TurkeyVehicleTRML4D_CombatMode, TurkeyVehicleTRML4D_PackMode, UkraineVehicleTRML4D, UkraineVehicleTRML4D_CombatMode, UkraineVehicleTRML4D_PackMode | Iraq, Russia, China, Iran, America, Israel, Nato, Britain, France, Germany, Italy, Ukraine, Sweden, Turkey | فعال در منوی ساخت |

## خودروهای پشتیبانی

تعداد یکتا: **7**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | Construction Dozer | `AmericaVehicleDozer` | — | America | فعال در منوی ساخت |
| 2 | Construction Dozer | `GLAVehicleDozer` | — | Arabic Alliance, GLA | خارج از منو |
| 3 | Construction Dozer | `IranVehicleDozer` | ChinaVehicleDozer, RussiaVehicleDozer, India_Dozer, Infa_ChinaVehicleDozer, Libya_Dozer, Pakistan_Dozer, SaudiArabia_Dozer, SouthAfrica_Dozer, Syria_Dozer, UAE_Dozer | China, Iran, Russia, India, ChinaInfantryGeneral, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, UAE | فعال در منوی ساخت |
| 4 | Construction Dozer | `NatoVehicleDozer` | GLAInfantryWorker, AirF_AmericaVehicleDozer, Israel_VehicleDozer, BritainVehicleDozer, FranceVehicleDozer, GermanyVehicleDozer, ItalyVehicleDozer, SwedenVehicleDozer, TurkeyVehicleDozer, UkraineVehicleDozer | Arabic Alliance, GLA, Israel, Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |
| 5 | Repair Drone | `AmericaVehicleRepairDrone` | — | America | خارج از منو |
| 6 | VT-72B | `IndiaVehicleVT72B` | — | India | خارج از منو |
| 7 | VT72B Utility Vehicle | `UAE_VT72B` | Iraq_VT72B, Slth_GLAInfantryWorker, Egypt_VT72B, India_VT72B, Japan_VT72B, Libya_VT72B, NorthKorea_VT72B, Pakistan_VT72B, SaudiArabia_VT72B, SouthAfrica_VT72B, SouthKorea_VT72B, Syria_VT72B, Vietnam_VT72B | Iraq, Egypt, India, Japan, Libya, NorthKorea, Pakistan, SaudiArabia, SouthAfrica, SouthKorea, Syria, UAE, Vietnam | فعال در منوی ساخت |

## تجهیزات و پرتابگرهای پهپادی

تعداد یکتا: **17**

| # | نام نمایشی | نام داخلی اصلی | نام‌های جایگزین / کلون‌ها | کشورها | وضعیت |
|---:|---|---|---|---|---|
| 1 | Ababil200 | `Iraq_Ababil200` | — | Iraq | فعال در منوی ساخت |
| 2 | AmericaVehicleBattleDrone | `AmericaVehicleBattleDrone` | AirF_AmericaVehicleBattleDrone | America, Israel, AmericaAirForceGeneral | خارج از منو |
| 3 | Arash-2 Suicide Drone | `IranDroneArash2` | — | Iran | فعال در منوی ساخت |
| 4 | ASN-301 Suicide Drone | `ChinaDroneAsn301` | — | China | فعال در منوی ساخت |
| 5 | Guardian Drone | `AmericaVehicleGuardianDrone` | — | America | خارج از منو |
| 6 | Hellfire Drone | `AirF_AmericaVehicleHellfireDrone` | — | Israel, AmericaAirForceGeneral | خارج از منو |
| 7 | Hellfire Drone | `AmericaVehicleHellfireDrone` | — | America | خارج از منو |
| 8 | IsraelDroneHaropExpanded | `IsraelDroneHaropExpanded` | — | Israel | فعال در منوی ساخت |
| 9 | JapanDroneBulsae4 | `JapanDroneBulsae4` | NorthKoreaDroneBulsae4, SouthKoreaDroneBulsae4, VietnamDroneBulsae4 | Japan, NorthKorea, SouthKorea, Vietnam | خارج از منو |
| 10 | JapanDroneSaetbyol9 | `JapanDroneSaetbyol9` | NorthKoreaDroneSaetbyol9, SouthKoreaDroneSaetbyol9, VietnamDroneSaetbyol9 | Japan, NorthKorea, SouthKorea, Vietnam | فعال در منوی ساخت |
| 11 | RussiaDroneFPV | `RussiaDroneFPV` | — | Russia | خارج از منو |
| 12 | Sarab7 | `Iraq_Sarab7` | — | Iraq | فعال در منوی ساخت |
| 13 | Scout Drone | `AmericaVehicleScoutDrone` | AirF_AmericaVehicleScoutDrone | America, Israel, AmericaAirForceGeneral | خارج از منو |
| 14 | Sentry Drone | `MISSION_AmericaVehicleSentryDrone` | — | America | خارج از منو |
| 15 | Shahed-136 Mobile Launcher | `IranVehicleShahedLauncher` | SpecterRadar_ShahedLauncher | Iran, Iraq | فعال در منوی ساخت |
| 16 | Spy Drone | `AmericaVehicleSpyDrone` | AirF_AmericaVehicleSpyDrone | America, Israel, AmericaAirForceGeneral | خارج از منو |
| 17 | Switchblade 600 | `NatoDroneSwitchblade600` | AmericaDroneSwitchblade600, BritainDroneSwitchblade600, FranceDroneSwitchblade600, GermanyDroneSwitchblade600, ItalyDroneSwitchblade600, SwedenDroneSwitchblade600, TurkeyDroneSwitchblade600, UkraineDroneSwitchblade600 | America, Arabic Alliance, Nato, Britain, France, Germany, Italy, Sweden, Turkey, Ukraine | فعال در منوی ساخت |

وضعیت «فعال در منوی ساخت» یعنی دست‌کم یک نسخه از آن تجهیز در زنجیرهٔ زنده Object → CommandButton → CommandSet ساختمان است.

## SHA-256

- `SPECTER_UNIQUE_EQUIPMENT_MASTER_LIST.xlsx`: `22bc81bcacc035674c842b8fea4aa4d285c19cce1d262cf9749edf6bc40da2a5`
- هش فایل Markdown در `SHA256SUMS.txt` آمده است (پس از نهایی‌شدن همین پرونده).
