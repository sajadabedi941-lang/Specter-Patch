# ممیزی فقط‌خواندنی — خودروهای متحرک رادار و پرتابگر Patriot و Iron Dome

تاریخ: **۲ نوامبر ۲۰۲۶، ۱۸:۳۰ به وقت ایران (Asia/Tehran)**  
مخزن: `sajadabedi941-lang/Specter-Patch`  
وضعیت: هیچ فایل بازی تغییر نکرد. هیچ واحدی ساخته نشد. New donor استفاده نشد. Zero Hour اجرا نشد.

لایه‌های بررسی‌شده: overlay `patch/Data/` ، `_SPEC_DATA_ONE.big` و `_SPEC_ART_ONE.big` از `art_data` (۲۰۲۶-۰۸-۱۸)، و `_SPECTER_PATCH_FINAL.big`.

معیار «خودروی متحرک»: `Locomotor` + نبود `IMMOBILE` + شاسی/چرخ در Object یا مش W3D. صرف `W3DTruckDraw` یا `EditorSorting = VEHICLE` حرکت نمی‌دهد.

صرف نام Object معادل سامانه دانسته نشد.

---

## نتیجه چهار بخش

| دسته | نتیجه | Object / مدل اصلی | آیا همان خودرو قابل استفاده است؟ |
|---|---|---|---|
| **Patriot Radar Vehicle** | **موجود ولی ثابت** | `AmericaRadarAN/MPQ65` / `US_AN_MPQ65.W3D` | بله — مدل AN/MPQ-65 با شاسی و لاستیک موجود است. مدل جدید لازم نیست. Object فعلی `IMMOBILE` است. |
| **Patriot Launcher Vehicle** | **موجود ولی ثابت** + **مدل بدون Object فعال** | لانچر زنده: `America_MIM104F_Launcher` / `US_MIM104F_L.W3D` ؛ کامیون کامل بی‌Object: `US_MIM104F.W3D` | بله — مدل جدید لازم نیست. بهترین کاندید متحرک همان `US_MIM104F.W3D` است که هیچ Objectی آن را صدا نمی‌زند. |
| **Iron Dome Radar Vehicle** | **موجود ولی ثابت** | `IsraelRadarIronDish` / `Isr_IrnDmRadar.W3D` | مدل رادار اختصاصی برای نسخه تریلر/ثابت قابل استفاده است. برای کامیون رادار چرخ‌دار شبیه EL/M-2084 مدل جدید لازم است (مش فعلی Tire ندارد). |
| **Iron Dome Launcher Vehicle** | **موجود ولی ثابت** | `ISI_IroneDome` / `Isr_Ironedome_l.W3D` | مدل تریلر لانچر برای سایت ثابت قابل استفاده است. برای کامیون متحرک مدل جدید لازم است. واحد overlay `Israel_AD_IronDome` متحرک است ولی Pantsir است و نباید استفاده شود. |

هیچ‌کدام **کاملاً پیدا نشد** نیستند. هیچ رادار/لانچر authentic با `Locomotor` برای این دو سامانه پیدا نشد.

---

# Patriot Radar Vehicle

**نتیجه: موجود ولی ثابت**

### Object زنده

| فیلد | مقدار |
|---|---|
| Object | `AmericaRadarAN/MPQ65` |
| نام نمایشی CSF | `OBJECT:ANMPQ65` = `AN/MPQ65 Radar / AESA / Multi Track` |
| Side | America |
| فایل | `_SPEC_DATA_ONE.big` → `Data/INI/Object/Specter/United States Of America/AirDefense Installation/AN_MPQ65.ini` |
| در overlay | این فایل در `patch/Data` نیست؛ تعریف packed DATA زنده است |

### مدل سه‌بعدی

- `Art/W3D/US_AN_MPQ65.W3D` و بافت `Art/Textures/US_MPQ65.dds` در `_SPEC_ART_ONE.big` **موجود** است.
- داخل مش: `CHASSIS` ، `TIRES` ، `AN/MPQ65` ، `ARMS` ، `JAGS`.
- ظاهر با رادار آرایه‌ای Patriot (AN/MPQ-65) روی شاسی چرخ‌دار سازگار است — نه صرفاً شباهت نام.

