# حذف Spy Satellite از رادار کشورهای غیرمجاز

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## علت بازگشت دکمه

تنها اصلاح ادغام‌شدهٔ قبلی PR **#682** (۱۵ اکتبر ۲۰۲۶، `0_SPECTER_NoGeneralSpySatellite.big`) بود: دکمهٔ عمومی `Command_SpySatelliteScan` از هر منوی نصب‌شده برداشته شد. Overlay با نام `0_` قبل از `_SPEC_DATA_ONE.big` و `INIZH.big` first-win می‌شد.

ریلیزهای **#710 تا #718** یک `CommandSet.ini` کامل SPECTER (نسب #657/#666) را هم به‌صورت loose و هم داخل `_SPEC_DATA_ONE.big` فرستادند. ControlBar فقط `Data\INI\CommandSet.ini` را باز می‌کند؛ فایل loose بر هر BIG می‌برد. Overlay #682 در مسیر نصب فعلی نیست، پس همان `Command_SpySatelliteScan` اسلات ۱ دوباره first-win شد.

`Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini` داخل BIG همان overlay #657 است (Spy Sat + Fee روی ۲۵ رادار، از جمله ایران و عراق). ControlBar این فایل را نمی‌خواند؛ برای اینکه last-win/ادغام اسلات نتواند دکمه را برگرداند، خطوط Spy Sat/Fee آن هم حذف شد.

