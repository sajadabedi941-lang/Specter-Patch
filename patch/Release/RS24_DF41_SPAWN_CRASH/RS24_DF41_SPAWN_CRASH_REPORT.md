# RS-24 Yars / DF-41 — crash at production complete

**Zero Hour در این محیط اجرا نشد.** لاگ Crash در دسترس نیست. رفع Crash تا آزمایش واقعی کاربر داخل بازی تأییدشده محسوب نمی‌شود.

Release قبلی `rs24-df41-wf-crash` نصب و آزمایش شد و مشکل ماند. این پرونده همان راه‌حل را تکرار نمی‌کند: Object مستعار `Russia_RS24_Yars` اضافه نشد و Drawهای DF-41 حذف نشدند.

ورودی: DATA سالم `wf-restore-warfactory-buttons` (`_SPEC_DATA_ONE.big`، SHA-256 `242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d`، ۳۵۷۲ ورودی).
ART فقط خوانده شد (`_SPEC_ART_TWO.big` از Full Release). ART تغییر نکرد.

بدون اجرای بازی نمی‌توان گفت Crash دقیقاً در کدام یک از این شش مرحله می‌افتد: پایان تایمر، منطق تکمیل کارخانه، `ThingFactory`، init ماژول، بارگذاری مدل، خروج از در. شواهد فایل فقط می‌توانند حلقه‌های مشکوک را جدا کنند.

## روسیه — RS-24 Yars

### مسیر زنده

| حلقه | نتیجه روی DATA قابل نصب |
| --- | --- |
| دکمهٔ اصلی WF | `Command_ConstructRussiaVehicleRS24` → `RussiaVehicleRS24` |
| کارخانه | `RussiaWarFactory` → `RussiaWarFactoryCommandSet` اسلات ۱۳ = همان دکمه |
| Object ساخته‌شده | `RussiaVehicleRS24` (موجود بود؛ اصلاح قبلی آن را عوض نکرد) |
| `Command_ConstructRussia_RS24_Yars` | همچنان `Object = Russia_RS24_Yars` (نام موجود نیست) |
| T3 / LBD | اسلات ۷ = دکمهٔ ناموجود. اگر تایمر ۲۲ث تمام شده، بازیکن دکمهٔ اصلی را زده نه T3 |

اصلاح قبلی یک کپی کامل به نام `Russia_RS24_Yars` اضافه کرد. دکمهٔ اصلی کارخانه هرگز به آن نام نمی‌رود. بنابراین آن اصلاح نمی‌توانست Crash لحظهٔ آماده‌شدن موشک روی WF اصلی را عوض کند.

### مقایسه با واحد سالم

`RussiaVehicle9K720` و `Russia_RS24_Yars_AI` در لحظهٔ ایجاد:

- `WeaponSet Conditions = None`
- بدون `RiderChangeContain` / `InitialPayload`
- `KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE`
- AI همان Drawهای RUS_RS24 را دارد (مدل‌ها در ART TWO هستند)

نسخهٔ بازیکن قبل از اصلاح:

- فقط `WEAPON_RIDER1` / `WEAPON_RIDER2` — هیچ WeaponSet پیش‌فرض
- `InitialPayload = GenericFakeRider1_Default_Rank` با `GeometryHeight = 10000000`
- `KindOf` اضافه: `HUGE_VEHICLE SALVAGER GARRISONABLE_UNTIL_DESTROYED`
- `Animation = RU_RS28_DA.RU_RS28_DA` و `RU_RS28_A.RU_RS28_A` — این W3Dها در ART TWO نیستند
- `Turret = TUT` / `TURRET` / `tut` روی بدنهٔ بدون آن استخوان. `CHI_DF21C` هم `Turrettt` مفقود دارد و سالم است؛ استخوان Turret علت قطعی فرض نشد
- `FireWeaponUpdate` / `DecalCollisionDummyWeapon` — `RussiaVehicleKrasukha4` روی همین WF هم دارد؛ علت منحصر فرض نشد
- `Generic8x8Locomotor_H` در `Locomotor.ini` هست؛ AI هم همان را دارد. سرعت عوض نشد

### مرحلهٔ مشکوک (فایل، نه اجرا)

مشکوک‌ترین حلقه برای روسیه: ایجاد Object در کارخانه (مرحلهٔ ۳–۴، شاید ۶).

- `DefaultProductionExitUpdate` واحد را می‌سازد.
- بلافاصله `InitialPayload` یک رایدر ۱۰ میلیون‌واحدی داخل Contain می‌سازد.
- `GARRISONABLE_UNTIL_DESTROYED` روی همان Contain در خروج کارخانه می‌تواند تداخل بدهد.
- بدون WeaponSet پیش‌فرض، lookup سلاح قبل از اعمال رایدر خالی است.
- اگر Draw در create همهٔ `TransitionKey`ها را بار کند، مدل‌های مفقود `RU_RS28_*` هم در همان لحظه لمس می‌شوند. این مرحله بدون بازی نامشخص است.

### اصلاح روسیه

Last-win همان Object زنده `RussiaVehicleRS24` در `zzzzz_SpecterRs24Df41Spawn`:

