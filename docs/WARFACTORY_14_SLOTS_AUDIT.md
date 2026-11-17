# SPECTER — ممیزی ۱۴ اسلات War Factory

تاریخ ممیزی: ۱ نوامبر ۲۰۲۶ (Asia/Tehran)  
وضعیت: **فقط گزارش؛ هیچ فایل DATA / ART / CommandSet / BIG / اجرایی تغییر نکرد.**  
ZH روی این داده‌ها اجرا نشده است.

## منبع زنده

| مورد | مقدار |
|---|---|
| انتشار DATA | GitHub Latest `s300-radar-drones` |
| فایل | `_SPEC_DATA_ONE.big` |
| SHA-256 | `aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53` |
| بارگذاری CommandSet | همه `Data\INI\CommandSet*.ini` داخل BIG؛ تعریف بعدی هم‌نام **last-win** است |
| هزینه / زمان | فیلد Object: `BuildCost` / `BuildTime` (ثانیه). دکمه `Cost` ندارد |
| نام دیده‌شده بازیکن | `CommandButton.TextLabel` → `Data\English\generals.csf` |

`CommandSet_ZZZZ_WarFactoryRebuild.ini` در این BIG **وجود ندارد** و روی منوی زنده اثر ندارد.

اسلات‌ها دقیقاً ۱ تا ۱۴ از CommandSet فعال ساختمان هستند. ترتیب فایل یا نام تجهیز حدس زده نشده.

---

## کدام CommandSet در بازی نهایی فعال است

| کشور | PlayerTemplate زنده | ساختمان War Factory | CommandSet شروع | CommandSet نهایی (اسلات‌های این گزارش) | منبع last-win |
|---|---|---|---|---|---|
| America | `FactionAmerica` — United State Armed Forces | `AmericaWarFactory_T` | `AmericaWarFactoryCommandSet_T` | `AmericaWarFactoryCommandSet_T3` پس از `Upgrade_US_Tier3` | `CommandSet.ini` |
| China | `FactionChina` — Chines PLA | `ChinaWarFactory` | `PLAWarFactoryCommandSet` | همان (ارتقا منو ندارد) | `CommandSet.ini` |
| Russia | `FactionRussia` | `RussiaWarFactory` | `RussiaWarFactoryCommandSet` | همان | `CommandSet.ini` |
| Iraq | `FactionIraq` — Iraqi Army (1970-2003) | `Iraq_WarFactory_T` | `Iraq_WarFactoryCommandSet_T3` | همان (ارتقا Tier روی خود ساختمان نیست) | `CommandSet_ZZZZ_IraqMicToWf.ini` (محتوا با `CommandSet.ini` یکی است) |
| Iran | `FactionIran` | `IranWarFactory` | `IranWarfactoryCommandSet` | همان | `CommandSet.ini` |
| Israel | `FactionAmericaAirForceGeneral` — **Israel Defence Forces** | `AirF_AmericaWarFactory` | `AirF_AmericaWarFactoryCommandSet` | همان | `CommandSet.ini` |
| Spain | **`FactionSpain` وجود ندارد** | **War Factory اسپانیایی وجود ندارد** | — | ۱۴ اسلات خالی | — |
| Arabic Alliance | `FactionGLA` — نمایش CSF: Arabic Alliance | `ArabicArmy_WarFactory` | `Arb_WarFactoryCommandSet_T` | `Arb_WarFactoryCommandSet_T3` پس از `Upgrade_Arb_Tier3` | `CommandSet.ini` |

### نکته‌های Override / مسیر اشتباه

