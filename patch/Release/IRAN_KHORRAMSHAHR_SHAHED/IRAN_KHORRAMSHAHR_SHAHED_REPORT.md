# Iran — Khorramshahr start-game + Shahed-136 Fire/range

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` اینجا نیستند. نتیجه داخل بازی تأیید نشده است.

## تعریف‌های زنده (نه loose INI)

منبع DATA: Release `rs24-df41-factory-complete` (۳۵۷۲ ورودی، SHA `4d74a2f4…`).

| واحد | نام Object زنده | مسیر last-win | دکمه ساخت | ساختمان |
| --- | --- | --- | --- | --- |
| خرمشهر ICBM | `IranVehicleKhormshar` | `Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini` (تعریف دوم/آخر) | `Command_ConstructIranVehicleKhormshar` اسلات ۹ | `IranWarFactory` / `IranWarfactoryCommandSet` |
| خرم (کارخانه موشک) | `Iran_Khorram` | `Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Khorram.ini` (تنها تعریف) | `CB_IRAN_MISSILE_G` اسلات ۷ | `Iran_MissileFactory` |
| Shahed-136 Mobile Launcher | `IranVehicleShahedLauncher` | `Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini` (تنها تعریف) | `Command_ConstructIranVehicleShahedLauncher` اسلات ۱۱ | همان War Factory |

`Iran_KhorramshahrTEL` و `Iran_Shahed136` در BIG زنده **وجود ندارند** (فقط loose PatchSystems).

`IranDroneShahed136` پهپاد جدا است؛ درخواست لانچر متحرک است.

## خرمشهر — علت قفل و اصلاح

تعریف اول `Khormshar.ini` زنده نیست. Overlay `Object_ZZZZ_ZzGlobalStoreFivePrereq.ini` last-win است.

قبل:

- `Prerequisites Object = Iran_GlobalStore` → بدون فروشگاه جهانی ساخته نمی‌شود
- `BuildTime = 22.0`
- `WeaponSet` فقط `WEAPON_RIDER1` (خلع‌سلاح) و `WEAPON_RIDER2` (`Khormshar1_ICBM`)
- `InitialPayload` رایدر ۱ + `RiderChangeContain` + `ObjectCreationUpgrade` rearm
- `CommandSet = Iraq_AlhussaienCommandSet` → `Command_TacticalStrike` با `NEED_SPECIAL_POWER_SCIENCE` / `Iraq_AlhussainMissile`

بعد (همان بلوک overlay، فایل جدید Object اضافه نشد):

- Prerequisites خالی
- `BuildTime = 10.0` (فیلد Object؛ زمان واقعی صف تولید SAGE)
- `WeaponSet Conditions = None` با همان `Khormshar1_ICBM` روی SECONDARY
- rider/rearm حذف شد
- `CommandSet = Iraq_AlhussaienArmedCommandSet` → `Command_IraqAlAbbasICBMFire` = `FIRE_WEAPON` SECONDARY بدون ساینس
- زیربلوک `Turret` مثل Fateh313

هزینه ۲۵۰۰، مدل `Irn_Khormsh*`، نام `OBJECT:Khormshar`، سلاح `Khormshar1_ICBM` عوض نشد.

`Iran_Khorram` (اسلات G کارخانه موشک، از قبل بدون پیش‌نیاز و با `Scud_B_CommandSet` مسلح): فقط `BuildTime 54.0 → 10.0`.

`IranVehicleFattah` و بقیه overlay همچنان `Iran_GlobalStore` دارند.

## Shahed-136 — علت نبود Fire و اصلاح

علت واقعی (ترکیبی، نه Tooltip):

1. `CommandSet = AmericaTankCrusaderCommandSet` زنده فقط اسلات ۱۱/۱۳/۱۴ دارد (`AttackMove` / `Guard` / `Stop`). دکمهٔ `FIRE_WEAPON` نیست. `AutoAcquireEnemiesWhenIdle = No` پس حملهٔ خودکار هم نیست.
2. سلاح `5x_Shahed136DroneSwarm`: `AttackRange = 1500`، `MinimumAttackRange = 1000`، **بدون `AntiGround`**. همان نام را `SpecterRadar_ShahedLauncher` هم دارد؛ last-win آن سلاح ممنوع بود.

اصلاح:

- `CommandSet = Scud_B_CommandSet` (مثل Fateh313؛ `Command_FireMainWeapon` = FIRE_WEAPON PRIMARY بدون ساینس). CommandSet مشترک ویرایش نشد.
- سلاح یکتای جدید `Weapon_Iran_Shahed136Launcher` در `Weapon_ZZZZ_IranShahed136Launcher.ini` (last-win نام جدید؛ `Weapon.ini` دست نخورده)
- همان `Shahed136_AI_Object`، همان آسیب ۱۸۰۰، `AntiGround = Yes`، `AcceptableAimDelta = 360`
- `DeployStyleAIUpdate` با `Turret` از قبل بود

### برد (واحد نقشه SAGE)

| | قبل | بعد |
| --- | ---: | ---: |
| سلاح `AttackRange` | ۱۵۰۰ (`5x_Shahed136DroneSwarm`) | ۳۰۰۰ (`Weapon_Iran_Shahed136Launcher`) |
| `MinimumAttackRange` | ۱۰۰۰ | ۲۰۰ |
| `VisionRange` لانچر | ۶۰۰ | ۳۰۰۰ |

۳۰۰۰ بین Hoveyzeh/Fateh (۱۲۰۰) و `Weapon_Iran_Khorram` (۴۰۵۹) است. `SpecterRadar_ShahedLauncher` همچنان ۱۵۰۰.

ظاهر `Irn_ShhdLnchr*`، هزینه ۱۵۰۰، زمان ۱۵ث عوض نشد.

## اعتبارسنجی ایستا

- مسیر کارخانه → دکمه → Object زنده برای هر سه واحد درست است
- سلاح‌ها، پرتابه، CommandSet، Fire button موجودند
- در برابر factory-complete فقط ۴ مسیر عوض شد (۳ جایگزین + ۱ سلاح جدید)
- ART نیست؛ last-win عراق/Supply/DataLink/RS-24 مانده
- تست بازی: **اجرا نشد**

## BIG

| فایل | حجم | SHA-256 | ورودی |
| --- | ---: | --- | ---: |
| `_SPEC_DATA_ONE.big` | 374 008 764 | `592b49746f14425213309be1cabc5343a1b98aefe9dd977cb27f3cb8e82a1eb4` | 3573 |

## نصب

فقط این `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید. SHA باید `592b4974…` شود. ART را عوض نکنید.

جایگزین کنید (هم‌زمان نگه ندارید): `rs24-df41-factory-complete`، `rs24-df41-firstwin`، `rs24-df41-loco-crash`، `rs24-df41-spawn-crash`، `rs24-df41-wf-crash`.

ترتیب: `0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
