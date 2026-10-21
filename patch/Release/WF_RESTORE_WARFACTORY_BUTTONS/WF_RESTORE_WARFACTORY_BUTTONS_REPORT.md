# Restore seven War Factory production bars

**بازی اجرا نشد.** Zero Hour در این محیط نیست. ادعای تست داخل بازی نمی‌شود.

## علت خالی بودن نوار (شواهد فایل)

Release `wf-fix-commandset-crash` (SHA `1411c9aa…`) ساختمان‌ها را به نام‌های یکتا بست:

`CommandSet = SaudiArabia_WarFactoryCommandSet_NoSarab` (و معادل شش کشور دیگر)

این نام‌ها **فقط** در `Data\INI\CommandSet_ZZZZ_ZZZZZWfDetach.ini` بودند.

انتقال متن به آن فایل اثبات بارگذاری نیست:

1. مسیر زندهٔ CommandSet بازی `Data\INI\CommandSet.ini` است. `INIZH.big` این مسیر را اول ثبت می‌کند؛ overlay همان مسیر در SPEC خوانده نمی‌شود یا تعریف اول می‌ماند.
2. فایل‌های اضافهٔ `CommandSet_ZZZZ_*.ini` نام‌های **جدید** را به نوار فرمان وصل نمی‌کنند. همان الگوی Supply Centre با `*_CountryIncome` است: نام در Object هست، در جدول زنده نیست، نوار خالی است.
3. تعریف دوبارهٔ نام‌های موجود در `CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini` هم نوار داخل بازی را عوض نکرد (Release `wf-remove-sarab7-9p117-alabbas`).
4. بلوک CommandSet داخل `Object\` Crash می‌دهد؛ آن مسیر بسته ماند.

کارخانهٔ عربستان به نام اشتباه اشاره نکرده بود. نام `_NoSarab` از نظر charset معتبر است، ولی در جدولی که موتور برای نوار ساخت می‌خواند وجود ندارد.

## اصلاح محدود

نه فایل overlay از DATA قابل نصب حذف شد. منبع معتبر مقایسه: `HT233_92N6E_TPY2_CUE/_SPEC_DATA_ONE.big` (آخرین DATA قبل از overlayهای خالی‌کننده). پس از حذف، مجموعه و بایت هر ورودی با آن منبع یکی است.

Objectهای `*_WarFactory_T` دوباره `CommandSet = *_WarFactoryCommandSet` دارند؛ آن نام‌ها داخل packed `CommandSet.ini` هستند و هر دکمه در `CommandButton.ini` وجود دارد. بلوک CommandSet داخل Object INI گذاشته نشد. Missile Factory، Supply Centre، DataLink رادار، و کارخانه‌های دیگر دست نخورده ماندند.

## زنجیرهٔ هر کشور (استاتیک روی BIG نهایی)

همه ۱۴ دکمه. اسلات ۱۴ = `Command_Sell`. هیچ اسلات خالی در تعریف زنده نیست.

### عربستان — `SaudiArabia_WarFactory_T`

- Object نهایی: `Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini`
- `CommandSet = SaudiArabia_WarFactoryCommandSet`
- تعریف زنده: `Data\INI\CommandSet.ini` (۱۴ دکمه)

| اسلات | فرمان |
| ---: | --- |
| 1 | `Command_ConstructIraq_T-72` |
| 2 | `Command_ConstructIraq_BMP-1` |
| 3 | `Command_ConstructIraq_BMP-2` |
| 4 | `Command_ConstructIraq_BTR-90` |
| 5 | `Command_ConstructIraq_2S1` |
| 6 | `Command_ConstructIraq_Sam8` |
| 7 | `Command_ConstructIraq_AssadBabel-2` |
| 8 | `Command_ConstructIraq_SA-6` |
| 9 | `Command_ConstructIraq_Sarab7` |
| 10 | `Command_ConstructIraq_Alhussaien` |
| 11 | `Command_ConstructIraqVehicleRoland3K` |
| 12 | `Command_ConstructIraq_BM-21` |
| 13 | `Command_ConstructIraq_R11ScudB` |
| 14 | `Command_Sell` |

UAE / Syria / SouthAfrica / Libya همان ۱۴ فرمان را روی `*_WarFactoryCommandSet` خود دارند. Object هر کدام در پوشهٔ Specter همان کشور است، نه overlay `zzzzz_SpecterWfRemoveSarab`.

### هند — `India_WarFactory_T`

- Object: `…\Indian Armed Forces\Buildings\India_WarFactory.ini`
- `CommandSet = India_WarFactoryCommandSet` در `CommandSet.ini` (۱۴ دکمه)

| اسلات | فرمان |
| ---: | --- |
| 1 | `Command_ConstructAmericaTankCrusader` |
| 2 | `Command_ConstructAmericaVehicleM1128` |
| 3 | `Command_ConstructAmericaVehicleM1296` |
| 4 | `Command_ConstructAmericaVehicleSentryDrone` |
| 5 | `Command_ConstructAmericaVehicleTomahawk` |
| 6 | `Command_ConstructAmericaTankM109A7` |
| 7 | `Command_ConstructAmericaVehicleAvenger` |
| 8 | `Command_ConstructAmericaVehicleMicrowave` |
| 9 | `Command_ConstructAmericaVehicleAN_TPY2` |
| 10 | `Command_ConstructAmericaVehicleTHAAD` |
| 11 | `Command_ConstructAmericaVehicleM142` |
| 12 | `Command_ConstructAmericaVehicleM1075I` |
| 13 | `Command_ConstructAmericaVehicleM1075T` |
| 14 | `Command_Sell` |

پاکستان همان ۱۴ فرمان را روی `Pakistan_WarFactoryCommandSet` در `CommandSet.ini` دارد. `CommandSet_Pakistan.ini` یک تعریف بعدی روسیه دارد؛ نوار زنده همان تعریف `CommandSet.ini` است (اول بارگذاری‌شده).

## اعتبارسنجی

- هیچ مسیر `zzzzz_SpecterWfRemoveSarab` یا `CommandSet_ZZZZ_ZZZZZWfDetach.ini` در BIG نیست.
- نام `_NoSarab` دیگر تعریف نشده.
- هر هفت Object به نام موجود در `CommandSet.ini` اشاره می‌کند.
- هر ۱۴ دکمه در `CommandButton.ini` موجود است.
- ورودی‌ها و محتوا با `HT233_92N6E_TPY2_CUE` یکی است.
- تست داخل بازی: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 008 909 | `242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d` |

این SHA با Release `ht233-92n6e-tpy2-cue` یکی است، چون اصلاح همان حذف overlayهای بعدی است. این فایل **همان** `wf-fix-commandset-crash` / `wf-detach` / `wf-remove` نیست.

## نصب

فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید.

هم‌زمان نصب نکنید:

- `_SPEC_DATA_ONE.big` از `wf-fix-commandset-crash` (نوار خالی)
- `_SPEC_DATA_ONE.big` از `wf-detach-sarab7-9p117-alabbas` (Crash)
- `_SPEC_DATA_ONE.big` از `wf-remove-sarab7-9p117-alabbas`

ART و `0_SPECTER_*` را نگه دارید.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
