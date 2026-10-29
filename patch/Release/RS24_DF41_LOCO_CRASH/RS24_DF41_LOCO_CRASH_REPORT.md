# RS-24 / DF-41 — root cause at production complete

**Zero Hour در این محیط اجرا نشد.** پوشهٔ نصب بازی کاربر اینجا نیست. SHA فایل روی دیسک کاربر با این Release تطبیق داده نشد. رفع Crash تا آزمایش واقعی داخل بازی تأییدشده نیست.

سه Release قبلی نصب و رد شدند. هیچ‌کدام فیلد `Locomotor` را عوض نکردند.

## ۱. فایل فعال و ترتیب بارگذاری

بازی و لاگر اینجا نیستند. آنچه بررسی شد همان BIGهای Release و DATA سالم `wf-restore` است.

| Release | حجم | SHA-256 | ورودی |
| --- | --- | --- | --- |
| `wf-restore-warfactory-buttons` | 374 008 909 | `242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d` | ۳۵۷۲ |
| `rs24-df41-wf-crash` | 374 049 400 | `a5514eac1a0f8cc497ee32ccac498c3b79121e646f4f233bcee11c3a346598be` | ۳۵۷۴ |
| `rs24-df41-spawn-crash` | 374 050 383 | `4fe03adf2e3d8dcc9a76fc0f5c066be54d6113f6ce698ddc157b8139f2e964ee` | ۳۵۷۴ |
| این پرونده `rs24-df41-loco-crash` | 374 050 097 | `4f41a480f1cc9a8e8d86274cd5c1ddb8edc3755194dc86d41cb0f0d975adb6ed` | ۳۵۷۴ |

`Launch_Specter.bat` فقط `_SPEC_DATA_ONE.big` را کنار `generals.exe` کپی می‌کند. اگر کاربر فایل را جایگزین نکرده باشد، بازی همان DATA قبلی را بار می‌کند.

Zero Hour مسیرهای هم‌نام را **first-win** می‌کند (`overwrite=FALSE`). ترتیب الفبایی معمول:

`0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`

