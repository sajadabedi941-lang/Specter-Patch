# Iran missile Fire buttons — stock Command_FireMainWeapon

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` اینجا نیستند. اعتبارسنجی فقط ایستا است. ادعای تست داخل بازی نمی‌شود.

منبع DATA: Release `iran-missiles-unlock-shahed-fire` / PR #707
(SHA `b9b7317ea6e346bc45544287c3fbcc5b96693a2c82019500d72044cd024eb915`).

قفل Upgrade همان pack است و اینجا دوباره دست نخورده ماند.

## علت ناپدید شدن Fire

مقایسه با لانچر سالم `RussiaVehicle9K720` (`GenericUpgradableArtillaryCommandSet` اسلات ۱ = `Command_FireMainWeapon` از `CommandButton.ini`).

| واحد بعد از #707 | CommandSet زنده | اسلات Fire | آیا دکمه در CommandButton.ini هست؟ |
| --- | --- | --- | --- |
| خرمشهر / Shahed | `IranKhorramshahrFireCommandSet` / `IranShahed136FireCommandSet` فقط در extra | `Command_IranFireSecondary` / `Command_IranFirePrimary` | **خیر** — فقط در `CommandButton_ZZZZ_ZzzIranMissileFire.ini` |
| Fateh / Fattah / TELهای A–J | `Scud_B_CommandSet` فقط در `CommandSet.ini` | `Command_FireMainWeapon` | بله، ولی خود CS مسیر STOCK است و INIZH می‌تواند first-win کند |
| BM-21 / Hoveyzeh | `Smerch_CommandSet` فقط در `CommandSet.ini` | همان | همان ریسک STOCK |

`CommandButton.ini` و `CommandSet.ini` مسیر STOCK هستند. INIZH first-win آن فایل‌ها را می‌گیرد. نام دکمهٔ extra که در `CommandButton.ini` نیست روی ControlBar ظاهر نمی‌شود. خرمشهر علاوه بر این سلاح `Khormshar1_ICBM` را روی **SECONDARY** داشت؛ حتی `Command_FireMainWeapon` (PRIMARY) آن را شلیک نمی‌کرد.

الگوی سالم SPECTER (۹K720 / Fateh طراحی): اسلات ۱ = `Command_FireMainWeapon`، سلاح PRIMARY، `NEED_TARGET_POS` + `DeployStyleAIUpdate`.

## اصلاح

- CommandSetهای یکتای ایران فقط به دکمه‌های موجود در `CommandButton.ini` وصل شدند: `Command_FireMainWeapon`، `Command_AttackMove`، `Command_Guard`، `Command_Stop`.
- همان تعریف‌ها به `CommandSet_IranMissiles.ini` (فایل extra شناخته‌شده ایران، الگوی مصر) هم اضافه شد.
- Object هر موشک ایران از `Scud_B` / `Smerch` جدا شد و به CS یکتای خودش اشاره می‌کند. `Scud_B_CommandSet` روسیه/عراق دست نخورد.
- خرمشهر: `Khormshar1_ICBM` روی PRIMARY (first-win و overlay). نام سلاح، آسیب، مدل عوض نشد.
- Shahed: همان سلاح/پرتابه بالستیک برد ۳۰۰۰.
- Prerequisites خالی، `BuildTime` خرمشهر ۱۰ث، کارخانه فقط `IranSupplyCenter`.

`Command_IranFirePrimary` / `Command_IranFireSecondary` دیگر مرجع نیستند.

## دکمه‌ها قبل / بعد

| واحد | قبل (علت نبود Fire) | CommandSet بعد | سلاح PRIMARY |
| --- | --- | --- | --- |
| Fateh-313 | `Scud_B` فقط در CommandSet.ini | `IranMissileFireCommandSet` | `2x_SRBM_Fateh313_HE` |
| خرمشهر | دکمه extra ناموجود + سلاح SECONDARY | `IranKhorramshahrFireCommandSet` | `Khormshar1_ICBM` |
| Fattah | `Scud_B` STOCK | `IranMissileFireCommandSet` | `2x_SRSSBM_Fattah` |
| Shahed-136 | `Command_IranFirePrimary` extra | `IranShahed136FireCommandSet` | `Weapon_Iran_Shahed136Launcher` برد ۳۰۰۰ |
| BM-21 | `Smerch` STOCK | `IranMissileFireCommandSet` | `122mm_M21OF_Grad_Semi` |
| Hoveyzeh | `Smerch` STOCK | `IranMissileFireCommandSet` | `2x_MRGLCM_Hoveyzeh` |
| Dezful Penetrator / Zolfaghar-M / Fattah-2 | `Scud_B` STOCK | `IranMissileFireCommandSet` | همان سلاح قبلی |
| Hormuz…Simorgh (A–J) | `Scud_B` STOCK | `IranMissileFireCommandSet` | همان `Weapon_Iran_*` |

هر چهار نام CS: اسلات ۱ Fire، ۱۲ AttackMove، ۱۳ Guard، ۱۴ Stop — مثل ۹K720.

## ایستا در برابر بازی

ایستا: هر Object به CS یکتا با `Command_FireMainWeapon`؛ هر دکمه در `CommandButton.ini` موجود است؛ سلاح PRIMARY؛ قفل Upgrade همچنان باز؛ Iskander/AlAbbas همچنان `Scud_B`؛ ART نیست.

داخل ZH: **اجرا نشد.** ظاهر شدن Fire، فعال بودن، و شلیک واقعی باید در بازی تأیید شود.

## BIG

| فایل | حجم | SHA-256 | ورودی |
| --- | ---: | --- | ---: |
| `_SPEC_DATA_ONE.big` | 374 012 466 | `bbbc60c7d39b37cef7c82e11b96e95f322e7b9fe7b2674660c02575f5584c81e` | 3576 |

## نصب

فقط این `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `bbbc60c7…` شود. ART را عوض نکنید.

جایگزین کنید (هم‌زمان نگه ندارید): `iran-missiles-unlock-shahed-fire`، `iran-khorramshahr-shahed136`، `rs24-df41-factory-complete`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