`generals.exe` / `INIZH.big` روی این VM نیستند. مسیر ثابت‌شده از `game.dat` (#682/#710): فهرست `*.big` با `_stricmp`، آرگومان جایگزینی `0`، اولین بایگانی مالک مسیر می‌ماند. موتور برای نوار فرمان فقط این نام را باز می‌کند: `Data\INI\CommandSet.ini`.

منبع زنده: `_SPEC_DATA_ONE.big` ریلیز `wf-remove-rs24-df41-khormshar` (SHA `a41168def32528d84d28879e077adcc1eb27ff3a02cc96b20fa15da05b3b465f`، ۳۵۷۹ ورودی).

## قبل → بعد (Object رادار زنده / CommandSet / دکمه)

فقط اسلات Spy Sat حذف شد. پهپادها، Sell، اسلات ۹–۱۲ (#666/#717)، RadarSearch کشوری، و میانبرهای Command Center دست‌نخورده‌اند. اسلات‌ها شماره‌گذاری مجدد نشدند.

### حذف شد — `Command_SpySatelliteScan` اسلات ۱

| کشور | Object رادار زنده | CommandSet | قبل | بعد |
| --- | --- | --- | --- | --- |
| آمریکا | `AmericaRadarStation` و `AmericaRadarMPQ65ST` | `AmericaRadarStationCommandSet` | ۱ = Spy Sat؛ ۲–۷ پهپاد؛ ۱۴ Sell | همان بدون اسلات ۱ |
| اسرائیل | `IsraelBuildingRadarStation` | `IsraelRadarStationCommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۱۴ Sell | همان بدون اسلات ۱ |
| روسیه | `Russia91N6E` (Side=China در فایل) | `RussiaRadarStationCommandSet` | ۱ = Spy Sat؛ ۲/۴/۶ پهپاد؛ ۱۴ Sell | همان بدون اسلات ۱ |
| چین | `ChinaRadarYj26` | `ChinaRadarStationCommandSet` | ۱ = Spy Sat؛ ۲–۹/۱۵ پهپاد؛ ۱۴ Sell | همان بدون اسلات ۱ |
| ناتو | `NatoRadarGM406` | `NatoGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۱۴ Sell | همان بدون اسلات ۱ |
| بریتانیا | `BritainRadarGM406` | `BritainGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| فرانسه | `FranceRadarGM406` | `FranceGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| آلمان | `GermanyRadarGM406` | `GermanyGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| ایتالیا | `ItalyRadarGM406` | `ItalyGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| سوئد | `SwedenRadarGM406` | `SwedenGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| اوکراین | `UkraineRadarGM406` | `UkraineGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |
| ترکیه | `TurkeyRadarGM406` | `TurkeyGM406CommandSet` | ۱ = Spy Sat؛ ۲–۶ پهپاد؛ ۹–۱۲ UAV؛ ۱۴ Sell | همان بدون اسلات ۱ |

#682 برای آمریکا/اسرائیل `Command_AmericaCountryScan` / `Command_IsraelCountryScan` می‌گذاشت. آن دکمه‌ها در `CommandButton.ini` زنده (#714) تعریف نشده‌اند و اضافه کردن‌شان گزینهٔ جدید است. طبق «فقط دکمهٔ Spy Satellite» فقط خط Spy Sat حذف شد؛ CountryScan اضافه نشد.

#680 جستجوی رادار ترکیه را نگه می‌داشت. روی CS زندهٔ فعلی `Command_TurkishRadarSearch` نیست؛ اضافه نشد.

### استثناهای طراحی‌شده — نگه داشته شد

| کشور | Object زنده | CommandSet | دکمهٔ اسلات ۱ | دلیل |
| --- | --- | --- | --- | --- |
| کره شمالی | `NorthKorea_RadarStation` | `NorthKorea_RadarStationCommandSet` | `Command_NorthKoreaRadarSearch` | جستجوی کشوری؛ Spy Sat نیست. #682/#680 نگه داشتند. #657 آن را به Spy Sat برده بود و بعداً برگشت. |
| کره جنوبی | `SouthKorea_RadarStation` | `SouthKorea_RadarStationCommandSet` | `Command_SouthKoreaRadarSearch` | همان |
| ژاپن | `Japan_RadarStation` | `Japan_RadarStationCommandSet` | `Command_JapanRadarSearch` | همان |
| ویتنام | `Vietnam_RadarStation` | `Vietnam_RadarStationCommandSet` | `Command_VietnamRadarSearch` | همان |

هیچ کشور زنده‌ای طبق #682 اجازهٔ دکمهٔ عمومی Spy Sat روی رادار را ندارد. استثنای واقعی همان RadarSearch کشوری است، نه `Command_SpySatelliteScan`.

### از قبل بدون Spy Sat روی جدول زندهٔ ControlBar (دست‌نخورده)

| کشور | Object زنده | CommandSet | وضعیت |
| --- | --- | --- | --- |
| ایران | `IranRadarStation` | `IranExpandedRadarCommandSet` | پهپاد ۱–۱۲ + Sell؛ Spy Sat ندارد |
| عراق | `Iraq_RadarStation` | `Iraq_RadarStationCommandSet` | استتار/MTS/پهپاد + ۹–۱۲؛ #696 `IraqiRadarSearch` را هم برداشت چون خودش Spy Sat بود |
| اتحاد عربی | `ArabicArmy59N6E` | `ArabRadarStationCommandSet` | پهپاد + Sell |
| هند | `India_RadarStation` | `India_RadarCommandSet` | پهپاد + ۹–۱۲ + Sell |
| لیبی | `Libya_RadarStation` | `Libya_RadarCommandSet` | Sell + ۹–۱۲ |
| پاکستان | `Pakistan_RadarStation` | `Pakistan_RadarCommandSet` | Sell + ۹–۱۲ |
| عربستان | `SaudiArabia_RadarStation` | `SaudiArabia_RadarCommandSet` | پهپاد + ۹–۱۲ + Sell |
| آفریقای جنوبی | `SouthAfrica_RadarStation` | `SouthAfrica_RadarCommandSet` | Sell + ۹–۱۲ |
| سوریه | `Syria_RadarStation` | `Syria_RadarCommandSet` | Sell + ۹–۱۲ |
| امارات | `UAE_RadarStation` | `UAE_RadarCommandSet` | Sell + ۹–۱۲ |

`IranRadarStationCommandSet` در `CommandSet.ini` هست ولی Object زنده به `IranExpandedRadarCommandSet` اشاره می‌کند. هر دو بدون Spy Sat ماندند.

### خارج از محدوده / بدون منوی رادار

- **مصر:** `Egypt_RadarStation` → `Egypt_RadarCommandSet` که در `CommandSet.ini` زنده تعریف نشده (جدول ControlBar ندارد). Spy Sat نیست.
- **اسرائیل ثانویه:** `Israel_RadarStation` هم به همان `Egypt_RadarCommandSet` گم‌شده اشاره می‌کند. رادار قابل‌بازی اسرائیل `IsraelBuildingRadarStation` است.
- **اسپانیا:** Object رادار ساختمانی در DATA زنده نیست.
- **GM406R / SAM / AN-TPY-2 / 92N6:** `CommandSet = None` — منوی رادار نیستند.
- **میانبر Command Center ژنرال** (`SpecialPowerShortcutUSA` و AirF/SupW/Lazr): `Command_SpySatelliteScan` / `FromShortcut` ماند؛ کاربر فقط رادار کشورها را خواست.

## فایل‌های تغییرکرده در BIG

1. `Data\INI\CommandSet.ini` — ۱۲ CS راداری بالا.
2. `Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini` — همهٔ خطوط `Command_SpySatelliteScan` و `Command_SpecterSpySatelliteFee` (۲۵ بلوک). ControlBar نمی‌خواندش.

`CommandButton.ini`، `Weapon.ini`، Objectها (از جمله `RadarUpgrade` / GrantUpgrade / Shahed UAV)، کارخانهٔ موشکی، و WF #718 بایت‌به‌بایت همان‌اند.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374077708 | `64835645cb60fe726b59d8033574823d5de4443aa9dff0f74c1f7978d3d67465` |
| `CommandSet.ini` | 453515 | `2af068adeb95042efb665dfcd9f65d9898e8333ded25f49687535586dcaece84` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

ART عوض نشد. CommandButton.ini همان overlay #714 است.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید (لازم؛ ControlBar اول همین مسیر loose را می‌خواند و بر INIZH / SPEC / `0_` می‌برد).
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید.
4. ART را عوض نکنید.
5. اگر `0_SPECTER_NoGeneralSpySatellite.big` یا `zz_SPECTER_NoGeneralSpySatellite.big` کنار exe مانده، لازم نیست؛ loose `CommandSet.ini` بر آن‌ها می‌برد. برای جلوگیری از first-win یک جدول قدیمی، overlay `0_` را برندارید مگر جدولش همین نسخه باشد.

یا `Install_RadarNoSpySat.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

روی رادار ۱۲ کشور جدول اول دکمهٔ Spy Satellite نباشد؛ RadarSearch کره/ژاپن/ویتنام بماند؛ پهپادها و اسلات ۹–۱۲ و Sell بمانند؛ مینی‌مپ/RadarUpgrade ایران و عراق و بقیه همان باشد. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