- **America:** بولدوزر زنده (`AmericaDozerCommandSet` last-win در `CommandSet_ZZZZ_ZGlobalStoreFive.ini`) اسلات ۱۱ را `AmericaWarFactory_T` می‌سازد. اسلات ۱۷ همان منو `AmericaWarFactory` (AI، `AmericaWarFactoryCommandSet`) است و منوی بازیکن نیست. ساختمان از `_T` شروع می‌شود و با Tier1/2/3 به `_T3` می‌رسد. جدول زیر **منوی کامل T3** است.
- **China:** بولدوزر `PLADozerCommandSet` همان `ChinaWarFactory` را می‌سازد. `ChinaWarFactoryCommandSet` (منوی مخلوط روسی) روی AI روسیه مانده و منوی چین زنده نیست. اسلات‌های ۴ و ۷ در `PLAWarFactoryCommandSet` خالی‌اند (DF-41 از این دو اسلات برداشته شده). در اسلات‌های ۱–۱۴ دکمه Sell نیست.
- **Russia:** بولدوزر زنده اسلات ۹ = `Command_ConstructRussiaWarFactory` → Object `RussiaWarFactory`. ساختمان جایگزین `RussiaWarFactory_T` با سری `_T/_T1/_T2/_T3/_T4/_LBD` **ساخته نمی‌شود**. آن سری دکمه‌هایی دارد که به Object ناموجود وصل‌اند (`RussiaTankT72B3`, `Russian_T15`, `Russia_Krasukha-4`, `Russia_TOR_M2U`, `Russia_PantsirS1M`, `Russia_RS24_Yars`, `Russia_Bm30`, `Russian_92N6E`, `Russian_tos1a`, `Russian_S400`). Objectهای واقعی روسیه نام‌های بدون خط تیره‌اند (`RussiaTankT72B3M`, `RussiaVehicleKrasukha4`, …).
- **Iraq:** شروع‌کننده `Iraq_VT72B` است (نه بولدوزر). اسلات ۴ = `Iraq_WarFactory_T`. خود Object از ابتدا `Iraq_WarFactoryCommandSet_T3` را دارد. سری `_T/_T1/_T2` در `CommandSet.ini` تعریف شده ولی این ساختمان آن‌ها را سوییچ نمی‌کند.
- **Israel:** کشور قابل انتخاب با برچسب **Israel Defence Forces** همان `FactionAmericaAirForceGeneral` است. هم `AirF_AmericaDozerCommandSet` و هم `IsraelDozerCommandSet` (last-win) War Factory را `AirF_AmericaWarFactory` می‌سازند.  
  `FactionIsrael` (نمایش «Israel»، `StartingBuilding=Israel_MilitaryHQ`) هم playable است ولی بولدوزرش همان AirF WF را می‌سازد.  
  `Israel_WarFactory` + `Israel_WarFactoryCommandSet` در `CommandSet_Israel_Integrity.ini` مسیر باقی‌ماندهٔ بلااستفاده است: اسلات ۱ = `Command_ConstructIsrael_AD_Barak8` که **در CommandButton تعریف نشده**.
- **Spain:** `FactionSpain` نیست. `Spain_WarFactory` / `Command_ConstructSpainWarFactory` نیست. تنها ساختمان اسپانیا `Spain_MissileFactory` است (کارخانه موشک، نه WF). بولدوزر ناتو اسلات ۱۱ را `NatoWarFactory` و اسلات ۱۴ را `Spain_MissileFactory` می‌سازد. منوی NATO در پیوست آمده و **منوی اسپانیا نیست**.
- **Arabic Alliance ≠ Iraq.** AA = `ArabicArmy_WarFactory` / `Arb_WarFactoryCommandSet_*` / Side=GLA. عراق = `Iraq_WarFactory_T` / `Iraq_WarFactoryCommandSet_T3`.  
  AA از کمبو اسکرمیش مخفی است (`PlayableSide=No` و `StartingBuilding` خالی) ولی Object و CommandSet در DATA مانده‌اند. ارتقای اختیاری `Upgrade_EgyptArmy` منو را به `EgyptWarFactoryCommandSet` عوض می‌کند؛ جدول زیر T3 پیش‌فرض است. Sell روی اسلات ۱۷ است، نه ۱–۱۴.

---

## America — `AmericaWarFactoryCommandSet_T3`

