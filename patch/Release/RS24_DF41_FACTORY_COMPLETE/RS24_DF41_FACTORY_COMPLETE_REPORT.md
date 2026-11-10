# RS-24 / DF-41 — factory-complete create path

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` و پوشهٔ نصب کاربر اینجا نیستند. Crash تا آزمایش داخل ZH رفع‌شده نیست.

## ۱. مقایسهٔ واقعی PR #704 با نسخه‌های قبلی

| پرونده | حجم | SHA-256 | ورودی | تعریف `RussiaVehicleRS24` / `ChinaVehicleDF41` |
| --- | ---: | --- | ---: | --- |
| wf-restore | 374 008 909 | `242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d` | 3572 | فقط مسیر اصلی Specter |
| `rs24-df41-loco-crash` | همان restore به‌جز overlay | `4f41a480…` | +2 overlay | مسیر اصلی **بدون تغییر** + `zzzzz_*` |
| `rs24-df41-firstwin` / PR #704 | 374 007 776 | `31cfd27daccec0004814eef8f10aedb8fb972923d0e11491ef9201ccf3097db4` | 3572 | **همان مسیر اصلی جایگزین شد** |
| این پرونده | 374 007 800 | `4d74a2f423914d31b4e5e58ff463929d3fc1bad965cc78e3743e950221346a52` | 3572 | همان مسیر اصلی دوباره جایگزین شد |

شواهد که #704 واقعاً مسیر زنده را عوض کرد (نه overlay):

- هش مسیر `Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini`: firstwin `7ddb60c8…` ≠ restore `d5670069…`
- هش مسیر `Data\INI\Object\Specter\PLA\Wheeled\DF41.ini`: firstwin `9bd6e459…` ≠ restore `8d255aff…`
- هر Object فقط یک تعریف دارد؛ پوشهٔ `zzzzz_SpecterRs24*` در firstwin خالی است
- overlayهای قبلی (`wf-crash` / `spawn-crash` / `loco-crash`) فایل اصلی را عوض نکردند

اگر کاربر SHA `31cfd27d…` را نصب کرده، تعریف زنده همان firstwin است و هنوز کرش تایمر را توضیح می‌دهد. SHA نصب‌شده روی ماشین کاربر اینجا قابل خواندن نیست.

`Launch_Specter.bat` فقط `_SPEC_DATA_ONE.big` را کنار `generals.exe` می‌گذارد. ترتیب ASCII: `0_SPECTER_*` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`. Object در `loadDirectory` است؛ تعریف **اول** همین دو مسیر Specter است.

## ۲. مسیر کامل تولید (firstwin زنده، قبل از این اصلاح)

روسیه:

`Command_ConstructRussiaVehicleRS24` (`CommandButton.ini`) → `Object = RussiaVehicleRS24` → `RussiaWarFactoryCommandSet` اسلات ۱۳ → `RussiaWarFactory` / `DefaultProductionExitUpdate` / `FactoryExitWidth = 25`

چین:

`Command_ConstructChinaVehicleDF41` → `Object = ChinaVehicleDF41` → `PLAWarFactoryCommandSet` اسلات ۴ و ۷ → همان `DefaultProductionExitUpdate`

T3/LBD جدا: `Command_ConstructRussia_RS24_Yars` → `Russia_RS24_Yars` **ناموجود**. اگر تایمر ۲۲ ثانیه تمام شود، مسیر اصلی است نه alias.

Locomotor هر دو بعد از #704: `Generic8x8Locomotor` (در `Data\INI\Locomotor.ini` هست). KindOf ساده مثل 9K720. `InitialPayload` حذف شده. Drawهای بدون W3D از فایل اصلی چین برداشته شده. همهٔ Modelهای باقی‌مانده در ART TWO هستند.

## ۳. علت‌های محتمل باقی‌مانده (شواهد فایل / خط)

واحدهای سالم همان کارخانه: `RussiaVehicle9K720` اسلات ۱۲، `ChinaVehicleDF17` اسلات ۳، `ChinaVehicleDF21C` اسلات ۱۰. هر سه: بدون rider-contain، `DeployStyleAIUpdate` با زیربلوک `Turret`، `GeometryIsSmall = No`، یک Draw، WeaponSet `Conditions = None` مسلح.

تفاوت‌های مشترک RS-24 / DF-41 بعد از #704 که با کرش لحظهٔ پایان تایمر سازگارند:

| # | فرض | شواهد | سالم همان کارخانه |
| --- | --- | --- | --- |
| A | `DeployStyleAIUpdate` با `TurretsFunctionOnlyWhenDeployed` / `TurretsMustCenterBeforePacking` **بدون** زیربلوک `Turret` در init ماژول AI | firstwin `RussiaVehicleRS24` خط ۴۳۶–۴۴۴؛ `ChinaVehicleDF41` خط ۳۸۲–۳۹۰. پرچم‌ها turret را اجباری می‌کنند | 9K720 / DF-17 / DF-21C همه `Turret { InitiallyDisabled = Yes; ControlledWeaponSlots = PRIMARY SECONDARY TERTIARY }` دارند |
| B | `RiderChangeContain` خالی در لحظهٔ create (بدون `InitialPayload`) | firstwin RS24 خط ۴۴۹–۴۵۹؛ DF41 خط ۳۹۵–۴۰۵. Rider1/2 به `GenericFakeRider*_Default_Rank` اشاره می‌کند (Object موجود است) ولی contain در spawn خالی است. `OCL_Rearm_*` هنوز `ContainInsideSourceObject = Yes` می‌نویسد | هیچ‌کدام rider-contain ندارند |
| C | `GeometryIsSmall = Yes` با `GeometryMajorRadius = 37` هنگام خروج از در کارخانه (`FactoryExitWidth = 25`) | firstwin RS24 خط ۵۳۱–۵۳۵؛ DF41 خط ۴۷۷–۴۸۱ | هر سه سالم `No` و شعاع ۳۲ |
| D | روسیه: `AnimationMode = ONCE` بدون `Animation` | firstwin RS24 خط ۱۷۲–۱۷۶ (`RIDER1 DEPLOYED REALLYDAMAGED`) و ۲۵۳–۲۶۳ (`RIDER2 DEPLOYED REALLYDAMAGED`). رگرسیون #704 بعد از حذف `RU_RS28_*` | چین صفر مورد دارد و باز کرش می‌کند → علت مشترک نیست |

رد یا ضعیف:

- استخوان `Turret = TUT` روی W3D نیست (RUS_RS24 / CHI_DF41 هیچ `TUT`/`TURRET` ندارند). DF-17 / DF-21C هم `Turret = Turrettt` بدون استخوان دارند **ولی** زیربلوک AI دارند و از کارخانه سالم بیرون می‌آیند. پس استخوان گمشده به‌تنهایی کافی نیست.
- `FireWeaponUpdate` ×۲: `RussiaVehicleKrasukha4` همان کارخانه FWU دارد و کار می‌کند.
- `ObjectCreationUpgrade` فقط با کلیک Rearm شلیک می‌شود، نه در spawn. وابسته به contain است؛ با حذف contain باید حذف شود تا کلیک بعدی کرش نسازد.
- مرحلهٔ دقیق (ThingFactory / module init / ProductionExit / فریم اول Draw) بدون لاگ ZH ثابت نمی‌شود.

## ۴. اصلاح این پرونده

همان دو مسیر اصلی دوباره از wf-restore جایگزین شدند. تعریف دوم / overlay اضافه نشد. ورودی BIG همان ۳۵۷۲ است. فقط DATA.

هر دو Object:

- زیربلوک `Turret` مثل 9K720 داخل `DeployStyleAIUpdate`
- حذف `RiderChangeContain` و `ObjectCreationUpgrade` rearm
- کلاهک‌ها روی `WeaponSet Conditions = None` (نام سلاح عوض نشد)
- `CommandSet = Iraq_AlhussaienArmedCommandSet` (همان نوار مسلح RIDER2 قبلی؛ دکمه‌ها `FIRE_WEAPON` اسلات PRIMARY/SECONDARY هستند)
- `GeometryIsSmall = No`

روسیه: `Animation = RUS_RS24_DA.RUS_RS24_DA` و `RUS_RS24_A.RUS_RS24_A` به دو state یتیم اضافه شد.

عوض نشد: قیمت ۳۵۰۰، زمان ۲۲ث، Side، DisplayName، KindOf، `Generic8x8Locomotor`، بدنه / Camo / Bones، نام کلاهک‌ها، FireWeaponUpdate، کارخانه، CommandSet کشورهای دیگر.

Alias `Russia_RS24_Yars` اضافه نشد.

## ۵. اعتبارسنجی ایستا (نه تست داخل بازی)

- هر Object فقط یک تعریف دارد و همان مسیر اصلی Specter است
- دکمهٔ کارخانه هنوز به همان Object اشاره می‌کند؛ اسلات کارخانه عوض نشده
- همهٔ `Model`های باقی‌مانده در `_SPEC_ART_TWO.big` هستند (صفر W3D مفقود)
- سلاح‌ها، Locomotor، CommandSet مسلح در DATA موجودند
- بلوک `CommandSet` داخل پوشهٔ Object/ نیست
- Last-win عراق / Supply / DataLink دست‌نخورده
- در برابر restore و firstwin فقط همان دو مسیر Object عوض شده‌اند
- ART در این BIG نیست

## ۶. BIG

| فایل | حجم | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374 007 800 | `4d74a2f423914d31b4e5e58ff463929d3fc1bad965cc78e3743e950221346a52` |

ورودی‌ها: ۳۵۷۲.

## نصب

فقط این `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `4d74a2f4…` شود. ART را عوض نکنید.

هم‌زمان نگه ندارید: `rs24-df41-firstwin`، `rs24-df41-loco-crash`، `rs24-df41-spawn-crash`، `rs24-df41-wf-crash`، `wf-fix-commandset-crash`، `wf-detach-sarab7-9p117-alabbas`، `wf-remove-sarab7-9p117-alabbas`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