Draw در INI از نوع `W3DTruckDraw` است ولی **TireBone تعریف نشده** و **Locomotor نیست**.

### حرکت

| مورد | وضعیت |
|---|---|
| KindOf | `VEHICLE IMMOBILE` |
| Locomotor | پیدا نشد |
| Physics | `Mass = 300` |
| Body | `ActiveBody` سلامت ۸۰۰ |
| CommandSet | `None` — از منو جدا ساخته نمی‌شود |

### سلاح و نقش رادار

شلیک موشک ندارد. `FireWeaponUpdate` با `AN_MPQ65_WaveEmitter` و `StealthDetectorUpdate` برد ۹۷۰ (کشف، غیرپیاده).

ارتباط با Patriot: سایت `America_MIM104F` سلاح `SpawnMPQ65ViaWeapon` را شلیک می‌کند → `OCL_AmericaSpawnMpq65ViaWeapon` Object `AmericaRadarAN/MPQ65` را می‌سازد. CSF سایت: «needs its radar active to work».

### کلون‌ها (معادل رادار متحرک Patriot نیستند مگر ذکر شود)

| Object | مدل | حرکت | توضیح |
|---|---|---|---|
| `AmericaRadarMPQ65ST` | `US_AN_MPQ65` | ثابت STRUCTURE | سلاح `MPQ65_FCR` |
| `ArabRadarAN/MPQ65E` | `Arb_AN_MPQ65E` | IMMOBILE | کلون عربی؛ مش شاسی+لاستیک دارد |
| `America_MPQ65_AI_Spawner` / `ISI_MPQ65_AI_Spawner` | AI | — | اسپانر هوش مصنوعی |
| **`US_AN_TPY2`** | `US_AN_TPY2` با Tire01–10 | **متحرک** (`Generic8x8Locomotor`) | رادار **THAAD** است نه Patriot. CSF: needed for THAAD. معادل AN/MPQ-65 اعلام نشد. |

### آیا می‌توان از همین خودرو استفاده کرد؟

**بله، مدل جدید لازم نیست.** `US_AN_MPQ65.W3D` شاسی و لاستیک دارد. Object فعلی ثابت و برده سایت است؛ برای نسخه متحرک باید تعریف INI جدا با Locomotor نوشته شود (این کار در این ممیزی انجام نشد).

---

# Patriot Launcher Vehicle

**نتیجه: موجود ولی ثابت (لانچر زنده) + مدل کامیون کامل بدون Object فعال**

### A) لانچر زنده سایت — ثابت

| فیلد | مقدار |
|---|---|
| Object | `America_MIM104F_Launcher` و `America_MIM104F_ABM_Launcher` |
| DisplayName | `OBJECT:MIM104F` = `MIM104F Patriot / PAC3 Missiles / ABM / AAM` |
| Side | America |
| فایل | `…/AirDefense Installation/MIM_104F.ini` و `MIM_104F_ABM.ini` در DATA BIG |
| مدل | `US_MIM104F_L.W3D` — مش `CHASSIS` ، `TIRES` ، `LAUNCHER` ، `TURRET` ، `MISSILE01–04` |
| Draw | `W3DTruckDraw` بدون TireBone |
| KindOf | `CAN_ATTACK … CLICK_THROUGH SPAWNS_ARE_THE_WEAPONS` — برده سایت |
| Locomotor | پیدا نشد |
| Physics / Body | Mass 500 / سلامت ۱۰۰۰ |
| Weapon | AA: `12x_LRSAM_PAC3F_MSE` ؛ ABM: `10x_PAC3_MSE_ABM` — **قابل شلیک** |

سایت `America_MIM104F` (مدل پد `Spec_SamUsCnfg`، KindOf `IMMOBILE STRUCTURE`) این لانچرها را spawn می‌کند.

### B) مدل کامیون کامل — بدون Object