ساختمان: `AmericaWarFactory_T` — `Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini`

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | M1A2Sepv1 | `Command_ConstructAmericaTankCrusader` | `AmericaTankCrusader` | تانک | 900 | 18.0 |
| 2 | M1128 Stryker MGS | `Command_ConstructAmericaVehicleM1128` | `AmericaVehicle_M1128` | نفربر | 700 | 10.0 |
| 3 | M-1296 APC | `Command_ConstructAmericaVehicleM1296` | `AmericaVehicleM1296` | نفربر | 900 | 12.0 |
| 4 | Oshkosh M-ATV | `Command_ConstructAmericaVehicleSentryDrone` | `AmericaVehicleSentryDrone` | خودرو | 600 | 10.0 |
| 5 | M270 MLRS | `Command_ConstructAmericaVehicleTomahawk` | `AmericaVehicleTomahawk` | راکت‌انداز | 1200 | 20.0 |
| 6 | M-109A7 155mm Artillary | `Command_ConstructAmericaTankM109A7` | `AmericaTankM109A7` | توپخانه | 1200 | 16.0 |
| 7 | M-6 Linebacker | `Command_ConstructAmericaVehicleAvenger` | `AmericaTankAvenger` | پدافند | 700 | 13.0 |
| 8 | M2A3 BUSKIII | `Command_ConstructAmericaVehicleMicrowave` | `AmericaTankMicrowave` | پدافند | 800 | 15.0 |
| 9 | AN/TPY-2 Mobile Radar System | `Command_ConstructAmericaVehicleAN_TPY2` | `US_AN_TPY2` | پدافند قدرتمند آمریکا | 2600 | 15.0 |
| 10 | THAAD Air Defense System | `Command_ConstructAmericaVehicleTHAAD` | `US_THAAD` | پدافند قدرتمند آمریکا | 3000 | 22.0 |
| 11 | M-142 HIMARS | `Command_ConstructAmericaVehicleM142` | `AmericaVehicleM142` | راکت‌انداز | 1200 | 18.0 |
| 12 | M1075I UGM133 Launcher | `Command_ConstructAmericaVehicleM1075I` | `US_M1075I_Trident` | پرتابگر بالستیک | 3400 | 22.0 |
| 13 | M1075T BGM-109 Cruise Missile Launcher | `Command_ConstructAmericaVehicleM1075T` | `US_M1075T_BGM109` | پرتابگر کروز | 1890 | 20.0 |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

یادداشت: اسلات ۴ دکمه هنوز `SentryDrone` است ولی TextLabel/Cameo به Oshkosh M-ATV عوض شده. اسلات ۸ همین وضع را با Microwave → برچسب M2A3 BUSKIII دارد. **اسلات ۹ و ۱۰ پدافند قدرتمند آمریکا** هستند.

---

## China — `PLAWarFactoryCommandSet`

ساختمان: `ChinaWarFactory` — `Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini`

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | ZTZ99A2 MBT | `Command_ConstructChinaTankBattleMaster` | `ChinaTankBattleMaster` | تانک | 1200 | 10.0 |
| 2 | AFT-10 Mobile ATGM System | `Command_ConstructChinaTankAFT10` | `ChinaTankAFT10` | تانک / ATGM | 1400 | 14.0 |
| 3 | DF-17 Hypersonic SRBM TEL | `Command_ConstructChinaVehicleDF17` | `ChinaVehicleDF17` | موشک بالستیک | 2000 | 22.0 |
| 4 | **خالی** | — | — | خالی | — | — |
| 5 | Tor-M2 | `Command_ConstructChinaTankTorM2` | `ChinaTankTorM2` | پدافند | 1600 | 11.0 |
| 6 | PGZ-04 SPAAAG | `Command_ConstructChinaTankPGZ04` | `ChinaTankPGZ04` | پدافند | 1000 | 10.0 |
| 7 | **خالی** | — | — | خالی | — | — |
| 8 | PHL-03 MLRS | `Command_ConstructChinaVehiclePHL03` | `ChinaVehiclePHL03` | راکت‌انداز | 1200 | 15.0 |
| 9 | PLZ-05 152mm SPG | `Command_ConstructChinaVehiclePLZ05` | `ChinaVehiclePLZ05` | توپخانه | 1200 | 16.0 |
| 10 | DF-21C SRBM | `Command_ConstructChinaVehicleDF21C` | `ChinaVehicleDF21C` | موشک بالستیک | 1600 | 20.0 |
| 11 | ZBD-04 IFV | `Command_ConstructChinaTankZBD04` | `ChinaTankZBD04` | نفربر | 1200 | 13.0 |
| 12 | HT-233 Radar | `Command_ConstructChinaVehicleHT233` | `ChinaVehicleHT233` | رادار پدافند | 2200 | 12.0 |
| 13 | DF-12 TBML | `Command_ConstructChinaVehicleDF12` | `ChinaVehicleDF12` | موشک بالستیک | 1600 | 17.0 |
| 14 | HQ-9B TEL | `Command_ConstructChinaVehicleHQ9` | `ChinaVehicleHQ9` | پدافند | 3200 | 13.0 |

اسلات‌های ۱۶ و ۱۷ فقط AI هستند (`AFT10_AI`, `ZBD04_AI`) و خارج از ۱۴ اسلات بازیکن‌اند. Sell در ۱–۱۴ نیست.

---

## Russia — `RussiaWarFactoryCommandSet`

