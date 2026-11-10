# سقف ساخت Air Defence: حداکثر ۳ از هر نوع برای هر بازیکن

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## سازوکار (موجود در همین پروژه / موتور ZH)

فیلد زندهٔ محدودیت تعداد، `MaxSimultaneousOfType` است. در SPECTER همین فیلد برای هواپیماهای نخبه، سایت‌های NASAMS/SAMP/T، S-500 و مجموعهٔ `Patch_AirDefense` استفاده شده.

رفتار موتور (نه فیلد حدسی):

- شمارش **به‌ازای هر بازیکن** است؛ پدافند بازیکن دیگر سهمیه را مصرف نمی‌کند.
- واحدهای زنده **و در حال ساخت** با هم شمرده می‌شوند؛ چند کارخانه / صف همزمان سقف را دور نمی‌زنند.
- فروش یا نابودی شمارنده را کم می‌کند؛ ساخت مجدد تا سقف ۳ دوباره مجاز است.
- `MaxSimultaneousLinkKey = Patch_AirDefense` قبلاً ده‌ها نوع را در **یک استخر مشترک ۱۰تایی** جمع می‌کرد. آن کلید از همهٔ Objectهای پوشش‌داده‌شده برداشته شد تا سقف **۳ از هر نوع** باشد، نه ۳ پدافند در مجموع.

سلاح، برد، قدرت، قیمت، ارتقا و رهگیری عوض نشدند. فقط `MaxSimultaneousOfType` و حذف `Patch_AirDefense` اعمال شد.

## مسیرهای ساخت بررسی‌شده