`Art/W3D/US_MIM104F.W3D` (۲۲۵۷۵۰ بایت) در ART موجود است و مش کامل‌تری دارد: دو مجموعه `CHASSIS/TIRES/LAUNCHER/TURRET`.  
جستجوی تمام INIهای DATA BIG: هیچ خط `Model = US_MIM104F` (بدون `_L`) وجود ندارد.

**وضعیت: مدل موجود ولی بدون Object فعال.** این نزدیک‌ترین دارایی به «خودروی متحرک پرتابگر Patriot» است.

### C) واحد overlay متحرک — ظاهر غلط

`America_AD_Patriot` در overlay: `Locomotor = Generic8x8Locomotor`، Tire01–08، Side=America، از HQ اسلات ۴ قابل ساخت. مدل **`Irq_Fahad3`** (فهد-۳ عراق). **موجود و متحرک است ولی پرتابگر Patriot نیست.** استفاده از آن به‌جای مدل MIM-104 توصیه نمی‌شود.

`AmericaMobileSamSiteMIM104F`: کامیون `US_M1075` متحرک که با ارتقا به سایت ثابت تبدیل می‌شود — ظاهر لانچر Patriot نیست.

### آیا می‌توان از همین خودرو استفاده کرد؟

**بله، مدل جدید لازم نیست.** برای لانچر ثابت همان `US_MIM104F_L` کافی است. برای خودروی متحرک باید Object جدید روی **`US_MIM104F.W3D` بی‌استفاده** سوار شود، نه وارد کردن مدل خارجی.

---

# Iron Dome Radar Vehicle

**نتیجه: موجود ولی ثابت**

### Object زنده

| فیلد | مقدار |
|---|---|
| Object | `IsraelRadarIronDish` |
| DisplayName | `OBJECT:IronDish` — **این کلید در generals.csf پیدا نشد** |
| Side | `AmericaAirForceGeneral` (اسرائیل packed DATA) |
| فایل | `_SPEC_DATA_ONE.big` → `Data/INI/Object/Specter/Israel Defense Forces/AirDefense Sites/IronRadar.ini` |

### مدل سه‌بعدی

- `Art/W3D/Isr_IrnDmRadar.W3D` **موجود** است.
- مش: `BASE` ، `TURRET` ، `APU` ، `RDDSKB`. **Tire / Chassis کامیون در مش نیست.**
- بافت `US_MIM104F.dds` (قرض از Patriot).
- Draw: `W3DModelDraw` نه TruckDraw.

ظاهر با رادار آرایه‌ای روی پایه/تریلر سازگارتر است تا کامیون ۶×۶ EL/M-2084.

### حرکت

KindOf: `VEHICLE IMMOBILE`. Locomotor نیست. Physics Mass 300. CommandSet None.

سایت `AirF_AmericaPatriotBattery` سلاح `SpawnIronDishViaWeapon` → `OCL_ZGFSpawnIronDishViaWeapon` این رادار را می‌سازد. پس به سامانه Iron Dome packed وصل است.

سلاح رادار: `AN_MPQ65_WaveEmitter` (کد Patriot قرضی) + StealthDetector.

حفره آسیب `IsraelRadarIronDishDamaged` به‌اشتباه مدل `US_AN_MPQ65` دارد.

### موارد مشابه که Iron Dome نیستند

- `Israel_AN_TPY2` / `US_AN_TPY2`: رادار متحرک با لاستیک و Locomotor؛ CSF آن را به THAAD/Arrow می‌بندد نه Iron Dome.
- `Israel_RadarStation`: ساختمان ثابت.

### آیا می‌توان از همین خودرو استفاده کرد؟

- برای رادار تریلر/ثابت سایت: **بله، مدل جدید لازم نیست** (`Isr_IrnDmRadar`).
- برای خودروی کامیونی متحرک شبیه تصویر مرجع EL/M-2084: **مدل جدید لازم است** چون مش فعلی چرخ ندارد. TPY-2 را به‌خاطر شباهت «رادار روی کامیون» معادل Iron Dome ندانید.

---