ساختمان زنده: `RussiaWarFactory` — `Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini`  
بولدوزر last-win: `Command_ConstructRussiaWarFactory` → همین Object.

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | T-90A MBT | `Command_ConstructRussiaTankT90A` | `RussiaTankT90A` | تانک | 1200 | 16.0 |
| 2 | T-72B3 | `Command_ConstructRussiaTankT72B3M` | `RussiaTankT72B3M` | تانک | 1100 | 15.0 |
| 3 | BM-30 Smerch | `Command_ConstructRussiaVehicleBm30` | `RussiaVehicleBm30` | راکت‌انداز | 1100 | 15.0 |
| 4 | Krasukha-4 | `Command_ConstructRussiaVehicleKrasukha4` | `RussiaVehicleKrasukha4` | جنگ الکترونیک | 5000 | 25 |
| 5 | 2S-19M2 MSTA-S | `Command_ConstructRussiaArtillery2S19M2` | `RussiaArtillery2S19M2` | توپخانه | 1300 | 15.0 |
| 6 | BMP3M IFV | `Command_ConstructRussiaTankBMP3` | `RussiaTankBMP3` | نفربر | 1600 | 14.0 |
| 7 | Tor-M2M | `Command_ConstructRussiaTankTorM2M` | `RussiaTankTorM2M` | پدافند | 1100 | 10.0 |
| 8 | Pantsir-S1M | `Command_ConstructRussiaVehiclePantsirS1M` | `RussiaVehiclePantsirS1M` | پدافند | 800 | 10.0 |
| 9 | 92N6E Radar | `Command_ConstructRussiaVehicle92N6R` | `RussiaVehicle92N6R` | رادار پدافند | 2200 | 12.0 |
| 10 | S-400 TEL | `Command_ConstructRussiaVehicleS400` | `RussiaVehicleS400` | پدافند | 3200 | 13.0 |
| 11 | Tos-1A Solntsepek | `Command_ConstructRussiaTankTos1A` | `RussiaTankTos1A` | راکت‌انداز | 1500 | 16.0 |
| 12 | 9K720 Iskander-M | `Command_ConstructRussiaVehicle9K720` | `RussiaVehicle9K720` | موشک بالستیک | 1600 | 20.0 |
| 13 | **خالی** | — | — | خالی | — | — |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

همهٔ Objectهای این منو در BIG وجود دارند.

---

## Iraq — `Iraq_WarFactoryCommandSet_T3`

ساختمان: `Iraq_WarFactory_T` — `Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini`  
این منو **عربی الایانس نیست**.

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | T-72A obr.1984 | `Command_ConstructIraq_T-72` | `Iraq_T-72` | تانک | 1000 | 16.0 |
| 2 | BMP-1 | `Command_ConstructIraq_BMP-1` | `Iraq_BMP-1` | نفربر | 600 | 13.0 |
| 3 | BMP-2k | `Command_ConstructIraq_BMP-2` | `Iraq_BMP-2` | نفربر | 650 | 13.0 |
| 4 | BTR-90 | `Command_ConstructIraq_BTR-90` | `Iraq_BTR-90` | نفربر | 800 | 12.0 |
| 5 | 2S1 SPG | `Command_ConstructIraq_2S1` | `Iraq_2S1` | توپخانه | 1800 | 16.0 |
| 6 | Sam-8 OSA | `Command_ConstructIraq_Sam8` | `Iraq_Sam8` | پدافند | 1200 | 12.0 |
| 7 | AssadBabel-2 MBT | `Command_ConstructIraq_AssadBabel-2` | `Iraq_AssadBabel-2` | تانک | 1300 | 18.0 |
| 8 | SA-6 | `Command_ConstructIraq_SA-6` | `Iraq_SA-6` | پدافند | 1000 | 15.0 |
| 9 | B-340 Radar | `Command_ConstructIraqVehicleB340` | `IraqVehicleB340` | رادار | 1200 | 14.0 |
| 10 | Karrar-2 | `Command_ConstructIraq_Karrar2` | `Iraq_Karrar2` | تانک | 2200 | 30 |
| 11 | Roland-3K | `Command_ConstructIraqVehicleRoland3K` | `IraqVehicleRoland3K` | پدافند | 900 | 10.0 |
| 12 | Fahad-3 TEL | `Command_ConstructIraqVehicleFahad3` | `IraqVehicleFahad3` | پرتابگر موشک | 2000 | 15.0 |
| 13 | **خالی** | — | — | خالی | — | — |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

همهٔ Objectهای پر در BIG وجود دارند.

---

## Iran — `IranWarfactoryCommandSet`

