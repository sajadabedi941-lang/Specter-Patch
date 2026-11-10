# Iran empty command panel — CommandSet.ini membership

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` در این محیط نیستند. ترتیب overwrite مسیر `CommandSet.ini` بین `_SPEC_DATA_ONE.big` و `INIZH.big` اینجا قابل dump نیست. تست داخل بازی انجام نشده است.

## وضعیت انتشار

| | وضعیت |
| --- | --- |
| `origin/main` | commitهای «Add files via upload»؛ PRهای #706–#708 merge نشده‌اند |
| Release نصب‌شده کاربر | `iran-missile-fire-buttons` / PR #708، SHA `bbbc60c7d39b37cef7c82e11b96e95f322e7b9fe7b2674660c02575f5584c81e` |
| INIZH.big | در ریپو و در این VM نیست |

`Launch_Specter.bat` فقط `_SPEC_DATA_ONE.big` و `_SPEC_ART_ONE.big` را کنار `generals.exe` می‌گذارد. فهرست ASCII کامل BIGهای پوشهٔ بازی اینجا موجود نیست.

## علت اثبات‌شده (از خود BIG شماره ۷۰۸)

زنجیرهٔ استخراج‌شده از آرشیو منتشرشده:

| Object (first-win داخل BIG) | CommandSet روی Object | آیا همان نام در `Data\INI\CommandSet.ini` هست؟ |
| --- | --- | --- |
| تمام ۱۹ موشک ایران (خرمشهر، Shahed، Fateh، Fattah، BM-21، Hoveyzeh، A–J، …) | `IranMissileFireCommandSet` / `IranKhorramshahrFireCommandSet` / `IranShahed136FireCommandSet` | **خیر** |
| `IranWarFactory` (ساخت کار می‌کند) | `IranWarfactoryCommandSet` | **بله** |
| `Iran_MissileFactory` | `Iran_MissileFactoryCommandSet` | **بله** |
| `IranVehicleDozer` | `IranDozerCommandSet` | **بله** |

نام‌های Fire فقط در `CommandSet_IranMissiles.ini` و `CommandSet_ZZZZ_ZzzIranMissileFire.ini` بودند. وجود در فایل extra / source کافی نیست.

شواهد مشترک پنل کاملاً خالی: بعد از #708 هر موشک ایران از `Scud_B`/`Smerch` (که داخل `CommandSet.ini` هستند) جدا شد و به نامی اشاره کرد که در `CommandSet.ini` نیست. ساختمان‌هایی که نوار فرمان دارند همان فایل را می‌خوانند.

`INIZH.big` اینجا نیست؛ حدس last-win/first-win آن مسیر زده نمی‌شود. شکاف empirically: عضویت در `CommandSet.ini` ↔ نوار دیده می‌شود.

دکمه‌های اسلات ۱/۱۲/۱۳/۱۴ همان `Command_FireMainWeapon` / `AttackMove` / `Guard` / `Stop` داخل `CommandButton.ini` هستند (اسلات ۱–۱۴ ControlBar). مشکل نام دکمه نبود؛ مشکل **غیاب خود CommandSet در فایل مؤثر** بود.

## اصلاح

فقط سه مسیر داخل همان BIG:

1. چهار CommandSet یکتا به **انتهای** `Data\INI\CommandSet.ini` اضافه شد (همان فایل `IranWarfactoryCommandSet`).
2. `CommandSet_IranMissiles.ini` به دو بلوک قبلی (Dozer / Factory) برگشت تا نام جدید تکرار نشود.
3. `CommandSet_ZZZZ_ZzzIranMissileFire.ini` فقط توضیح است.

Objectها، سلاح‌ها، Prerequisites، زمان ۱۰ث خرمشهر، برد ۳۰۰۰ Shahed، `Scud_B` روسیه/عراق، ART: بدون تغییر.

در برابر #708 فقط همان سه مسیر فرق دارد.

## اعتبارسنجی ایستا روی BIG جدید

- هر ۱۹ Object موشک → نام CS داخل `CommandSet.ini`
- هر دکمهٔ آن CS در `CommandButton.ini` موجود است؛ اسلات‌ها ۱–۱۴
- هر نام CS فقط یک‌بار تعریف شده
- Iskander همچنان `Scud_B_CommandSet`
- قفل Upgrade همچنان باز؛ کارخانه فقط `IranSupplyCenter`

داخل ZH: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 | ورودی |
| --- | ---: | --- | ---: |
| `_SPEC_DATA_ONE.big` | 374 011 625 | `46aab7d5c9433471a545935e2f922949d85130de287e44da3d13772a18c604cc` | 3576 |

## نصب

فقط همین `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `46aab7d5…` شود. ART را عوض نکنید.

جایگزین کنید (هم‌زمان نگذارید): `iran-missile-fire-buttons`، `iran-missiles-unlock-shahed-fire`، `iran-khorramshahr-shahed136`، `rs24-df41-factory-complete`.