# Iron Dome Launcher Vehicle

**نتیجه: موجود ولی ثابت**

### Object زنده authentic

| فیلد | مقدار |
|---|---|
| Object | `ISI_IroneDome` و `ISI_IroneDome_ABM` |
| DisplayName | `OBJECT:IroneDome` = `Irondome / Multitargeting / Multitracking / Jam Resist` (کلید ABM در CSF نیست) |
| Side | AmericaAirForceGeneral |
| فایل | `…/AirDefense Sites/IroneDome_AA.ini` و `IroneDome_ABM.ini` در DATA BIG |
| مدل | `Isr_Ironedome_l.W3D` |

مش W3D: `BASE` ، `LAUNCHER` ، `HANDLE` ، `APU` ، `COMMS` ، `WEAPONA01–04`. **Tire نیست.** داخل فایل `ClonedFromObject` و بافت `US_MIM104F.dds` است (از لانچر Patriot کلون شده).

KindOf: `CAN_ATTACK … CLICK_THROUGH SPAWNS_ARE_THE_WEAPONS`. Locomotor نیست. Physics Mass 100.

سلاح: `IroneDome_AA` و `IroneDome_ABM` (ABM فلگ بالستیک دارد) — **قابل شلیک**. پرتابه `ISI_IroneDome_M.W3D`.

سایت `AirF_AmericaPatriotBattery` این لانچرها را spawn می‌کند (اسلات ۷ بولدوزر AirF).

### واحد overlay متحرک — ظاهر غلط

`Israel_AD_IronDome`: `Locomotor = Generic8x8Locomotor`، لاستیک، از HQ اسرائیل اسلات ۱ قابل ساخت. مدل **`RUS_9K96S2` Pantsir** و سلاح `57E6M-R`. **موجود و متحرک است ولی پرتابگر Iron Dome نیست.** استفاده از آن توصیه نمی‌شود.

### آیا می‌توان از همین خودرو استفاده کرد؟

- برای لانچر تریلر سایت: **بله** (`Isr_Ironedome_l`).
- برای خودروی کامیونی متحرک شبیه تصویر مرجع: **مدل جدید لازم است** (مش بدون چرخ). Pantsir overlay جایگزین نیست.

---

## جمع‌بندی استفاده مجدد مدل

| نیاز | مدل موجود | وارد کردن مدل جدید؟ |
|---|---|---|
| رادار Patriot متحرک | `US_AN_MPQ65.W3D` (شاسی+لاستیک) | خیر |
| پرتابگر Patriot متحرک | `US_MIM104F.W3D` بی‌Object (شاسی+لاستیک+لانچر) | خیر |
| رادار Iron Dome تریلر/ثابت | `Isr_IrnDmRadar.W3D` | خیر |
| رادار Iron Dome کامیونی | مش چرخ‌دار اختصاصی نیست | **بله** |
| پرتابگر Iron Dome تریلر/ثابت | `Isr_Ironedome_l.W3D` | خیر |
| پرتابگر Iron Dome کامیونی | مش چرخ‌دار اختصاصی نیست | **بله** |

ارتباط سامانه‌ای همین حالا در DATA هست: سایت MIM-104F → لانچر PAC-3 + رادار MPQ-65 ؛ سایت Iron Dome → لانچر `ISI_IroneDome` + رادار `IsraelRadarIronDish`. هر دو زنجیره روی پد ثابت‌اند نه خودروهای مستقل قابل راندن.

---

## خروجی‌ها

- Markdown: `docs/specter-patriot-iron-dome-mobile-vehicles/SPECTER_PATRIOT_IRON_DOME_MOBILE_VEHICLES_AUDIT.md`
- Excel: `docs/specter-patriot-iron-dome-mobile-vehicles/SPECTER_PATRIOT_IRON_DOME_MOBILE_VEHICLES_AUDIT.xlsx`  
  برگه‌ها: Verdict, Patriot_Radar, Patriot_Launcher, IronDome_Radar, IronDome_Launcher, Related_Not_Match, W3D_Assets, MethodNotes