ساختمان: `IranWarFactory` — `Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini`

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | MBT Karrar | `Command_ConstructIranTankKarrar` | `IranTankKarrar` | تانک | 1200 | 15.0 |
| 2 | Z-3 MBT | `Command_ConstructIranTankZ3MBT` | `IranTankZ3MBT` | تانک | 1000 | 13.0 |
| 3 | Raad SPG | `Command_ConstructIranVehicleRaadSPG` | `IranVehicleRaadSPG` | توپخانه | 1600 | 20.0 |
| 4 | BMP-1A | `Command_ConstructIranVehicleBMP1A` | `IranVehicleBMP1A` | نفربر | 600 | 13.0 |
| 5 | BMP-2 | `Command_ConstructIranVehicleBMP2` | `IranVehicleBMP2` | نفربر | 650 | 13.0 |
| 6 | Tor-1M | `Command_ConstructIranTankTor1M` | `IranTankTor1M` | پدافند | 1400 | 10.0 |
| 7 | BM-21 Grad | `Command_ConstructIranVehicleBM21` | `IranVehicleBM21` | راکت‌انداز | 750 | 11.0 |
| 8 | Fatheh - 313 | `Command_ConstructIranVehicleFateh313` | `IranVehicleFateh313` | موشک بالستیک | 1000 | 15.0 |
| 9 | **خالی** | — | — | خالی | — | — |
| 10 | Fattah MSRBM | `Command_ConstructIranVehicleFattah` | `IranVehicleFattah` | موشک بالستیک | 1000 | 15.0 |
| 11 | Shahed-136 Mobile Launcher | `Command_ConstructIranVehicleShahedLauncher` | `IranVehicleShahedLauncher` | پرتابگر پهپاد | 1500 | 15.0 |
| 12 | Pantsir-S1M | `Command_ConstructIranVehiclePantsirS1M` | `IranVehiclePantsirS1M` | پدافند | 1500 | 12.0 |
| 13 | Raad-M2EK | `Command_ConstructIranRaadM2EK` | `IranRaadM2EK` | توپخانه | 1000 | 15.0 |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

اسلات ۹ در DATA زنده خالی است (`Command_ConstructIranVehicleKhormshar` در این CommandSet نیست).

---

## Israel — `AirF_AmericaWarFactoryCommandSet`

کشور زنده در کمبو: **Israel Defence Forces** (`FactionAmericaAirForceGeneral`).  
ساختمان: `AirF_AmericaWarFactory` — `Data\INI\Object\Specter\Israel Defense Forces\Buildings\Warfactory.ini`

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | Merkava MK4 | `Command_ConstructIsrael_MerkavaMk4` | `Israel_MerkavaMk4` | تانک | 800 | 17.0 |
| 2 | M270 MRLS | `AirF_Command_ConstructAmericaVehicleTomahawk` | `AirF_AmericaVehicleTomahawk` | راکت‌انداز | 1000 | 15.0 |
| 3 | Plasan Mrap | `AirF_Command_ConstructAmericaVehicleHumvee` | `AirF_AmericaVehicleHumvee` | خودرو | 600 | 10.0 |
| 4 | PULS TBM | `AirF_Command_ConstructAmericaVehicleMedic` | `AirF_AmericaVehicleMedic` | پرتابگر موشک | 1000 | 15.0 |
| 5 | M109A6 | `Command_ConstructIsrael_M109A6` | `Israel_M109A6` | توپخانه | 1200 | 16.0 |
| 6 | Eitan MGS | `AirF_Command_ConstructAmericaVehicleSentryDrone` | `AirF_AmericaVehicleSentryDrone` | نفربر | 700 | 10.0 |
| 7 | Namer AAA | `AirF_Command_ConstructAmericaVehicleAvenger` | `AirF_AmericaTankAvenger` | پدافند | 720 | 12.0 |
| 8 | Namer IFV | `AirF_Command_ConstructAmericaVehicleMicrowave` | `AirF_AmericaTankMicrowave` | نفربر پدافندی | 900 | 13.0 |
| 9 | Arrow AAM Launcher | `Command_ConstructIsrael_Arrow` | `Israel_Arrow` | پدافند | 3200 | 23.0 |
| 10 | AN/TPY2 Radar | `Command_ConstructIsrael_AN_TPY2` | `Israel_AN_TPY2` | رادار پدافند (کلون AN/TPY-2 آمریکا) | 2600 | 15.0 |
| 11 | *(کلید CSF موجود نیست)* `CONTROLBAR:ConstructIsraelVehicleEitanAFV` | `Command_ConstructIsraelVehicleEitanAFV` | `IsraelVehicleEitanAFV` | نفربر | 700 | 10.0 |
| 12 | **خالی** | — | — | خالی | — | — |
| 13 | Rally Point | `Command_SetRallyPoint` | — | نقطه تجمع | — | — |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

