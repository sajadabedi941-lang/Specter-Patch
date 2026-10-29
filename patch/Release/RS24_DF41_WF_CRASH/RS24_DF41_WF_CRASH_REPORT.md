# RS-24 Yars / DF-41 War Factory construct crash

**بازی اجرا نشد.** Zero Hour در این محیط نیست. رفع Crash تأیید قطعی داخل بازی نیست.

لاگ داخل بازی در دست نیست. دو لحظه از هم جدا شده‌اند و برای هر موشک علت جدا گزارش می‌شود.

## منبع

ورودی: Release `wf-restore-warfactory-buttons` (`_SPEC_DATA_ONE.big`، SHA-256 `242a7c81…`، ۳۵۷۲ ورودی).
ART بررسی‌شده: `_SPEC_ART_TWO.big` از `WORLD_WAR_III2027-Full-Release` (مدل‌های W3D). ART تغییر نکرد.

## روسیه — RS-24 Yars

| حلقه | نتیجه روی DATA قابل نصب |
| --- | --- |
| دکمهٔ `Command_ConstructRussia_RS24_Yars` | `UNIT_BUILD` → `Object = Russia_RS24_Yars` |
| Object `Russia_RS24_Yars` قبل از اصلاح | **وجود ندارد** |
| Object زندهٔ بازیکن | `RussiaVehicleRS24` در `…\Wheeled\RS-24_Yars.ini` |
| مدل‌های `RussiaVehicleRS24` در ART TWO | همه هستند (`RUS_RS24` / `_T` / `_WL` / `HL` / Camo / Bones) |
| WF اصلی `RussiaWarFactory` | `RussiaWarFactoryCommandSet` اسلات ۱۳ = `Command_ConstructRussiaVehicleRS24` (Object موجود) |
| `RussiaWarFactoryCommandSet_T3` / `_LBD` | اسلات ۷ = `Command_ConstructRussia_RS24_Yars` (Object مفقود) |

اگر نوار زنده‌ای که بازیکن می‌زند همان دکمهٔ `Command_ConstructRussia_RS24_Yars` باشد، Crash هنگام **کلیک / ورود به صف** است: UNIT_BUILD به نامی اشاره می‌کند که ThingFactory ندارد.

اگر فقط دکمهٔ `Command_ConstructRussiaVehicleRS24` زده شود، نام Object موجود است و مدل‌ها در ART TWO هستند؛ آن مسیر از نظر فایل Crash ندارد. بدون اجرای بازی نمی‌توان گفت بازیکن کدام دکمه را می‌زند. نام «RS_24Yars» با دکمهٔ شکسته یکی است.

اصلاح: last-win `Object Russia_RS24_Yars` کپی همان‌آمار `RussiaVehicleRS24` (قیمت ۳۵۰۰، زمان ۲۲ث، Side=Russia، همان دو کلاهک). `RussiaVehicleRS24` دست نخورده ماند.

## چین — DF-41

| حلقه | نتیجه روی DATA قابل نصب |
| --- | --- |
| دکمهٔ `Command_ConstructChinaVehicleDF41` | `UNIT_BUILD` → `Object = ChinaVehicleDF41` (موجود) |
| WF چین `ChinaWarFactory` | `PLAWarFactoryCommandSet` اسلات ۴ و ۷ = همان دکمه |
| مقایسه با DF-21C / DF-17 سالم | آن‌ها یک `W3DTruckDraw` دارند؛ DF-41 چند Draw اضافه مثل RS-24 دارد |
| `CHI_DF41` / `_A` / `_AD` / `D` / Camo / `DF41_Bones` | در ART TWO هستند |
| `CHI_DF41_WL` ، `CHI_DF41HL` ، `CHI_DF41_T` ، `CHI_DF41_TD` | **در ART TWO نیستند** |
| `ModuleTag_Tires` | `Model = None` به‌جای تایر مفقود |

نام Object دکمه موجود است؛ این Crash از نوع «Object مفقود هنگام کلیک» نیست. Drawهای اضافه‌ای که W3D ندارند هنگام **ساخته‌شدن / init رسم Object** Crash می‌دهند. DF-41_AI آن Drawهای مفقود را ندارد.

اصلاح: last-win همان Object با حذف فقط `ModuleTag_Tires` / `WarningLights` / `HeadLights`. بدنه، Camo، Bones، قیمت ۳۵۰۰، زمان ۲۲ث، Side=China، `ICBM_DF41_1x_300kt_Warhead` و `DF41_ICBM_6x_Warhead_Missile` ماندند.

## چیزهایی که دست نخورده ماند

Missile Factory، Supply Centre، DataLink رادار، CommandSet/CommandButton هسته، ART، کارخانه و موشک کشورهای دیگر.

## اعتبارسنجی استاتیک

- `Russia_RS24_Yars` حالا last-win در `zzzzz_SpecterRs24Df41Crash` است و Side/قیمت/زمان/سلاح با `RussiaVehicleRS24` یکی است.
- `ChinaVehicleDF41` last-win همان پوشه است؛ `Model=None` و W3Dهای مفقود نیستند؛ CHI_DF41 و DF41_Bones هستند.
- بلوک CommandSet داخل Object/ نیست.
- تست داخل بازی: **اجرا نشد.**

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 049 400 | `a5514eac1a0f8cc497ee32ccac498c3b79121e646f4f233bcee11c3a346598be` |

ورودی‌ها: ۳۵۷۲ → ۳۵۷۴. این فایل همان `wf-fix-commandset-crash` / `wf-detach` / `wf-remove` نیست.

## نصب

فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید. ART را عوض نکنید.

هم‌زمان نصب نکنید: DATAهای `wf-fix-commandset-crash`، `wf-detach-sarab7-9p117-alabbas`، `wf-remove-sarab7-9p117-alabbas`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