1. `WeaponSet Conditions = None` هم‌تراز حالت خلع‌سلاح (Tertiary = `DeployHeavyWeapons`).
2. `CommandSet = RussiaVehicleRS24_UnarmedRearmSet` — همان ستی که بعد از رایدر اولیه اعمال می‌شد؛ دکمهٔ Rearm می‌ماند.
3. `InitialPayload` حذف شد. `RiderChangeContain` و OCL Rearm ماند تا شارژ مجدد بعداً Rider2 بسازد.
4. `KindOf` هم‌تراز 9K720 / AI.
5. ارجاع `RU_RS28_*` حذف شد. مدل همان `RUS_RS24_DA` / `RUS_RS24_A` ماند.

قیمت ۳۵۰۰، زمان ۲۲ث، Side=Russia، هر دو کلاهک، Drawهای RUS_RS24، Locomotor و قانون شلیک عوض نشدند. Object تکراری اضافه نشد.

## چین — DF-41

### مسیر زنده

| حلقه | نتیجه روی DATA قابل نصب |
| --- | --- |
| دکمه | `Command_ConstructChinaVehicleDF41` → `ChinaVehicleDF41` (موجود) |
| کارخانه | `ChinaWarFactory` → `PLAWarFactoryCommandSet` اسلات ۴ و ۷ = همان دکمه |
| اصلاح قبلی | سه Draw (Tires / WL / HL) حذف شد؛ Crash ماند |

### مقایسه با DF-21C / DF-17 / AI

AI برخلاف گزارش قبلی **همان Drawهای اضافه را دارد** (`CHI_DF41_T` / `_WL` / `HL` که در ART TWO نیستند). «AI بدون آن Drawها کار می‌کند» از روی فایل درست نیست. AI در اسلات ۱۵ است و ساخته‌شدنش در بازی تأیید نشده.

تفاوت بازیکن با AI و DF-21C در لحظهٔ ایجاد (بعد از رد شدن فرض Draw):

- بازیکن: `RiderChangeContain` + `InitialPayload` — AI ندارد
- بازیکن: بدون WeaponSet پیش‌فرض — AI و DF-21C دارند
- بازیکن: `HUGE_VEHICLE SALVAGER GARRISONABLE_UNTIL_DESTROYED` — AI / DF-21C ندارند
- بازیکن: دو `FireWeaponUpdate` — AI ندارد؛ یکهٔ قطعی نیست
- هر دو: `Generic8x8Locomotor_H`
- `CHI_DF41` / `_A` / `_AD` / Camo / `DF41_Bones` در ART TWO هستند
- `CHI_DF41_A` انیمیشن داخل W3D ندارد؛ AI هم `CHI_DF41_A.CHI_DF41_A` دارد

حذف بیشتر Draw انجام نشد.

### مرحلهٔ مشکوک (فایل، نه اجرا)

مشکوک‌ترین حلقه برای چین: ایجاد Object و init ماژول (مرحلهٔ ۳–۴)، نه بارگذاری مدل‌های WL/HL (آن فرض در بازی رد شد).

همان مسیر Contain + رایدر تودرتو + KindOf پادگان + نبود WeaponSet پیش‌فرض. استخوان `TUT` روی `CHI_DF41` نیست، ولی DF-21C هم استخوان Turret ناموجود دارد؛ علت قطعی اعلام نشد.

### اصلاح چین

Last-win همان `ChinaVehicleDF41`، مستقل از روسیه، بدون حذف Draw:

1. `WeaponSet Conditions = None` خلع‌سلاح.
2. `CommandSet = ChinaVehicleDF41_UnarmedRearmSet`.
3. `InitialPayload` حذف شد؛ `RiderChangeContain` و OCL Rearm ماند.
4. `KindOf` هم‌تراز DF-21C / AI.

قیمت ۳۵۰۰، زمان ۲۲ث، Side=China، کلاهک‌های `ICBM_DF41_1x_300kt_Warhead` و `DF41_ICBM_6x_Warhead_Missile`، Drawها، Locomotor و قانون شلیک عوض نشدند.

## چیزهایی که دست نخورده ماند

Missile Factory، Supply Centre، DataLink رادار، CommandSet/CommandButton هسته، ART، کارخانه و موشک کشورهای دیگر، Object مستعار `Russia_RS24_Yars`.

## اعتبارسنجی استاتیک

- Overlay قدیمی `zzzzz_SpecterRs24Df41Crash` در BIG جدید نیست.
- Last-win هر دو Object در `zzzzz_SpecterRs24Df41Spawn` است.
- بلوک CommandSet داخل Object/ نیست.
- دکمه‌های UNIT_BUILD همان Objectهای قبلی را می‌سازند.
- T3/LBD روسیه همچنان به نام مفقود `Russia_RS24_Yars` می‌رود (کلیک/صف، نه تایمر WF اصلی).
- Last-winهای عراق رادار، Supply Centre، و DataLink 92N6E سر جایشان هستند.
- تست داخل بازی: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 050 383 | `4fe03adf2e3d8dcc9a76fc0f5c066be54d6113f6ce698ddc157b8139f2e964ee` |

ورودی‌ها: ۳۵۷۲ → ۳۵۷۴. این فایل همان `rs24-df41-wf-crash` / `wf-fix-commandset-crash` / `wf-detach` / `wf-remove` نیست.

## نصب

فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید. ART را عوض نکنید.

هم‌زمان نصب نکنید: DATAهای `rs24-df41-wf-crash`، `wf-fix-commandset-crash`، `wf-detach-sarab7-9p117-alabbas`، `wf-remove-sarab7-9p117-alabbas`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