اسلات ۱۰ کلون رادار قدرتمند آمریکایی است، ولی روی منوی اسرائیل. اسلات ۱۱ Object دارد؛ فقط رشته CSF خالی است.

---

## Spain — War Factory اختصاصی ندارد

| اسلات | نام دکمه | CommandButton | Object | نوع | قیمت | زمان |
|---:|---|---|---|---|---|---|
| 1 | **خالی** | — | — | خالی | — | — |
| 2 | **خالی** | — | — | خالی | — | — |
| 3 | **خالی** | — | — | خالی | — | — |
| 4 | **خالی** | — | — | خالی | — | — |
| 5 | **خالی** | — | — | خالی | — | — |
| 6 | **خالی** | — | — | خالی | — | — |
| 7 | **خالی** | — | — | خالی | — | — |
| 8 | **خالی** | — | — | خالی | — | — |
| 9 | **خالی** | — | — | خالی | — | — |
| 10 | **خالی** | — | — | خالی | — | — |
| 11 | **خالی** | — | — | خالی | — | — |
| 12 | **خالی** | — | — | خالی | — | — |
| 13 | **خالی** | — | — | خالی | — | — |
| 14 | **خالی** | — | — | خالی | — | — |

باقی‌ماندهٔ اسپانیا: `Spain_MissileFactory` + `Spain_MissileFactoryCommandSet` (خارج از این ممیزی). منوی NATO در پیوست است و کشور اسپانیا نیست.

---

## Arabic Alliance — `Arb_WarFactoryCommandSet_T3`

باقی‌مانده در DATA؛ از کمبو اسکرمیش/MP مخفی است. با عراق یکی نیست.

ساختمان: `ArabicArmy_WarFactory` — `Data\INI\Object\Specter\Arabic Alliance\Buildings\Warfactory.ini`

| اسلات | نام دکمه (CSF) | CommandButton | Object | نوع | قیمت | زمان (ث) |
|---:|---|---|---|---|---:|---:|
| 1 | T-90S Algerian Version | `Command_ConstructGLATankScorpion` | `GLATankScorpion` | تانک | 1200 | 15.0 |
| 2 | Oshkosh M-ATV | `Command_ConstructGLAVehicleTechnical` | `GLAVehicleTechnical` | خودرو | 800 | 8.0 |
| 3 | Tor1M | `Command_ConstructArab_Tor1M` | `Arab_Tor1M` | پدافند | 1100 | 10.0 |
| 4 | *(کلید CSF موجود نیست)* `CONTROLBAR:ConstructArabVehicleJiny` | `Command_ConstructArabVehicleJiny` | `ArabVehicleJiny` | خودرو | 1200 | 12.0 |
| 5 | BMP-3M | `Command_ConstructGLAVehicleToxinTruck` | `GLAVehicleToxinTruck` | نفربر | 1200 | 12.0 |
| 6 | M-109A7 155mm Artillary | `Command_ConstructGLAVehicleRocketBuggy` | `GLAVehicleRocketBuggy` | توپخانه (برچسب) / Object باگی | 1200 | 16.0 |
| 7 | M1A2 Abrams | `Command_ConstructGLATankMarauder` | `GLATankMarauder` | تانک | 950 | 18.0 |
| 8 | M2A3 Bradley | `Command_ConstructGLAVehicleCombatBike` | `GLAVehicleCombatBike` | نفربر (برچسب) / Object باگی | 1800 | 16.0 |
| 9 | Iskander M | `Command_ConstructGLAVehicleScudLauncher` | `GLAVehicleScudLauncher` | موشک بالستیک | 1600 | 17.0 |
| 10 | Pantsir S1 | `Command_ConstructArb_Pantsir` | `Arb_Pantsir` | پدافند | 900 | 10.0 |
| 11 | BM30 Smerch | `Command_ConstructArb_bm30` | `ArabicArmy_Bm30` | راکت‌انداز | 1200 | 16.0 |
| 12 | 30N6E Mobile Radar | `Command_ConstructArb_30N6E` | `Arb_30N6E` | رادار پدافند | 1200 | 14.0 |
| 13 | S-300PMU2 Grumble | `Command_ConstructArb_S300` | `Arabic_S300PMU2` | پدافند | 2000 | 15.0 |
| 14 | Krasukha 4E | `Command_ConstructArab_Krasukha-4` | `Arab_Krasukha-4` | جنگ الکترونیک | 5000 | 25 |

