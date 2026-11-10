# Crash fix: CommandSet blocks were in Object/

**بازی اجرا نشد.** Zero Hour / SPECTER در این محیط موجود نیست. ادعای رفع قطعی Crash داخل بازی نمی‌شود. اعتبارسنجی فقط استاتیک روی DATA قابل نصب است.

## علت Crash با شواهد

Release قبلی (`wf-detach-sarab7-9p117-alabbas`، SHA-256 `5938daae…`) این فایل را داخل `_SPEC_DATA_ONE.big` گذاشت:

`Data\INI\Object\zzzzz_SpecterWfRemoveSarab\CommandSets.ini`

مسیر خطای بازی (`Data/ini/zzzzz_specterwfremovesarab/commandsets.ini`) همان فایل است.

داخل آن فایل تعریف‌ها **بلوک CommandSet** بودند:

```
CommandSet SaudiArabia_WarFactoryCommandSet_NoSarab
  1 = Command_ConstructIraq_T-72
  ...
End
```

این syntax برای `Data\INI\CommandSet*.ini` معتبر است. برای پوشهٔ `Data\INI\Object\` معتبر نیست.

بارگذاری ZH:

- فایل‌های `Data\INI\Object\` به‌عنوان Object INI parse می‌شوند.
- در آن context، `CommandSet` یک **فیلد Object** است: `CommandSet = Name`.
- بلوک `CommandSet SaudiArabia_WarFactoryCommandSet_NoSarab` فیلد را با `SaudiArabia` پر می‌کند و باقی‌مانده `_WarFactoryCommandSet_NoSarab` می‌شود — همان توکن خطای `_warfactorycommandset_nosarab`.

چیزی که Crash **نبود**:

| فرض | نتیجه روی DATA واقعی |
| --- | --- |
| نام از نظر charset نامعتبر است | خیر. `SaudiArabia_WarFactoryCommandSet_NoSarab` فقط حروف / رقم / `_` است و با حرف شروع می‌شود. الگوی SPECTER همین است. |
| دوباره در `CommandSet.ini` تعریف شده | خیر. این هفت نام یکتا هیچ‌جا در `CommandSet.ini` نیستند. فقط یک تعریف دارند. |
| تداخل با CommandSet دیگر | خیر. نام‌های یکتا فقط در همین فایل جدید هستند. |
| کارخانهٔ عربستان به نام اشتباه اشاره کرده | خیر. `SaudiArabia_WarFactory_T` فیلد درست دارد: `CommandSet = SaudiArabia_WarFactoryCommandSet_NoSarab`. |

## اصلاح محدود

بلوک‌ها به `Data\INI\CommandSet_ZZZZ_ZZZZZWfDetach.ini` منتقل شدند (همان الگوی `CommandSet_Pakistan.ini`). فایل Crash از BIG حذف شد. هفت Object last-win و نام‌های یکتا و اسلات‌ها عوض نشدند.

## نتیجه هر کشور (استاتیک)

| کشور | Object last-win | CommandSet فعال | محل تعریف نهایی CommandSet | Sarab7 / 9P117 / AlAbbas |
| --- | --- | --- | --- | --- |
| عربستان | `zzzzz_SpecterWfRemoveSarab\SaudiArabia_WarFactory.ini` | `SaudiArabia_WarFactoryCommandSet_NoSarab` | `CommandSet_ZZZZ_ZZZZZWfDetach.ini` | خیر |
| امارات | `UAE_WarFactory.ini` | `UAE_WarFactoryCommandSet_NoSarab` | همان | خیر |
| سوریه | `Syria_WarFactory.ini` | `Syria_WarFactoryCommandSet_NoSarab` | همان | خیر |
| هند | `India_WarFactory.ini` | `India_WarFactoryCommandSet_NoSarab` | همان | خیر |
| پاکستان | `Pakistan_WarFactory.ini` | `Pakistan_WarFactoryCommandSet_NoSarab` | همان | خیر |
| آفریقای جنوبی | `SouthAfrica_WarFactory.ini` | `SouthAfrica_WarFactoryCommandSet_NoSarab` | همان | خیر |
| لیبی | `Libya_WarFactory.ini` | `Libya_WarFactoryCommandSet_NoSarab` | همان | خیر |

پنج کشور عراقی بقیهٔ گزینه‌ها را نگه داشتند: T-72, BMP-1/2, BTR-90, 2S1, Sam8, AssadBabel-2, SA-6, Alhussaien, Roland3K, BM-21, Sell. اسلات ۹ = AlKhalid همان کشور، اسلات ۱۳ = CombatDrone همان کشور.

`Iraq_AlFahdMissileFactoryCommandSet` همچنان `CB_MISSILE_D/E/G` دارد.

Last-winهای حفظ‌شده: رادار عراق، Supply Centre خرید داخل ساختمان، HT-233 / 92N6E DataLink، TPY-2.

## اعتبارسنجی

- فایل Crash در BIG نیست.
- هیچ بلوک `CommandSet Name` در `Object\zzzzz_SpecterWfRemoveSarab\` نیست.
- تعریف نهایی هر هفت نام یکتا فقط `Data\INI\CommandSet_ZZZZ_ZZZZZWfDetach.ini` است.
- Objectهای `*_WarFactory_T` هنوز به همان نام‌های یکتا اشاره می‌کنند.
- روی آن نام‌ها دکمهٔ ممنوع نیست.
- تست داخل بازی: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 129 157 | `1411c9aa7d1850b4a50858b010a14beb967c0b90441a96d627e68928128bb54a` |

ورودی‌ها: 3581 (فایل Crash حذف، `CommandSet_ZZZZ_ZZZZZWfDetach.ini` اضافه).

## نصب

فقط همین `_SPEC_DATA_ONE.big` را جایگزین کنید.

هم‌زمان نصب نکنید:

- `_SPEC_DATA_ONE.big` مربوط به Release `wf-detach-sarab7-9p117-alabbas` (فایل Crash)
- `_SPEC_DATA_ONE.big` مربوط به Release `wf-remove-sarab7-9p117-alabbas` (دکمه‌ها در بازی نمی‌رفتند)

`_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` و `0_SPECTER_*` را نگه دارید. Overlay جدا لازم نیست.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
