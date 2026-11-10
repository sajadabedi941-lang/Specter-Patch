# RS-24 / DF-41 — first-win live Object

**Zero Hour اجرا نشد.** پوشهٔ نصب کاربر اینجا نیست. SHA روی دیسک بازی تطبیق داده نشد. Crash تا آزمایش داخل ZH رفع‌شده نیست.

چهار overlay قبلی (`wf-crash`، `spawn-crash`، `loco-crash`، حذف Draw) تعریف **دوم** به مسیر `zzzzz_*` اضافه کردند. بازی همان فایل اصلی را نگه می‌دارد.

## ۱. نسخهٔ فعال

| فایل بررسی‌شده اینجا | SHA-256 | توضیح |
| --- | --- | --- |
| Release `rs24-df41-loco-crash` | `4f41a480…` | منتشر شده؛ دو تعریف برای هر Object |
| DATA این محیط | همان BIG Release / wf-restore | `generals.exe` و `INIZH.big` نیستند |

اگر SHA کنار `generals.exe` برابر `4f41a480f1cc9a8e8d86274cd5c1ddb8edc3755194dc86d41cb0f0d975adb6ed` باشد، فایل Release درست نصب شده — ولی **محتوای زندهٔ Object همان فایل اصلی است، نه overlay**.

`Launch_Specter.bat` فقط `_SPEC_DATA_ONE.big` را کپی می‌کند. مسیرهای stock را INIZH first-win می‌کند. پوشهٔ `Object\` چند فایل با یک نام Object دارد.

شواهد اینکه overlay زنده نیست:

- `CommandSet` اضافه با نام تکراری نوار زنده را عوض نمی‌کند (هفت کشور WF).
- `Iraq_RadarStation` اصلی از قبل `GrantUpgradeCreate Upgrade_AmericaRadar` دارد؛ کار کردن نقشه overlay را ثابت نمی‌کند.
- overlay عراق `SpySatellite` را از Object برداشت؛ دکمه در `CommandSet.ini` اول ماند.
- چهار overlay موشک هیچ اثر داخل بازی نداشتند، در حالی که هر چهار BIG آن‌ها را به‌عنوان last-win گزارش کرده بودند.

تعریف **اول** (زنده اگر first-win باشد):

- `Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini`
- `Data\INI\Object\Specter\PLA\Wheeled\DF41.ini`

این پرونده همان دو مسیر را **جایگزین** می‌کند. تعریف دوم اضافه نشد. ورودی BIG همان ۳۵۷۲ است.

## ۲. روسیه — مسیر واقعی

`Command_ConstructRussiaVehicleRS24` → `RussiaVehicleRS24` → `RussiaWarFactory` / `DefaultProductionExitUpdate`.

T3/LBD جدا: `Command_ConstructRussia_RS24_Yars` → `Russia_RS24_Yars` ناموجود. اگر تایمر ۲۲ث تمام شود، مسیر اصلی است.

### تعریف زندهٔ قبلی (فایل اصلی)

Locomotor `_H`؛ KindOf با `HUGE_VEHICLE SALVAGER GARRISONABLE`؛ `InitialPayload` رایدر ۱۰ میلیون‌واحدی؛ بدون WeaponSet پیش‌فرض؛ `RiderChangeContain`؛ `RU_RS28_*` مفقود در ART TWO؛ Drawهای RUS_RS24 همه در ART TWO هستند.

### واحد سالم همان کارخانه

`RussiaVehicle9K720` اسلات ۱۲: `Generic8x8Locomotor`، KindOf ساده، یک Draw، WeaponSet `None`، بدون Rider/Payload، `GeometryIsSmall = No`.

### فرضیه‌ها

| فرض | وضعیت |
| --- | --- |
| overlay loco/Draw/spawn در بازی بار شد | رد. اثر نداشتند و فایل اصلی عوض نشده بود |
| `_H` در جدول INIZH نیست | هنوز ممکن است؛ تا وقتی روی فایل اصلی نرود آزمایش نشده |
| InitialPayload هنگام خروج کارخانه | روی فایل اصلی هنوز بود؛ 9K720 ندارد |
| Draw مفقود روسیه | رد برای بدنه؛ `RU_RS28_*` مفقود است |
| مرحلهٔ دقیق Crash | بدون لاگ نامشخص |

## ۳. چین — مسیر واقعی

`Command_ConstructChinaVehicleDF41` → `ChinaVehicleDF41` → همان `DefaultProductionExitUpdate`.

### تعریف زندهٔ قبلی (فایل اصلی)

همان خانوادهٔ مهندسی روسیه. Draw اضافه: `CHI_DF41_WL` / `CHI_DF41HL` / `CHI_DF41_T` در ART TWO نیستند؛ `Model = None` برای تایر.

### واحد سالم همان کارخانه

`ChinaVehicleDF17` اسلات ۳ و `ChinaVehicleDF21C` اسلات ۱۰: `Generic8x8Locomotor`، یک Draw، بدون Rider/Payload، KindOf ساده.

`ChinaVehicleDF41_AI` همان Drawهای مفقود و `_H` را دارد؛ اسلات ۱۵ پنهان است.

### فرضیه‌ها

| فرض | وضعیت |
| --- | --- |
| حذف Draw در `wf-crash` زنده شد | رد. فقط overlay بود |
| AI بدون آن Drawها کار می‌کند | رد از روی فایل؛ AI همان Drawها را دارد |
| بقیه مثل روسیه | Payload/KindOf/WeaponSet روی فایل اصلی بودند |

## ۴. اصلاح این پرونده

جایگزینی همان دو مسیر اصلی در DATA `wf-restore`. Overlay `zzzzz_*` برای این دو موشک نیست.

هر دو: `Generic8x8Locomotor`، WeaponSet پیش‌فرض خلع‌سلاح، CommandSet UnarmedRearm، بدون `InitialPayload`، KindOf هم‌تراز 9K720/DF-21C. `RiderChangeContain` و OCL Rearm ماند.

روسیه: ارجاع `RU_RS28_*` حذف شد. Drawهای RUS_RS24 ماند (W3D دارند). Hulk ماند.

چین: Drawهایی که W3D در ART TWO ندارند از **فایل اصلی** برداشته شد. بدنه/Camo/Bones ماند.

قیمت ۳۵۰۰، زمان ۲۲ث، Side، کلاهک‌ها عوض نشدند.

## اعتبارسنجی

- هر Object فقط یک تعریف دارد و همان مسیر اصلی است.
- بلوک CommandSet داخل Object/ نیست.
- Last-win عراق/Supply/DataLink دست نخورده.
- تست بازی: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 007 776 | `31cfd27daccec0004814eef8f10aedb8fb972923d0e11491ef9201ccf3097db4` |

ورودی‌ها: ۳۵۷۲ (overlay اضافه نشد).

## نصب

فقط این `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `31cfd27d…` شود. ART را عوض نکنید.

هم‌زمان نگه ندارید: `rs24-df41-loco-crash`، `rs24-df41-spawn-crash`، `rs24-df41-wf-crash`، `wf-fix-commandset-crash`، `wf-detach-sarab7-9p117-alabbas`، `wf-remove-sarab7-9p117-alabbas`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