چند دکمه GLA هنوز Object قدیمی دارند ولی TextLabel/Cameo به تجهیز ناتو/آمریکا عوض شده (اسلات‌های ۲، ۵، ۶، ۷، ۸). Objectها موجودند؛ نام دیده‌شده با شناسه Object یکی نیست. Sell داخل ۱۴ اسلات نیست (اسلات ۱۷).

---

## جدول مقایسه‌ای اسلات ۱–۱۴

سلول‌ها نام دیده‌شده بازیکن‌اند. `خالی` یعنی آن شماره در CommandSet نهایی دکمه ندارد.

| اسلات | America | China | Russia | Iraq | Iran | Israel | Spain | Arabic Alliance |
|---:|---|---|---|---|---|---|---|---|
| 1 | M1A2Sepv1 | ZTZ99A2 MBT | T-90A MBT | T-72A obr.1984 | MBT Karrar | Merkava MK4 | خالی | T-90S Algerian Version |
| 2 | M1128 Stryker MGS | AFT-10 | T-72B3 | BMP-1 | Z-3 MBT | M270 MRLS | خالی | Oshkosh M-ATV (Object=Technical) |
| 3 | M-1296 APC | DF-17 TEL | BM-30 Smerch | BMP-2k | Raad SPG | Plasan Mrap | خالی | Tor1M |
| 4 | Oshkosh M-ATV (Object=SentryDrone) | **خالی** | Krasukha-4 | BTR-90 | BMP-1A | PULS TBM | خالی | Jiny (CSF ندارد) |
| 5 | M270 MLRS | Tor-M2 | 2S-19M2 MSTA-S | 2S1 SPG | BMP-2 | M109A6 | خالی | BMP-3M (Object=ToxinTruck) |
| 6 | M-109A7 | PGZ-04 | BMP3M IFV | Sam-8 OSA | Tor-1M | Eitan MGS | خالی | M-109A7 (Object=RocketBuggy) |
| 7 | M-6 Linebacker | **خالی** | Tor-M2M | AssadBabel-2 MBT | BM-21 Grad | Namer AAA | خالی | M1A2 Abrams (Object=Marauder) |
| 8 | M2A3 BUSKIII (Object=Microwave) | PHL-03 MLRS | Pantsir-S1M | SA-6 | Fateh-313 | Namer IFV | خالی | M2A3 Bradley (Object=CombatBike) |
| 9 | **AN/TPY-2** | PLZ-05 | 92N6E Radar | B-340 Radar | **خالی** | Arrow | خالی | Iskander M |
| 10 | **THAAD** | DF-21C | S-400 TEL | Karrar-2 | Fattah MSRBM | AN/TPY2 (کلون USA) | خالی | Pantsir S1 |
| 11 | M-142 HIMARS | ZBD-04 IFV | Tos-1A | Roland-3K | Shahed-136 Launcher | Eitan AFV (CSF ندارد) | خالی | BM30 Smerch |
| 12 | M1075I UGM133 | HT-233 Radar | 9K720 Iskander-M | Fahad-3 TEL | Pantsir-S1M | **خالی** | خالی | 30N6E Radar |
| 13 | M1075T BGM-109 | DF-12 TBML | **خالی** | **خالی** | Raad-M2EK | Rally Point | خالی | S-300PMU2 |
| 14 | Sell | HQ-9B TEL | Sell | Sell | Sell | Sell | خالی | Krasukha 4E |

---

## پدافند قدرتمند آمریکا روی War Factory

| کشور | اسلات | تجهیز دیده‌شده | Object |
|---|---:|---|---|
| America | 9 | AN/TPY-2 Mobile Radar System | `US_AN_TPY2` — $2600 / 15s |
| America | 10 | THAAD Air Defense System | `US_THAAD` — $3000 / 22s |
| Israel (IDF / AirF) | 10 | AN/TPY2 Radar | `Israel_AN_TPY2` — $2600 / 15s (کلون، نه ساختمان آمریکا) |

اسلات ۷ آمریکا (Linebacker/Avenger) و ۸ (برچسب M2A3 / Object Microwave) پدافند معمولی‌اند، نه رده THAAD/TPY-2.

---

## Object اشتباه یا ناموجود

