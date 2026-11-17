# Iraq Spy Satellite (real remaining path) + four Supply Centres

منبع DATA: Release `iraq-radar-spy-satellite-fix` (`70454ee1…`, 373 955 619 بایت).  
`main` همچنان `aac7ffc1` است و PRهای قبلی ادغام نشده‌اند.  
فقط `_SPEC_DATA_ONE.big` بازسازی شد.

**تست داخل بازی انجام نشده است.**

## Spy Satellite روی رادار عراق

رادار/مینی‌مپ در تست کاربر درست شد؛ `RadarUpgrade { TriggeredBy = Upgrade_AmericaRadar }` حفظ شد.

**علت ریشه‌ای باقی‌ماندن Spy Sat:** پارس CommandSet در SAGE اسلات‌ها را روی همان شیء موجود **ادغام** می‌کند، کل مجموعه را جایگزین نمی‌کند. فایل Last-Win قبلی اسلات ۱ و ۲ را حذف کرد، نه بازنویسی. بنابراین `CommandSet_ZZZZ_SpySatelliteRadar.ini` همچنان نگه داشت:

- اسلات ۱ = `Command_SpySatelliteScan`
- اسلات ۲ = `Command_SpecterSpySatelliteFee`

ماژول‌های Object قبلاً جدا شده بودند؛ دکمه از ادغام CommandSet می‌آمد. `Command_IraqiRadarSearch` هم همان Spy Sat است (`SSSpySat` / `SPECIAL_SPY_SATELLITE`).

**اصلاح:** در `CommandSet_ZZZZ_ZZZIraqRadar.ini` اسلات ۱ و ۲ صریحاً بازنویسی شدند (Camo / MTS). `Command_IraqiRadarSearch` Last-Win شد به `STOP` تا اگر اسلات باقی‌مانده‌ای به آن اشاره کند دیگر Spy Sat نباشد. Object رادار و TriggeredBy دست نخورده‌اند. CommandSet کشورهای دیگر همان Spy Sat را دارند.

## Supply Centre چهار کشور

PR #694 فقط دکمه خرید را Last-Win کرد. Object مؤثر `*SupplyCenter` (مسیر مشترک با overlay) هنوز `SpawnBehavior` واحد **سمت اشتباه** می‌ساخت؛ همان واحدی که با ساخت ساختمان خارج می‌شود.

| کشور | واحد طراحی‌شده | چرا | علت قبلی | اصلاح |
|---|---|---|---|---|
| France | `FranceHelicopterCH47F` | ChinookAIUpdate + HARVESTER، الگوی NATO CH47F | Spawn = `AmericaVehicleChinook` (Side=America) | Spawn = CH47F فرانسه؛ خرید همان دکمه |
| America | `AmericaSupplyChinook_USA` | ChinookAIUpdate MaxBoxes=40، طراحی overlay | Spawn = `AmericaVehicleChinook` (نه واحد overlay) | Spawn + خرید Chinook overlay |
| China | `ChinaVehicleSupplyTruck` | SupplyTruckAIUpdate + HARVESTER، Side=China | Spawn درست بود؛ ظرفیت SPEC چهار جعبه | Spawn حفظ؛ Object overlay (۳۸ جعبه) Last-Win |
| Russia | `RussiaSupplyTruck_CountryIncome` | SupplyTruckAIUpdate + HARVESTER، Side=Russia | Spawn = کامیون چین؛ Mi-8 در لیست خرید HARVESTER نیست | Spawn = کامیون روسیه؛ اسلات ۲ Mi-8 بازنویسی شد |

هر چهار ساختمان Last-Win در `zzzzz_SpecterSupplyCentreBuy` Dock + Exit + ProductionUpdate دارند.

## BIG

| فایل | حجم | SHA-256 |
|---|---|---|
| این بازسازی `_SPEC_DATA_ONE.big` | 373 991 918 | `45250b1a7dd68e0ea5d6d79945066d69bfb8ced5d26371dc07d768b59ab09ee3` |

ورودی‌ها: 3563 → 3568. ART تغییر نکرد.
