# حذف RS-24 / DF-41 / خرمشهر فقط از War Factory روسیه، چین، ایران

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## Object / CommandSet زنده (حدس زده نشد)

منبع: `_SPEC_DATA_ONE.big` ریلیز `radar-shahed-range` (SHA `e2b32682…`). ControlBar فقط `Data\INI\CommandSet.ini` را می‌خواند.

| کشور | Object زنده WF | CommandSet | دکمهٔ حذف‌شده |
| --- | --- | --- | --- |
| روسیه | `RussiaWarFactory` → `Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini` | `RussiaWarFactoryCommandSet` | اسلات ۱۳ `Command_ConstructRussiaVehicleRS24` (`RussiaVehicleRS24`) |
| چین | `ChinaWarFactory` → `Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini` | `PLAWarFactoryCommandSet` | اسلات ۴ و ۷ `Command_ConstructChinaVehicleDF41`؛ اسلات ۱۵ `Command_ConstructChinaVehicleDF41_AI` |
| ایران | `IranWarFactory` → `Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini` | `IranWarfactoryCommandSet` | اسلات ۹ `Command_ConstructIranVehicleKhormshar`؛ اسلات ۱۵ `Command_ConstructIranVehicleKhormshar_AI` |

`RussiaWarFactory_T` زنده است ولی اسلات RS-24 آن از قبل کامنت بوده. `ChinaWarFactory-bk` / `Infa_ChinaWarFactory` DF-41 ندارند. `IranExpandedHQCommandSet` HQ است نه WF؛ خرمشهر آنجا ماند.

تنها فایل تغییرکرده در BIG: `Data\INI\CommandSet.ini`. اسلات‌های باقی‌مانده شماره‌شان عوض نشد (حفره مجاز است؛ مثل CSهای موجود SPECTER). هر سه CS بعد از حذف هنوز ۱۳–۱۴ دکمه دارند و `End` دارند.

## Missile Factory حفظ شد

`CB_FACTORY_SLOT_K/L/M/N` روی کارخانهٔ موشکی روسیه / چین / ایران و عراق (`CB_MISSILE_A`…`K` + L/M/N) دست‌نخورده است. Objectهای `Factory_RS24YarsOnce` / `Factory_DF41Once` / `Factory_KhormsharOnce` و سلاح‌ها حذف نشدند. CommandButtonها ماندند تا از Missile Factory ساخته شوند.

عراق: هیچ `CB_MISSILE_*` به WF روسیه/چین/ایران نرفت.

## CommandSetهایی که تغییر کردند

فقط این سه:

1. `PLAWarFactoryCommandSet` — ۱۴ اسلات باقی (DF-17، Tor، PGZ، PHL، PLZ، DF-21C، ZBD، HT233، DF-12، HQ-9، …)
2. `IranWarfactoryCommandSet` — ۱۳ اسلات باقی (Karrar، Fateh، Fattah، Shahed، Sell، …)
3. `RussiaWarFactoryCommandSet` — ۱۳ اسلات باقی (T-90، 9K720، S-400، Sell، …)

سایر ~۱۱۵۰ CommandSet از جمله Missile Factory، Iraq A–N، #710 Iran fire، #666 رادار Shahed بدون تغییر بایت‌اند.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374079939 | `a41168def32528d84d28879e077adcc1eb27ff3a02cc96b20fa15da05b3b465f` |
| `CommandSet.ini` | 453927 | `32bf182ad2f701b86eba5b95d9a2a1ebc4ae8472fcd59bc01e949bbacbd628d9` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

ART عوض نشد. CommandButton.ini همان overlay #714 است. #710–#717 (ایران fire، Shahed برد ۳۰۰۰، کارخانه K/L/M/N، سقف پدافند) در DATA مانده‌اند.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید (لازم؛ ControlBar اول همین مسیر را می‌خواند).
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید.
4. ART را عوض نکنید.

یا `Install_WfRemoveRs24Df41Khormshar.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

در WF روسیه/چین/ایران دکمهٔ RS-24 / DF-41 / خرمشهر نباشد؛ بقیهٔ نوار ساخت بماند؛ همان سه موشک در Missile Factory اسلات L/M/N ساخته شوند. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