| مسیر | مشکل |
|---|---|
| `RussiaWarFactory_T` / `RussiaWarFactoryCommandSet_T3` (ساخته نمی‌شود) | تقریباً همه دکمه‌های روسی با نام خط‌تیره به Object ناموجود وصل‌اند |
| `Israel_WarFactory` + Integrity CS (ساخته نمی‌شود) | `Command_ConstructIsrael_AD_Barak8` و `Command_ConstructIsrael_AD_IronDome` در CommandButton نیستند |
| Israel اسلات ۱۱ زنده | Object `IsraelVehicleEitanAFV` موجود است؛ کلید CSF نیست — بازیکن کلید خام را می‌بیند |
| AA اسلات ۴ | Object `ArabVehicleJiny` موجود است؛ کلید CSF نیست |
| AA اسلات‌های ۲/۵/۶/۷/۸ | Object قدیمی GLA باقی است؛ برچسب CSF به تجهیز دیگر اشاره می‌کند |
| China اسلات ۴ و ۷ | خالی (عمدی در CS زنده) |
| Iran اسلات ۹ | خالی (Khormshar در CS زنده نیست) |
| Spain | هیچ Object/دکمه War Factory اسپانیایی |

دکمه `Command_ConstructNNatoVehicleM142ATACMS` (N اضافه) مربوط به NATO است و به `ItalyVehicleM142ATACMS` وصل است — روی منوی اسپانیا نیست.

---

## پیوست — NATO War Factory (اسپانیا نیست)

فقط برای مرجع. بولدوزر ناتو این ساختمان را می‌سازد؛ `FactionNato` = NATO Armies.  
CommandSet: `NatoWarfactoryCommandSet` در `CommandSet.ini`.  
Object: `NatoWarFactory`، Side=Nato.

| اسلات | نام دکمه | CommandButton | Object | نوع | قیمت | زمان |
|---:|---|---|---|---|---:|---:|
| 1 | Leopard 2A7+ | `Command_ConstructNatoTankLeopard2A7Plus` | `NatoTankLeopard2A7Plus` | تانک | 2000 | 15.0 |
| 2 | PUMA IFV | `Command_ConstructNatoTankPuma` | `NatoTankPuma` | نفربر | 950 | 17.0 |
| 3 | Cortale - MK3 | `Command_ConstructNatoVehicleCortaleMK3` | `NatoVehicleCortaleMK3` | خودرو | 1200 | 12.0 |
| 4 | VBCI APC | `Command_ConstructNatoVehicleVBCI` | `NatoVehicleVBCI` | نفربر | 700 | 12.0 |
| 5 | M-142 HIMARS | `Command_ConstructNatoVehicleM142` | `NatoVehicleM142` | راکت‌انداز | 1200 | 18.0 |
| 6 | Caesar 155mm SPG | `Command_ConstructNatoVehicleCaesar` | `NatoVehicleCaesar` | توپخانه | 1200 | 16.0 |
| 7 | Centauro-B2 | `Command_ConstructNatoVehicleCentauroB2` | `NatoVehicleCentauroB2` | تانک چرخ‌دار | 900 | 12.0 |
| 8 | IRIS-T SLX | `Command_ConstructNatoVehicleIRIST` | `NatoVehicleIRIST` | پدافند | 1700 | 22.0 |
| 9 | TRML-4D | `Command_ConstructNatoVehicleTRML4D` | `NatoVehicleTRML4D` | رادار | 2200 | 12.0 |
| 10 | M-142 ATACMS | `Command_ConstructNNatoVehicleM142ATACMS` | `ItalyVehicleM142ATACMS` | موشک | 1600 | 20.0 |
| 11 | خالی | — | — | خالی | — | — |
| 12 | خالی | — | — | خالی | — | — |
| 13 | خالی | — | — | خالی | — | — |
| 14 | Sell | `Command_Sell` | — | فروش | — | — |

---

## روش و محدودیت

1. نصب‌کننده `SPECTER_S300_RADAR_DRONES_INSTALL.zip` از ریلیز `s300-radar-drones` خوانده شد (فقط استخراج موقت زیر `/tmp`؛ داخل مخزن کپی نشد).
2. همه `CommandSet*.ini` و `CommandButton*.ini` ریشه `Data\INI` به ترتیب الفبایی last-win شدند.
3. Object زنده هر کشور از دکمه Construct بولدوزر/کارگر last-win به‌دست آمد، نه از نام فایل.
4. اسلات ۱–۱۴ همان کلیدهای عددی CommandSet هستند.
5. بازی Zero Hour برای تأیید چیدمان کنترل‌بار اجرا نشده است.

هیچ فایل بازی در این کار ویرایش نشده است.
