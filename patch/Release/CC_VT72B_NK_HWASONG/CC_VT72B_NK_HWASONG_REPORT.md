# Command Center: فقط VT72B (ژاپن/ویتنام/کره جنوبی) و VT72B+Hwasong15BB (کره شمالی)

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## مسیر زنده

ControlBar فقط `Data\INI\CommandSet.ini` را باز می‌کند. فایل loose بر هر BIG می‌برد. `game.dat` فهرست `*.big` را با `_stricmp` مرتب می‌کند و اولین بایگانی مالک مسیر را نگه می‌دارد.

منبع: `_SPEC_DATA_ONE.big` ریلیز `radar-no-spy-sat` (SHA `64835645cb60fe726b59d8033574823d5de4443aa9dff0f74c1f7978d3d67465`، ۳۵۷۹ ورودی).

هر چهار CommandSet نام یکتا دارند (یک تعریف در `CommandSet.ini`؛ هیچ `CommandSet_*.ini` دیگری آن‌ها را بازنویسی نمی‌کند). CommandSet مشترک نبود؛ نسخهٔ مستقل ساخته نشد.

| کشور | Object Command Center زنده | CommandSet |
| --- | --- | --- |
| ژاپن | `Japan_CommandCenter` | `Japan_CommandCenterCommandSet` |
| ویتنام | `Vietnam_CommandCenter` | `Vietnam_CommandCenterCommandSet` |
| کره جنوبی | `SouthKorea_CommandCenter` | `SouthKorea_CommandCenterCommandSet` |
| کره شمالی | `NorthKorea_CommandCenter` | `NorthKorea_CommandCenterCommandSet` |

## VT72B و موشک — از DATA زنده، حدس زده نشد

| کشور | دکمه | Object |
| --- | --- | --- |
| ژاپن | `Command_ConstructJapan_VT72B` | `Japan_VT72B` |
| ویتنام | `Command_ConstructVietnam_VT72B` | `Vietnam_VT72B` |
| کره جنوبی | `Command_ConstructSouthKorea_VT72B` | `SouthKorea_VT72B` |
| کره شمالی | `Command_ConstructNorthKorea_VT72B` | `NorthKorea_VT72B` |
| کره شمالی | `Command_ConstructNorthKorea_Hwasong15BB` اسلات ۷ | `NorthKorea_Hwasong15BB` (`ButtonImage = pla_df41`) |

`DF_41` / `ChinaVehicleDF41` / `Factory_DF41Once` روی هیچ‌کدام از این چهار Command Center نیستند. گزینهٔ موشکی زندهٔ منوی کره شمالی `Hwasong15BB` است؛ موشک جدید ساخته نشد.

## قبل → بعد

اسلات‌های باقی‌مانده شماره‌شان عوض نشد. `SetRallyPoint` (۱۳) و `Sell` (۱۴) تولید واحد نیستند و ماندند تا نوار فرمان Command Center خالی/غیرقابل‌فروش نشود. واحد جدید اضافه نشد.

### ژاپن — `Japan_CommandCenterCommandSet`

| اسلات | قبل | بعد |
| ---: | --- | --- |
| 1 | `Command_ConstructJapan_VT72B` | **ماند** |
| 2 | `Command_ConstructJapanFinal_M2020` | حذف |
| 3 | `Command_ConstructJapanFinal_Chonma5` | حذف |
| 4 | `Command_ConstructJapanReal_M1985` | حذف |
| 5 | `Command_ConstructJapanReal_Hwasong5` | حذف |
| 6 | `Command_ConstructJapanReal_KN23` | حذف |
| 7 | `Command_ConstructJapan_Hwasong15BB` | حذف |
| 8 | `Command_ConstructJapanFinal_M1992SPAAG` | حذف |
| 9 | `Command_ConstructJapanFinal_Pongae3` | حذف |
| 10 | `Command_ConstructJapanFinal_Pongae5` | حذف |
| 11 | `Command_ConstructJapanFinal_KN06` | حذف |
| 12 | `Command_ConstructJapanFinal_Pongae6ABM` | حذف |
| 13 | `Command_SetRallyPoint` | ماند (غیرتولیدی) |
| 14 | `Command_Sell` | ماند (غیرتولیدی) |
| 15 | `Command_ConstructJapanFinal_Saetbyol4` | حذف |
| 16 | `Command_ConstructJapanFinal_Kumsong3` | حذف |
| 17 | `Command_ConstructJapanFinal_Bulsae4` | حذف |
| 18 | `Command_ConstructJapanReal_Songun915` | حذف |

### ویتنام — `Vietnam_CommandCenterCommandSet`

همان الگوی ژاپن با پیشوند `Vietnam` / `VietnamFinal` / `VietnamReal`. بعد: اسلات ۱ `Command_ConstructVietnam_VT72B`، ۱۳ Rally، ۱۴ Sell.

### کره جنوبی — `SouthKorea_CommandCenterCommandSet`

همان الگو با پیشوند `SouthKorea`. بعد: اسلات ۱ `Command_ConstructSouthKorea_VT72B`، ۱۳ Rally، ۱۴ Sell.

### کره شمالی — `NorthKorea_CommandCenterCommandSet`

| اسلات | قبل | بعد |
| ---: | --- | --- |
| 1 | `Command_ConstructNorthKorea_VT72B` | **ماند** |
| 2 | `Command_ConstructNKFinal_M2020` | حذف |
| 3 | `Command_ConstructNKFinal_Chonma5` | حذف |
| 4 | `Command_ConstructNorthKoreaReal_M1985` | حذف |
| 5 | `Command_ConstructNorthKoreaReal_Hwasong5` | حذف |
| 6 | `Command_ConstructNorthKoreaReal_KN23` | حذف |
| 7 | `Command_ConstructNorthKorea_Hwasong15BB` | **ماند** (موشک زندهٔ منو؛ DF-41 نیست) |
| 8–12، ۱۵–۱۸ | SPAAG / Pongae / KN06 / Saetbyol / Kumsong / Bulsae / Songun915 | حذف |
| 13 | `Command_SetRallyPoint` | ماند |
| 14 | `Command_Sell` | ماند |

## دست‌نخورده

War Factory / Missile Factory / Supply Center / رادار این چهار کشور، Command Center عراق و بقیه، `CommandButton.ini`، Objectهای VT72B و `NorthKorea_Hwasong15BB`، قیمت/سلاح/مدل، کارخانه K/L/M/N، #710–#719.

تنها فایل تغییرکرده در BIG: `Data\INI\CommandSet.ini`.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075020 | `52baa018c53015e90bf55b1451a33d22cad9de0951b4924168287129eeb2144a` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

ART عوض نشد.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید (لازم؛ ControlBar اول همین مسیر loose را می‌خواند).
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید.
4. ART را عوض نکنید.

یا `Install_CcVt72bNkHwasong.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

Command Center ژاپن/ویتنام/کره جنوبی فقط VT72B (+ Rally/Sell) نشان بدهد؛ کره شمالی VT72B و Hwasong15BB. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
