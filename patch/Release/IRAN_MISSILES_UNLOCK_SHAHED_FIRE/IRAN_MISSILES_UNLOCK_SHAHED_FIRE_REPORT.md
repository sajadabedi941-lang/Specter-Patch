# Iran missiles unlock + Shahed-136 Fire (follow-up to PR #706)

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` در این محیط نیستند. هیچ تست داخل بازی انجام نشده است. اعتبارسنجی فقط ایستا روی BIG زنده است. ادعای رفع قطعی داخل ZH نمی‌شود.

منبع DATA: Release `iran-khorramshahr-shahed136` / PR #706
(`_SPEC_DATA_ONE.big`، ۳۵۷۳ ورودی، SHA `592b49746f14425213309be1cabc5343a1b98aefe9dd977cb27f3cb8e82a1eb4`).

## چرا PR #706 در ZH شکست خورد

درس RS-24/DF-41 اینجا هم برقرار است: **نام Object اول ثبت‌شده زنده است.** Overlay `Object_ZZZZ_*` last-win برای `IranVehicleKhormshar` در تست واقعی کاربر قفل را برنداشت.

| مسیر | چیزی که #706 عوض کرد | چیزی که بازی می‌خواند |
| --- | --- | --- |
| `IranVehicleKhormshar` | فقط overlay `Object_ZZZZ_ZzGlobalStoreFivePrereq.ini` (Prereq خالی، زمان ۱۰، Armed CS) | **اول** `Khormshar.ini`: `IranIndustrialComplex`، زمان ۲۲، `Iraq_AlhussaienCommandSet` + ساینس، Rider1 خلع‌سلاح |
| `IranVehicleFattah` | overlay: `WarFactory + GlobalStore + Radar` (قفل ماند) | **اول** `Fattah.ini`: `WarFactory AND IndustrialComplex AND Radar` |
| `Fattah2` / `ZolfagharM` / `DezfulPenetrator` | overlay: `GlobalStore` (+ Radar روی Fattah2) | **اول** `Iran_System.ini`: `IndustrialComplex` (+ Radar روی Fattah2) |
| `Iran_MissileFactory` | دست نخورده | تنها تعریف: AND حدود ۲۰ `SupplyCenter` کشور دیگر → کارخانه ساخته نمی‌شود → هر ۱۰ TEL قفل |
| `IranVehicleShahedLauncher` | `Scud_B_CommandSet` + `Weapon_Iran_Shahed136Launcher` با پرتابه `Shahed136_AI_Object` | همان فایل اول؛ Fire همچنان مرده |

`Scud_B_CommandSet` و `Command_FireMainWeapon` فقط در `CommandSet.ini` / `CommandButton.ini` هستند. این مسیرها STOCK هستند و INIZH می‌تواند first-win کند. وجود سلاح یکتا به‌تنهایی Fire را روشن نمی‌کند.

`Shahed136_AI_Object` پهپاد است (`KindOf = PRELOAD SELECTABLE CAN_ATTACK PROJECTILE SMALL_MISSILE`، `MissileAIUpdate`، `EditorSorting = VEHICLE`). Fateh313 زنده از `SRBM_Fateh313_Object` با `KindOf = PROJECTILE BALLISTIC_MISSILE` و `DumbProjectileBehavior` شلیک می‌کند.

## اصلاح روی مسیر زنده

First-win و last-win هر دو برای واحدهای تکراری هم‌تراز شدند. CommandSet/Button شلیک نام یکتا در فایل extra است و Object به همان نام اشاره می‌کند. ART نیست.

## فهرست موشک‌های بررسی‌شده

ساخت از War Factory (`IranWarfactoryCommandSet`، تنها در `CommandSet.ini`):

| واحد | Object | اسلات | علت قفل #706 | اصلاح این Release | Fire |
| --- | --- | ---: | --- | --- | --- |
| Fateh-313 | `IranVehicleFateh313` | ۸ | قفل نبود (`Prerequisites` خالی، `Scud_B` + پرتابه بالستیک) | دست نخورده | همان الگوی سالم |
| خرمشهر | `IranVehicleKhormshar` | ۹ | first-win: `IranIndustrialComplex` + Rider1 خلع‌سلاح + `Command_TacticalStrike` با `NEED_SPECIAL_POWER_SCIENCE` | first+last: Prereq خالی، `BuildTime=10`، `WeaponSet None` + `Khormshar1_ICBM`، rider/rearm حذف، `IranKhorramshahrFireCommandSet` | دکمه یکتای SECONDARY بدون ساینس |
| Fattah | `IranVehicleFattah` | ۱۰ | first-win AND سه ساختمان | first+last Prereq خالی | `Scud_B` مثل Fateh؛ سلاح `2x_SRSSBM_Fattah` عوض نشد |
| Shahed-136 | `IranVehicleShahedLauncher` | ۱۱ | قفل ساخت نبود؛ Fire مرده | CS یکتا + پرتابه بالستیک | مسیر زیر |
| BM-21 | `IranVehicleBM21` | ۷ | قفل نبود | دست نخورده | `Smerch_CommandSet` |
| خرمشهر AI | `IranVehicleKhormshar_AI` | ۱۵ | قفل ساخت نبود | دست نخورده (واحد AI جدا) | — |

ساخت از Expanded HQ (`IranExpandedHQCommandSet`):

| واحد | Object | اسلات | علت قفل | اصلاح |
| --- | --- | ---: | --- | --- |
| Dezful Penetrator | `IranVehicleDezfulPenetrator` | ۲ | first `IranIndustrialComplex` / last `Iran_GlobalStore` | هر دو خالی |
| Zolfaghar-M | `IranVehicleZolfagharM` | ۴ | همان | هر دو خالی |
| Fattah-2 | `IranVehicleFattah2` | ۵ | first `IndustrialComplex+Radar` / last `GlobalStore+Radar` | هر دو خالی |
| Hoveyzeh | `IranVehicleHoveyzeh` | ۱۲ | قفل نبود | دست نخورده |
| خرمشهر | همان Object WF | ۹ | بالا | بالا |

ساخت از Missile Factory (`CB_IRAN_MISSILE_A`–`J` → `Iran_Hormuz` / `Qader` / `Qiam` / `Emad` / `Khalij` / `Dezful` / `Khorram` / `Kheibar` / `Ghadr` / `Simorgh`):

هر ده TEL از قبل بدون Prerequisites واحد و با `Scud_B_CommandSet` مسلح بودند. قفل مشترک **خود کارخانه** بود: `Prerequisites Object = IranSupplyCenter AND` بیست Supply کشور دیگر.

اصلاح: تنها تعریف `Iran_MissileFactory.ini` → `Object = IranSupplyCenter`. دکمه‌های A–J و سلاح/هزینه TELها عوض نشد. `Iran_Khorram` همچنان `BuildTime=10`.

`IranSejjilSilo` سیلو/سوپروپن است، TEL نیست؛ Prerequisites آن عمداً دست نخورده ماند.

`Iran_KhorramshahrTEL` در BIG زنده وجود ندارد.

## Shahed-136 — علت واقعی Fire و اصلاح

مقایسه با Fateh313 زنده (شلیک‌پذیر):

| | Shahed بعد از #706 | Fateh313 |
| --- | --- | --- |
| CommandSet | `Scud_B_CommandSet` (فقط در `CommandSet.ini`) | همان |
| سلاح | `Weapon_Iran_Shahed136Launcher` AntiGround/3000 | `2x_SRBM_Fateh313_HE` |
| پرتابه | `Shahed136_AI_Object` پهپاد قابل انتخاب | `SRBM_Fateh313_Object` بالستیک گنگ |
| AI پرتابه | `MissileAIUpdate` | `DumbProjectileBehavior` |
| KindOf پرتابه | `SELECTABLE CAN_ATTACK PROJECTILE SMALL_MISSILE` | `PROJECTILE BALLISTIC_MISSILE` |

وجود `AntiGround = Yes` سلاح را شلیک‌پذیر نمی‌کند اگر پرتابه واحد مهاجم باشد.

بعد:

1. Object به `IranShahed136FireCommandSet` (فایل extra یکتا) اشاره می‌کند — `Scud_B` مشترک کشورها ویرایش نشد.
2. دکمه `Command_IranFirePrimary` = `FIRE_WEAPON` PRIMARY `NEED_TARGET_POS` بدون ساینس.
3. پرتابه یکتای `Iran_Shahed136_FireProjectile`: مدل `Irn_Shahed136`، `KindOf = PROJECTILE BALLISTIC_MISSILE`، `DumbProjectileBehavior` (ارتفاع ۲۲۰/۹۰۰).
4. برد سلاح ۳۰۰۰ / حداقل ۲۰۰ / Vision ۳۰۰۰ / آسیب ۱۸۰۰ / هزینه ۱۵۰۰ / بدنه `Irn_ShhdLnchr*` حفظ شد.
5. `5x_Shahed136DroneSwarm` (لانچر رادار) همچنان ۱۵۰۰.

`DeployStyleAIUpdate` + `NEED_TARGET_POS` همان الگوی Fateh است: Unpack سپس شلیک. دکمه Deploy جدا روی Shahed نیست (Fateh هم ندارد؛ TERTIARY ندارد).

خرمشهر: `Command_IranFireSecondary` روی SECONDARY (`Khormshar1_ICBM`) + Deploy TERTIARY. هزینه ۲۵۰۰، مدل `Irn_Khormsh*`، نام `OBJECT:Khormshar` عوض نشد.

## چیزهایی که عمداً دست نخورد

- سلاح، مدل، نام، هزینه TELها و Fateh/BM-21/Hoveyzeh
- `Scud_B_CommandSet` / `Smerch_CommandSet` / `Iraq_Alhussaien*`
- Overlay غیر ایران (`RussiaVehicle96L6TSP` همچنان `Russia_GlobalStore`)
- Sejjil، ART، عراق رادار، Supply Centre، DataLink، RS-24

## اعتبارسنجی ایستا در برابر تست بازی

ایستا (انجام شد): first و last خرمشهر/Fattah/Fattah2/Zolfaghar/Dezful بدون IC/GlobalStore/Radar؛ کارخانه فقط `IranSupplyCenter`؛ Shahed CS/دکمه/سلاح/پرتابه بالستیک؛ برد ۳۰۰۰؛ swarm ۱۵۰۰؛ canaryهای قبلی سالم.

داخل ZH (انجام نشد): ساخت از دقیقه صفر، Fire خرمشهر، انتخاب هدف/شلیک/برد ۳۰۰۰ Shahed باید در بازی واقعی تأیید شود.

## BIG

| فایل | حجم | SHA-256 | ورودی |
| --- | ---: | --- | ---: |
| `_SPEC_DATA_ONE.big` | 374 011 409 | `b9b7317ea6e346bc45544287c3fbcc5b96693a2c82019500d72044cd024eb915` | 3576 |

در برابر #706: ۳ مسیر extra اضافه شد (دکمه، CommandSet، پرتابه) و ۷ مسیر زنده splice شد.

## نصب

فقط همین `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `b9b7317e…` شود. ART را عوض نکنید.

جایگزین کنید (هم‌زمان نگه ندارید): `iran-khorramshahr-shahed136`، `rs24-df41-factory-complete`، `rs24-df41-firstwin`، `rs24-df41-loco-crash`، `rs24-df41-spawn-crash`، `rs24-df41-wf-crash`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
