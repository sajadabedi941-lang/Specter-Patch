# War Factory: detach seven countries from leftover Sarab7 / 9P117 / AlAbbas

**تست داخل بازی اجرا نشده است.** این Release جایگزین `wf-remove-sarab7-9p117-alabbas` است؛ آن فایل را دوباره نصب نکنید.

## علت دقیق شکست پچ قبلی

Release قبلی (`87901f52` / `wf-remove-sarab7-9p117-alabbas`) فایل `CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini` را به DATA اضافه کرد و همان نام‌های موجود را دوباره تعریف کرد:

`SaudiArabia_WarFactoryCommandSet` و معادل‌های UAE / Syria / SouthAfrica / Libya / India / Pakistan.

اسکن استاتیک ما این فایل را Last-Win حساب می‌کرد. بازی این‌طور کار نمی‌کند.

1. ساختمان واقعی هر کشور `*_WarFactory_T` است و `CommandSet = *_WarFactoryCommandSet` دارد.
2. همان نام‌ها از قبل در `Data\INI\CommandSet.ini` تعریف شده‌اند. `INIZH.big` مسیر `CommandSet.ini` را اول ثبت می‌کند (`overwrite=FALSE`)؛ نسخهٔ SPEC از همان مسیر خوانده نمی‌شود یا تعریف اول همان نام باقی می‌ماند.
3. تعریف دوبارهٔ **همان نام** در فایل `CommandSet_*.ini` بعدی نوار ساخت داخل بازی را عوض نمی‌کند. اسلات ۹ = `Command_ConstructIraq_Sarab7` و اسلات ۱۳ = `Command_ConstructIraq_R11ScudB` (۹P۱۱۷) روی تعریف اول می‌مانند.
4. `AlAbbas` روی این War Factoryها `CB_MISSILE_D` نبود؛ اگر در بازی دیده می‌شد از همان نوار تعریف‌اول / سامانهٔ موشکی بود، نه از فایل اضافه.

فایل قبلی داخل BIG بود و SHA آن درست بود. مشکل نصب ناقص نبود؛ مسیر فعال ساختمان عوض نشده بود.

## اصلاح این Release

Object folder حتماً parse می‌شود. هر هفت `*_WarFactory_T` Last-Win شدند و به **نام CommandSet جدید** وصل شدند که هرگز در `CommandSet.ini` نبوده است. اسلات‌های ۹ و ۱۳ روی نوار عراقی با واحد معتبر همان کشور بازنویسی شدند (AlKhalid / CombatDrone)، بدون تکرار دکمه.

Object / Weapon / دکمهٔ ساخت / Missile Factory / عراق دست‌نخورده ماند.

فقط `_SPEC_DATA_ONE.big` لازم است. ART و overlay لازم نیست.

## نتیجه هر کشور

| کشور | Object واقعی | CommandSet فعال | اسلات اصلاح‌شده | Sarab7 | 9P117 | AlAbbas |
| --- | --- | --- | --- | --- | --- | --- |
| عربستان | `SaudiArabia_WarFactory_T` | `SaudiArabia_WarFactoryCommandSet_NoSarab` | ۹ → AlKhalid، ۱۳ → CombatDrone | خیر | خیر | خیر |
| امارات | `UAE_WarFactory_T` | `UAE_WarFactoryCommandSet_NoSarab` | ۹ → AlKhalid، ۱۳ → CombatDrone | خیر | خیر | خیر |
| سوریه | `Syria_WarFactory_T` | `Syria_WarFactoryCommandSet_NoSarab` | ۹ → AlKhalid، ۱۳ → CombatDrone | خیر | خیر | خیر |
| هند | `India_WarFactory_T` | `India_WarFactoryCommandSet_NoSarab` | قفل roster موجود CommandSet.ini (آمریکا) | خیر | خیر | خیر |
| پاکستان | `Pakistan_WarFactory_T` | `Pakistan_WarFactoryCommandSet_NoSarab` | قفل roster موجود CommandSet.ini (آمریکا) | خیر | خیر | خیر |
| آفریقای جنوبی | `SouthAfrica_WarFactory_T` | `SouthAfrica_WarFactoryCommandSet_NoSarab` | ۹ → AlKhalid، ۱۳ → CombatDrone | خیر | خیر | خیر |
| لیبی | `Libya_WarFactory_T` | `Libya_WarFactoryCommandSet_NoSarab` | ۹ → AlKhalid، ۱۳ → CombatDrone | خیر | خیر | خیر |

پنج کشور عراقی بقیهٔ گزینه‌ها را نگه داشتند: T-72, BMP-1/2, BTR-90, 2S1, Sam8, AssadBabel-2, SA-6, Alhussaien, Roland3K, BM-21, Sell.

`Iraq_AlFahdMissileFactoryCommandSet` همچنان `CB_MISSILE_D/E/G` دارد.

## اعتبارسنجی

استاتیک روی فایل نهایی قابل نصب: Object Last-Win هر هفت کشور در `zzzzz_SpecterWfRemoveSarab` است، CommandSet فعال نام یکتاست، هیچ اسلات ممنوعی روی آن نام‌ها نیست، Missile Factory و last-winهای Supply Centre / HT-233-92N6E / رادار عراق حفظ شدند.

تست داخل بازی: اجرا نشد.

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 128 596 | `5938daae22613cfe36455e83995d2c101fb0a012332f4be3cf1ccee2be5df579` |

ورودی‌ها: 3573 → 3581.

## نصب

1. `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` و `0_SPECTER_*` را نگه دارید.
2. `_SPEC_DATA_ONE.big` این Release را جایگزین کنید (نه فایل Release قبلی).
3. ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
