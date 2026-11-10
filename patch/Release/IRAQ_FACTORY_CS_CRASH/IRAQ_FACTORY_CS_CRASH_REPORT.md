# Iraq factory CommandSet crash after PR #713

**Zero Hour اجرا نشد.** تست ایستا ≠ تأیید داخل بازی.

## علت (با شواهد)

دیالوگ کرش:

```
Data/INI/CommandSet.ini
CommandSet Iraq_AlFahdMissileFactoryCommandSet
```

### ۱. CommandSet.ini منتشرشدهٔ #713 در برابر #712

هر دو فایل از Release مربوطه استخراج شد (SHA با دارایی گیت‌هاب یکی است).

| | #712 `missile-factory-klmn` | #713 `missile-factory-m-rs24` |
| --- | ---: | ---: |
| حجم | 454291 | 454198 |
| SHA-256 | `56bd87eb…7139ea74` | `405e5879…62ad858` |
| تعداد CommandSet | 1152 یکتا، بدون تکرار | 1152 یکتا، بدون تکرار |

تنها ۲۵ مجموعه عوض شد؛ در همه فقط اسلات ۱۳. سینتکس عراق معتبر است (`End` بسته، بدون کاراکتر غیر ASCII، بدون اسلات تکراری):

```
#712  13 = CB_MISSILE_M
#713  13 = CB_FACTORY_SLOT_M
```

بقیهٔ اسلات‌های عراق (A–J، K=`CB_MISSILE_K`، L، N) با #712 یکسان است. فاصلهٔ خالی بعد از `End` عراق حذف شد؛ SAGE به آن نیاز ندارد و بقیهٔ مجموعه‌های تغییرکرده همان فاصله را دارند.

`CB_FACTORY_SLOT_M` در CommandSet.ini شمارهٔ #713 بیست‌وپنج بار آمده؛ در #712 صفر بار.

### ۲. دکمه در DATA هست، روی مسیر زنده‌ی ControlBar نیست

`CommandButton CB_FACTORY_SLOT_M` فقط در انتهای `Data\INI\CommandButton.ini` داخل `_SPEC_DATA_ONE.big` شمارهٔ #713 تعریف شده (Object=`Factory_RS24YarsOnce`). مسیر یکتای Object و سلاح یک‌کلیپ دست‌نخورده‌اند.

منبع موتور (همان استناد PR #710، `ControlBar::init`):

```
ini.load("Data\\INI\\Default\\CommandButton.ini", INI_LOAD_OVERWRITE, NULL);
ini.load("Data\\INI\\CommandButton.ini", INI_LOAD_OVERWRITE, NULL);
ini.load("Data\\INI\\CommandSet.ini", INI_LOAD_OVERWRITE, NULL);
```

`FileSystem::openFile` اول فایل شل را باز می‌کند؛ بین BIGها اولین آرشیو برنده است (`overwrite = FALSE`). `INIZH.big` قبل از `_SPEC_DATA_ONE.big` ثبت می‌شود. بنابراین:

- `CommandSet.ini` شل #713 زنده است (overlay شمارهٔ #710/#712/#713).
- `CommandButton.ini` شل نصب نشد. ControlBar نسخهٔ INIZH را باز می‌کند، نه نسخهٔ DATA که `CB_FACTORY_SLOT_M` دارد.

`parseCommandSetDefinition` هر نام اسلات را در جدول دکمه جستجو می‌کند. نام ناموجود = `INI_INVALID_DATA` و دیالوگ همان CommandSet در حال پارس را نشان می‌دهد.

`Iraq_AlFahdMissileFactoryCommandSet` اولین مجموعهٔ کارخانه در فایل است که `CB_FACTORY_SLOT_M` دارد (آفست ۴۳۰۸۹۶). مجموعه‌های آمریکا/روسیه و غیره بعد از آن‌اند؛ پارسر به آن‌ها نمی‌رسد.

### ۳. چرا #712 با همین CommandSet عراق کرش گزارش نشد

اسلات ۱۳ عراق در #712 هنوز `CB_MISSILE_M` بود. آن دکمه از قبل در جدول زنده/INIZH هست (`Iraq_BM-21`). #713 همان اسلات را به دکمهٔ جدید عوض کرد. اسلات‌های L/N شمارهٔ #712 هم فقط در DATA `CommandButton.ini` بودند؛ اگر آن‌ها هم در INIZH نباشند، #712 روی همین نام کرش می‌کرد. اصلاح شل `CommandButton.ini` هر چهار دکمهٔ K/L/M/N را روی مسیر زنده می‌گذارد.

### ۴. ارجاع‌های زنده

| محل | نقش |
| --- | --- |
| `Object Iraq_AlFahdMissileFactory` | `CommandSet = Iraq_AlFahdMissileFactoryCommandSet` — تعریف بلاک ندارد |
| `CommandSet.ini` | یک تعریف، بدون تکرار |
| فایل‌های extra `CommandSet_*.ini` | جدول ControlBar نیستند |
| `Iraq_AlFahdMissileFactoryBuildingCommandSet` | فقط Sell؛ عوض نشد |

مصر / Arabic Alliance کارخانهٔ موشکی ندارند.

## اصلاح (حداقلی)

DATA BIG و `CommandSet.ini` شمارهٔ #713 **عوض نشدند**. فقط `CommandButton.ini` همان BIG به‌صورت فایل شل `Data\INI\CommandButton.ini` منتشر شد — همان الگوی #710.

حفظ شد: Fire ایران (#710)، K/L/N (#712)، اسلات M = `Factory_RS24YarsOnce` @ 27000 یک‌کلیپ، A–J عراق، عدم انتقال فهرست عراق.

ART عوض نشد.

## اعتبارسنجی ایستا

هر ۲۵ CommandSet کارخانه: اسلات M = `CB_FACTORY_SLOT_M` و هر نام اسلات در `CommandButton.ini` شل موجود است. عراق A–J = `CB_MISSILE_A`…`J`، K = `CB_MISSILE_K`.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374080193 | `d5a8ed982e7ff37de1fa9923f1ee96abe16312f481f563891d95e1b4dffb26c8` |
| `CommandSet.ini` | 454198 | `405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

BIG و CommandSet با Release `missile-factory-m-rs24` بایت‌به‌بایت یکسان‌اند.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید (همان BIG شمارهٔ #713).
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید (جایگزین #710/#712/#713).
3. **`CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید** — این فایل در #713 نبود و علت کرش است.
4. ART را عوض نکنید.

یا `Install_IraqFactoryCsCrash.bat` را اجرا کنید.