| مسیر | نتیجه |
| --- | --- |
| `CommandButton` / `UNIT_BUILD` | سقف روی خود Object است |
| `CommandButton` / `DOZER_CONSTRUCT` (سایت SAM/NASAMS/SAMP/T/Bavar/S-400) | همان Object؛ سقف اعمال شد |
| `CommandSet.ini` زنده (#710/#714) | بدون تغییر |
| `ObjectCreationList` `CreateObject` | هیچ CreateObject به نام‌های انتخاب‌شده نیست |
| اسکریپت INI | فایل اسکریپت در این BIG نیست |
| `SPECIAL_POWER_CONSTRUCT` | فقط تونل Sneak Attack؛ AD نیست |
| دکمه‌های ژنرال‌های وانیل ZH (SupW/Lazr/Boss/Demo/…) | Object در این BIG تعریف نشده؛ قابل پچ نیست |

اسپانیا در این BIG هیچ Object پدافندی قابل‌ساخت ندارد (فقط کارخانهٔ موشکی و TELهای تهاجمی). اگر از آنلاک EU5 استفاده کند، `Specter_EU5_IRIST` و `Specter_EU5_TRML4D` سقف ۳ دارند.

`BritainVehicleStormShadowTEL` و `ItalyVehicleStormShadowTEL` TEL کروز هستند، نه AD؛ سقف قبلی ۱۰ آن‌ها دست‌نخورده ماند.

## پوشش ایستا

- **۲۴۸ Object** / **۳۰ Side** / **۲۰۲ فایل Object** / **۲۷۸ بلوک** (همهٔ تعریف‌های هر نام، نه فقط first-win)
- منبع: `_SPEC_DATA_ONE.big` ریلیز `df41-factory-ballistic` (SHA `5b7ee5c6…`)
- `CommandSet.ini` / `CommandButton.ini` / `Weapon.ini` بایت‌به‌بایت همان #714/#715
- `Factory_DF41Once` / `Factory_RS24YarsOnce` / `Factory_KhormsharOnce` بدون تغییر
- پس از پچ: هر ۲۴۸ نام `MaxSimultaneousOfType = 3` و هیچ `Patch_AirDefense` باقی نماند
- `BuildCost` و `KindOf` first-win بدون تغییر

سقف‌های قبلی روی همین مجموعه: بدون سقف ۱۶۱، ۱۰×۵۷، ۴×۹، ۳×۱۸، ۶×۱ (`IranVehicleMajid`)، ۲×۲ (`RussiaVehicleS500`, `Iraq_MIC_S500`). همه به ۳ رسیدند.

## کشورها / Sideها و Objectها

فهرست کامل با مسیر first-win در `AD_MAX_THREE_INVENTORY.tsv` است.

| Side | تعداد | Objectها |
| --- | ---: | --- |
| America | 9 | AmericaInfantryMarinesStinger, AmericaMobileSamSiteMIM104F, AmericaPatriotBattery, AmericaTankAvenger, AmericaVehicleM1126_M1_Shorad, America_MIM104F, US_AN_TPY2, US_THAAD, US_THAAD_Site_AI |
| Britain | 9 | BritainDroneMantisWingman, BritainIRISTSamSite, BritainMantis, BritainNASAMSIII, BritainSAMPTNG, BritainVehicleCortaleMK3, BritainVehicleIRIST, BritainVehicleStormer, BritainVehicleTRML4D |
| China | 8 | ChinaGattlingCannon, ChinaTankGattling, ChinaTankPGZ04, ChinaTankTorM2, ChinaVehicleHQ9, ChinaVehicleHT233, China_Hq9_Site, RussiaInfantryIgla |
| ChinaInfantryGeneral | 1 | Infa_ChinaGattlingCannon |
| ChinaTankGeneral | 1 | Infa_ChinaTankGattling |
| Egypt | 6 | Egypt_AD_MD, Egypt_AD_SAM, Egypt_AD_SHORAD, Egypt_Sam2, Egypt_VehicleRoland3K, Egypt_ZSU-23-4 |
| France | 9 | FranceDroneMantisWingman, FranceIRISTSamSite, FranceMantis, FranceNASAMSIII, FranceSAMPTNG, FranceVehicleCortaleMK3, FranceVehicleIRIST, FranceVehicleSAMPT, FranceVehicleTRML4D |
| GLA (ائتلاف عربی + کپی‌های مصر با Side=GLA) | 13 | Arab_Tor1M, Arabic_S300PMU2, Arabic_StingerSoldier, Arb_30N6E, Arb_Pantsir, Arb_S300PMU2AI_Installation, EgyptIRISTSamSite, EgyptVehicle9K317, EgyptVehicle9S19M2, EgyptVehicleS300VM, GLAStingerSite, GLAStingerSiteNoHole, GLAVehicleQuadCannon |
| GLAStealthGeneral | 2 | Slth_GLAStingerSite, Slth_GLAVehicleQuadCannon |
| Germany | 9 | GermanyDroneMantisWingman, GermanyIRISTSamSite, GermanyMantis, GermanyNASAMSIII, GermanySAMPTNG, GermanyVehicleCortaleMK3, GermanyVehicleIRIST, GermanyVehicleTRML, GermanyVehicleTRML4D |
| India | 9 | India_AD_AntiDrone, India_AD_MD, India_AD_SAM, India_AD_SHORAD, India_CRAM, India_RepublicanGuardIgla, India_Sam2, India_VehicleRoland3K, India_ZSU-23-4 |
| Iran | 10 | IranBavarSiteAI, IranKhordad15SamSite, IranRaadM2EK, IranTankTor1M, IranVehicleMajid, IranVehiclePantsirS1M, IranVehicleRaadBaran, IranVehicleRaadSPG, Iran_Bavar, Iran_Meraj |
| Iraq | 23 | IraqFahad3SamSite, IraqVehicleB340, IraqVehicleFahad3, IraqVehicleRoland3K, Iraq_DefenseSite, Iraq_MIC_92N6R, Iraq_MIC_96L6TSP, Iraq_MIC_AN_TPY2, Iraq_MIC_Arrow, Iraq_MIC_HQ9, Iraq_MIC_HT233, Iraq_MIC_IRIST, Iraq_MIC_PantsirS1M, Iraq_MIC_S400, Iraq_MIC_S500, Iraq_MIC_THAAD, Iraq_MIC_TRML4D, Iraq_MIC_US_AN_TPY2, Iraq_RepublicanGuardIgla, Iraq_SA-6, Iraq_Sam2, Iraq_Sam8, Iraq_ZSU-23-4 |
| Israel | 7 | AirF_AmericaPatriotBattery, AirF_AmericaTankAvenger, IsraelInfantryStingerSoldier, Israel_AD_Barak8, Israel_AD_IronDome, Israel_AN_TPY2, Israel_Arrow |
| Italy | 9 | ItalyDroneMantisWingman, ItalyIRISTSamSite, ItalyMantis, ItalyNASAMSIII, ItalySAMPTNG, ItalyVehicleCortaleMK3, ItalyVehicleIRIST, ItalyVehicleSAMPT, ItalyVehicleTRML4D |
| Japan | 4 | Japan_CRAM, Japan_DefenseSite, Japan_Hq9_Site, Japan_Sam2 |
| Libya | 9 | Libya_AD_AntiDrone, Libya_AD_MD, Libya_AD_SAM, Libya_AD_SHORAD, Libya_CRAM, Libya_RepublicanGuardIgla, Libya_Sam2, Libya_VehicleRoland3K, Libya_ZSU-23-4 |
| Nato | 8 | NatoDroneMantisWingman, NatoIRISTSamSite, NatoMantis, NatoNASAMSIII, NatoSAMPTNG, NatoVehicleCortaleMK3, NatoVehicleIRIST, NatoVehicleTRML4D |
| NorthKorea | 4 | NorthKorea_CRAM, NorthKorea_DefenseSite, NorthKorea_Hq9_Site, NorthKorea_Sam2 |
| Pakistan | 10 | PakistanVehicleHQ9P, Pakistan_AD_AntiDrone, Pakistan_AD_MD, Pakistan_AD_SAM, Pakistan_AD_SHORAD, Pakistan_CRAM, Pakistan_RepublicanGuardIgla, Pakistan_Sam2, Pakistan_VehicleRoland3K, Pakistan_ZSU-23-4 |
| Russia | 10 | RussiaS400Site_AI, RussiaTankTorM2M, RussiaVehicle55K6E, RussiaVehicle92N6R, RussiaVehicle96L6TSP, RussiaVehicle9K317, RussiaVehiclePantsirS1M, RussiaVehicleS400, RussiaVehicleS500, Russia_92N6R |
| SaudiArabia | 12 | SaudiArabiaVehicleAvenger, SaudiArabiaVehiclePatriot, SaudiArabiaVehiclePatriotBtry, SaudiArabia_AD_AntiDrone, SaudiArabia_AD_MD, SaudiArabia_AD_SAM, SaudiArabia_AD_SHORAD, SaudiArabia_CRAM, SaudiArabia_RepublicanGuardIgla, SaudiArabia_Sam2, SaudiArabia_VehicleRoland3K, SaudiArabia_ZSU-23-4 |
| SouthAfrica | 9 | SouthAfrica_AD_AntiDrone, SouthAfrica_AD_MD, SouthAfrica_AD_SAM, SouthAfrica_AD_SHORAD, SouthAfrica_CRAM, SouthAfrica_RepublicanGuardIgla, SouthAfrica_Sam2, SouthAfrica_VehicleRoland3K, SouthAfrica_ZSU-23-4 |
| SouthKorea | 4 | SouthKorea_CRAM, SouthKorea_DefenseSite, SouthKorea_Hq9_Site, SouthKorea_Sam2 |
| Sweden | 8 | SwedenDroneMantisWingman, SwedenIRISTSamSite, SwedenMantis, SwedenNASAMSIII, SwedenSAMPTNG, SwedenVehicleCortaleMK3, SwedenVehicleIRIST, SwedenVehicleTRML4D |
| Syria | 9 | Syria_AD_AntiDrone, Syria_AD_MD, Syria_AD_SAM, Syria_AD_SHORAD, Syria_CRAM, Syria_RepublicanGuardIgla, Syria_Sam2, Syria_VehicleRoland3K, Syria_ZSU-23-4 |
| Turkey | 10 | TurkeyDroneMantisWingman, TurkeyIRISTSamSite, TurkeyMantis, TurkeyNASAMSIII, TurkeySAMPTNG, TurkeyVehicleCortaleMK3, TurkeyVehicleHisar, TurkeyVehicleIRIST, TurkeyVehicleKorkut, TurkeyVehicleTRML4D |
| UAE | 11 | UAEVehiclePantsir, UAEVehiclePatriot, UAE_AD_AntiDrone, UAE_AD_MD, UAE_AD_SAM, UAE_AD_SHORAD, UAE_CRAM, UAE_RepublicanGuardIgla, UAE_Sam2, UAE_VehicleRoland3K, UAE_ZSU-23-4 |
| Ukraine | 10 | Specter_EU5_IRIST, Specter_EU5_TRML4D, UkraineDroneMantisWingman, UkraineIRISTSamSite, UkraineMantis, UkraineNASAMSIII, UkraineSAMPTNG, UkraineVehicleCortaleMK3, UkraineVehicleIRIST, UkraineVehicleTRML4D |
| Vietnam | 5 | VietnamVehicleS300, Vietnam_CRAM, Vietnam_DefenseSite, Vietnam_Hq9_Site, Vietnam_Sam2 |
| Spain | 0 | هیچ Object پدافندی در این BIG نیست |

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374080209 | `8728a24c3856850ff4d958b0b4d15dd443da13f299306fd16e57ea10f6432628` |
| `CommandSet.ini` | 454198 | `405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

ART عوض نشد. overlay شل CommandSet/CommandButton همان #714 است.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید.
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید.
4. ART را عوض نکنید.

یا `Install_ADMaxThree.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

هر بازیکن از هر نوع پدافند حداکثر ۳ عدد بتواند داشته باشد (زنده + در صف). فروش/نابودی سهمیه را برگرداند. بازیکن دوم سقف بازیکن اول را مصرف نکند. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