`INIZH.big` زودتر از `_SPEC_DATA_ONE.big` مسیرهای stock را ثبت می‌کند. بنابراین `Data\INI\Locomotor.ini` / `Weapon.ini` / `CommandSet.ini` / `CommandButton.ini` نسخهٔ INIZH زنده است، نه نسخهٔ داخل SPEC DATA. پوشهٔ `Data\INI\Object\` مسیرهای یکتای SPECTER دارد و last-win نام Object آنجا کار می‌کند (رادار عراق و Supply Centre همین‌طور در بازی اثر کردند).

فقط یک فایل Locomotor در هر سه BIG هست: `Data\INI\Locomotor.ini`. فایل اضافهٔ `Locomotor_*.ini` در DATA قابل نصب نیست. `Generic8x8Locomotor_H` فقط در همان مسیر stock تعریف شده و در جدول زندهٔ INIZH نیست.

اگر SHA فایل داخل پوشهٔ بازی با یکی از سه ردیف بالا یکی نباشد، اول همان ناسازگاری نصب را درست کنید.

## ۲. روسیه — مسیر واقعی

| حلقه | تعریف نهایی |
| --- | --- |
| دکمهٔ اصلی | `Command_ConstructRussiaVehicleRS24` → `RussiaVehicleRS24` |
| کارخانه | `RussiaWarFactory` → `RussiaWarFactoryCommandSet` اسلات ۱۳ |
| خروج | `DefaultProductionExitUpdate` ، `FactoryExitWidth = 25` |
| last-win در `wf-crash` | `RussiaVehicleRS24` **عوض نشد** (فقط alias اضافه شد) |
| last-win در `spawn-crash` | overlay `zzzzz_SpecterRs24Df41Spawn` برور است؛ هنوز `Generic8x8Locomotor_H` |
| T3 / LBD جدا | `Command_ConstructRussia_RS24_Yars` → `Russia_RS24_Yars` **ناموجود**. آن مسیر کلیک/صف است نه تایمر ۲۲ث WF اصلی |

## ۳. چین — مسیر واقعی

| حلقه | تعریف نهایی |
| --- | --- |
| دکمه | `Command_ConstructChinaVehicleDF41` → `ChinaVehicleDF41` |
| کارخانه | `ChinaWarFactory` → `PLAWarFactoryCommandSet` اسلات ۴ و ۷ |
| خروج | همان `DefaultProductionExitUpdate` |
| مقایسهٔ شلیک/استقرار | `ChinaVehicleDF21C` و `ChinaVehicleDF17`: یک `W3DTruckDraw`، `WeaponSet Conditions = None`، `Generic8x8Locomotor`، بدون Rider |
| AI | `ChinaVehicleDF41_AI` همان Drawهای اضافه و همان `_H` را دارد؛ اسلات ۱۵ پنهان است و ساخته‌شدنش تأیید نشده |

## ۴. تفاوت‌های نسخهٔ نهایی (wf-restore / هر سه Release قبلی)

### روسیه `RussiaVehicleRS24` در برابر `RussiaVehicle9K720` / `Russia_Yars`

| مورد | RS-24 (قبل از این پرونده) | 9K720 / Yars سالم | ارتباط با Crash پایان تایمر |
| --- | --- | --- | --- |
| Locomotor | `Generic8x8Locomotor_H` | `Generic8x8Locomotor` | **قوی.** `_H` فقط در `Locomotor.ini` است؛ INIZH آن مسیر را می‌برد. ایجاد Object بدون locomotor زنده Crash می‌دهد. سه اصلاح قبلی این فیلد را نگه داشتند. |
| KindOf | + `HUGE_VEHICLE SALVAGER GARRISONABLE_UNTIL_DESTROYED` | بدون آن‌ها | spawn-crash این را برداشت و Crash ماند |
| WeaponSet پیش‌فرض | نداشت (فقط RIDER1/2) | `Conditions = None` | spawn-crash اضافه کرد و Crash ماند |
| RiderChange + InitialPayload | دارد؛ رایدر با ارتفاع ۱۰٬۰۰۰٬۰۰۰ | ندارد | spawn-crash Payload را برداشت و Crash ماند |
| Draw اضافه / `RU_RS28_*` | چند Draw؛ دو انیمیشن به W3D مفقود | یک Draw | مدل بدنه و تایر RS-24 در ART TWO هستند؛ فرض Draw در بازی رد شد |
| Turret = TUT | استخوان روی `RUS_RS24` نیست | 9K720 استخوان `TURRET` دارد | DF-21C هم Turret ناموجود دارد و سالم است |
| FireWeaponUpdate decal | دو بار | ندارد | Krasukha روی همین WF دارد |
| Geometry | BOX 37 / 10 / 17 ، `GeometryIsSmall = Yes` | کوچک‌تر | بدون بازی قطعی نیست |
| کارخانه | همان DefaultProductionExit | همان | کارخانه دست نخورده |

### چین `ChinaVehicleDF41` در برابر DF-21C / DF-17

| مورد | DF-41 (قبل از این پرونده) | DF-21C / DF-17 | ارتباط |
| --- | --- | --- | --- |
| Locomotor | `Generic8x8Locomotor_H` | `Generic8x8Locomotor` | **همان علت مستقل.** هر دو موشک `_H` دارند؛ واحدهای سالم همان کشور `_H` ندارند. |
| Draw WL / HL / T | W3D در ART TWO نیست | یک Draw سالم | `wf-crash` این Drawها را حذف کرد و Crash ماند. AI همان Drawهای مفقود را دارد |
| KindOf / Payload / WeaponSet | مثل RS-24 | ساده | spawn-crash عوض کرد و Crash ماند |
| مدل بدنه | `CHI_DF41` / `_A` / `_AD` / Camo / Bones در ART TWO هستند | موجود | بارگذاری بدنه علت ردشده است |

`Object_ZZZZ_*` و Supply last-win بعد از overlayهای قبلی می‌آیند ولی `RussiaVehicleRS24` / `ChinaVehicleDF41` را دوباره تعریف نمی‌کنند. last-win Object اگر کاربر BIG درست را گذاشته باشد واقعاً برنده است — فقط فیلد اشتباه را عوض کرده بودند.

## ۵. آیا اصلاحات قبلی در فایل فعال بودند؟

- اگر SHA = `a5514eac…` بود: alias و حذف Draw چین اعمال شده؛ `RussiaVehicleRS24` و `_H` دست‌نخورده.
- اگر SHA = `4fe03adf…` بود: KindOf / WeaponSet / Payload روی هر دو Object اعمال شده؛ **هنوز `_H`**.
- اگر SHA = `242a7c81…` یا DATA قدیمی‌تر بود: هیچ overlayای اعمال نشده؛ همان `_H` اصلی.

هر سه حالت به یک فیلد ایجاد می‌رسند که هرگز عوض نشد.

## ۶. مرحلهٔ Crash

بدون لاگ قطعی نیست. نزدیک‌ترین حلقه از روی فایل: **ایجاد Object پس از پایان تایمر** وقتی موتور `Locomotor = Generic8x8Locomotor_H` را resolve می‌کند. منطق صف و کلیک برای WF اصلی سالم است (نام Object موجود است).

## ۷. اصلاح ضروری

فقط last-win همان دو Object زنده روی DATA `wf-restore`:

`Locomotor = SET_NORMAL Generic8x8Locomotor`

این نام در INIZH هست و همان نام DF-21C / DF-17 / 9K720 / `Russia_Yars` است. سرعت زنده از ۴۲ به ۵۸ می‌رسد (همان سرعت واحد سالم). قیمت ۳۵۰۰، زمان ۲۲ث، Side، کلاهک‌ها، Draw، KindOf، Rider، ART و کارخانه عوض نشدند. alias و حذف Draw تکرار نشد.

پوشه‌های `zzzzz_SpecterRs24Df41Crash` و `zzzzz_SpecterRs24Df41Spawn` در این BIG نیستند.

T3/LBD روسیه همچنان به `Russia_RS24_Yars` مفقود می‌رود؛ آن مسیر جدا از Crash تایمر WF اصلی است.

## اعتبارسنجی استاتیک

- Last-win هر دو Object در `zzzzz_SpecterRs24Df41Loco` است و locomotor = `Generic8x8Locomotor`.
- `_H` در بدنهٔ last-win نیست.
- 9K720 و DF-21C همچنان `Generic8x8Locomotor` دارند.
- بلوک CommandSet داخل Object/ نیست.
- Last-win عراق رادار، Supply، DataLink سر جایشان هستند.
- تست بازی: **اجرا نشد.**

## نصب

فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید. ART را عوض نکنید.

هم‌زمان نگه ندارید: `rs24-df41-spawn-crash`، `rs24-df41-wf-crash`، `wf-fix-commandset-crash`، `wf-detach-sarab7-9p117-alabbas`، `wf-remove-sarab7-9p117-alabbas`.

SHA فایل داخل پوشهٔ بازی باید `4f41a480f1cc9a8e8d86274cd5c1ddb8edc3755194dc86d41cb0f0d975adb6ed` شود.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
