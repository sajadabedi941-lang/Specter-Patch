# Missile factory slot M = live RS24Yars

**Zero Hour اجرا نشد.** تست ایستا ≠ تست داخل بازی. تا شلیک واقعی در ZH، تولید و یک‌بارمصرف بودن رفع‌شده اعلام نمی‌شود.

منبع DATA: `_SPEC_DATA_ONE.big` از PR #712 / `missile-factory-klmn` (SHA `ad4ded5faf0a83a4886f4cc55f42b63a7b53bdd26cf2bea31e005fdbba852e16`). `CommandSet.ini` همین Release جایگزین overlayهای #710/#712 است و چهار Fire ایران را نگه می‌دارد.

## هویت زنده «RS_24Yars»

هیچ `Object RS_24Yars` در BIG زنده نیست. زنجیرهٔ واقعی از DATA #712:

| قطعه | مقدار زنده |
| --- | --- |
| Object | `RussiaVehicleRS24` — `Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini` (اولین ثبت ThingFactory) |
| DisplayName | `OBJECT:Yars` |
| دکمه | `Command_ConstructRussiaVehicleRS24` → Object=`RussiaVehicleRS24`، تصویر `rus_rs24` |
| سلاح PRIMARY | `RS24_Yars_ICBM_1x_Warhead` — در Weapon.ini با توضیح `; ----------- Russia RS24Yars --------------` |
| پرتابه | `RS24_Yars_Object` (در `Russia_WeaponObjects.ini`) |
| استخوان شلیک | `ModuleTag_Bones` / `WeaponLaunchBone = PRIMARY WeaponA` |
| قیمت زنده | **3500** |
| Prerequisite زنده | `RussiaWarFactory` |
| CommandSet زنده | `Iraq_AlhussaienArmedCommandSet` |

`Russia_Yars` واحد دیگری است (اسلات G کارخانهٔ روسیه، `Weapon_Russia_Yars`، قیمت ۴۷۰۰). `Russia_RS24_Yars` Object ندارد (دکمهٔ یتیم). `Russia_RS24_Yars_AI` فقط AI است. هیچ‌کدام به‌جای RS24Yars استفاده نشد.

## چرا کپی کارخانه (`Factory_RS24YarsOnce`)

دستور: اگر Object زنده هست همان زنجیره را به کار ببر؛ نسخهٔ مستقل فقط با دلیل مستند.

تغییر خود `RussiaVehicleRS24` یا `RS24_Yars_ICBM_1x_Warhead` این‌ها را last-win می‌کند:

1. قیمت کارخانه باید **27000** باشد؛ TEL کارخانهٔ جنگ روسیه **3500** است.
2. `RussiaWarFactory` ساخت را برای ۲۴ کشور دیگر می‌بندد.
3. CommandSet سوارکار ICBM است، نه `Command_FireMainWeapon`.
4. سلاح زنده `AutoReloadsClip` ندارد (پیش‌فرض Yes) — یک‌بارمصرف نیست.
5. `MISSILE01` جز حالت RIDER2 مخفی است.

کپی روی مسیر یکتای `Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini` ثبت می‌شود. فایل زنده `RS-24_Yars.ini` بایت‌به‌بایت ماند.

زنجیرهٔ ایستا M: `CB_FACTORY_SLOT_M` → `Factory_RS24YarsOnce` (27000) → `FactoryOnceFireCommandSet` / `Command_FireMainWeapon` → `Weapon_Factory_RS24YarsOnce` (`ClipSize=1`, `AutoReloadsClip=No`, `FireOCL=OCL_HussienMissileDisarm`) → `RS24_Yars_Object`. Prerequisite خالی است. `MISSILE01` روی کپی Show است (W3D `RUS_RS24` در ART ONE این استخوان را دارد). ART عوض نشد.

## یک‌بارمصرف بودن (ایستا)

`Weapon_Factory_RS24YarsOnce`: `ClipSize = 1` و **`AutoReloadsClip = No`**. پس از یک شلیک موفق کلیپ خالی می‌ماند و موتور دوباره پر نمی‌کند. `FireOCL = OCL_HussienMissileDisarm` همان سازوکار خرمشهر زنده است (RIDER1 بدون سلاح). `DelayBetweenShots` / tooltip به‌عنوان راه‌حل عوض نشد. سلاح زنده `RS24_Yars_ICBM_1x_Warhead` دست‌نخورده ماند.

خرید دوباره = ساخت Object جدید با قیمت ۲۷۰۰۰.

## K / L / N از #712

| اسلات | Object | قیمت | وضعیت |
| --- | --- | ---: | --- |
| K=۱۱ | `Iraq_Alhussaien` (عراق: `CB_MISSILE_K`) | **20000** | حفظ شد |
| L=۱۲ | `Factory_KhormsharOnce` | **20000** | حفظ شد؛ یک‌کلیپ |
| M=۱۳ | `Factory_RS24YarsOnce` از `RussiaVehicleRS24` | **27000** | **این PR** |
| N=۱۴ | `Factory_DF41Once` | **30000** | حفظ شد؛ یک‌کلیپ |

فقط اسلات ۱۳ عوض شد: Rally کشورها و `CB_MISSILE_M` عراق (`Iraq_BM-21`) → `CB_FACTORY_SLOT_M`. A–J هر کشور دست‌نخورده است.

## عراق

A–J همان `CB_MISSILE_A`…`J`. K همان `CB_MISSILE_K` → `Iraq_Alhussaien` 20000. فهرست A–M و CommandSet کارخانهٔ عراق به کشور دیگر کپی نشد. `Iraq_AlFahdMissileFactoryBuildingCommandSet` فقط Sell ماند.

## مصر / Arabic Alliance

در `CommandSet.ini` و Objectهای زنده هیچ کارخانهٔ موشکی برای مصر یا Arabic Alliance نیست. فقط War Factory دارند. کارخانه‌دار فرض نشدند.

## گزارش کشور به کشور (ایستا)

۲۵ CommandSet تولید در `Data\INI\CommandSet.ini` (مسیر خوانده‌شدهٔ ControlBar). دکمه در `CommandButton.ini`.

| کشور | کارخانه | K (۱۱) | L (۱۲) | M (۱۳) | N (۱۴) |
| --- | --- | --- | --- | --- | --- |
| America | `America_MissileFactory` | Iraq_Alhussaien 20000 | Factory_KhormsharOnce 20000 | **Factory_RS24YarsOnce 27000** | Factory_DF41Once 30000 |
| Britain | `Britain_MissileFactory` | همان | همان | همان | همان |
| China | `China_MissileFactory` | همان | همان | همان | همان |
| France | `France_MissileFactory` | همان | همان | همان | همان |
| Germany | `Germany_MissileFactory` | همان | همان | همان | همان |
| India | `India_MissileFactory` | همان | همان | همان | همان |
| Iran | `Iran_MissileFactory` | همان | همان | همان | همان |
| Iraq | `Iraq_AlFahdMissileFactory` | `CB_MISSILE_K` → Iraq_Alhussaien 20000 | Factory_KhormsharOnce 20000 | **Factory_RS24YarsOnce 27000** | Factory_DF41Once 30000 |
| Israel | `Israel_MissileFactory` | همان | همان | همان | همان |
| Italy | `Italy_MissileFactory` | همان | همان | همان | همان |
| Japan | `Japan_MissileFactory` | همان | همان | همان | همان |
| Libya | `Libya_MissileFactory` | همان | همان | همان | همان |
| North Korea | `NorthKorea_MissileFactory` | همان | همان | همان | همان |
| Pakistan | `Pakistan_MissileFactory` | همان | همان | همان | همان |
| Russia | `Russia_MissileFactory` | همان | همان | همان | همان |
| Saudi Arabia | `SaudiArabia_MissileFactory` | همان | همان | همان | همان |
| South Africa | `SouthAfrica_MissileFactory` | همان | همان | همان | همان |
| South Korea | `SouthKorea_MissileFactory` | همان | همان | همان | همان |
| Spain | `Spain_MissileFactory` | همان | همان | همان | همان |
| Sweden | `Sweden_MissileFactory` | همان | همان | همان | همان |
| Syria | `Syria_MissileFactory` | همان | همان | همان | همان |
| Turkey | `Turkey_MissileFactory` | همان | همان | همان | همان |
| UAE | `UAE_MissileFactory` | همان | همان | همان | همان |
| Ukraine | `Ukraine_MissileFactory` | همان | همان | همان | همان |
| Vietnam | `Vietnam_MissileFactory` | همان | همان | همان | همان |

A–J هر کشور با نسخهٔ #712 یکسان است.

## بارگذاری DATA

ThingFactory `loadDirectory Data\INI\Object` — مسیر یکتای `FactoryKLMN\Factory_RS24YarsOnce.ini` اولین (و تنها) ثبت این Object است. WeaponStore فقط `Data\INI\Weapon.ini` را می‌خواند؛ سلاح جدید به انتهای همان فایل اضافه شد و نام زنده را بازنویسی نمی‌کند. ControlBar فقط `Data\INI\CommandSet.ini` و `CommandButton.ini` را می‌خواند. INIZH روی `CommandSet.ini` first-win است؛ به‌همین خاطر overlay شل همین Release باید کنار BIG نصب شود.

ورودی‌های تغییرکرده نسبت به #712: `CommandSet.ini`, `CommandButton.ini`, `Weapon.ini`، به‌اضافهٔ یک Object جدید. 3578 → 3579.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374080193 | `d5a8ed982e7ff37de1fa9923f1ee96abe16312f481f563891d95e1b4dffb26c8` |
| `CommandSet.ini` | 454198 | `405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858` |

ART دست‌نخورده.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` جایگزین کنید.
2. `CommandSet.ini` همین Release را در `Data\INI\CommandSet.ini` بگذارید (جایگزین #710/#712). چهار Fire ایران و اسلات‌های K/L/N داخل همین فایل است.
3. ART را عوض نکنید.

## آنچه ZH باید جداگانه تأیید کند

- دکمهٔ اسلات M روی هر ۲۵ کارخانه ظاهر می‌شود و واحد را با قیمت ۲۷۰۰۰ می‌سازد.
- پس از یک شلیک موفق، همان واحد دوباره شلیک نمی‌کند.
- ساخت بعدی نیاز به خرید مجدد دارد.
- TEL کارخانهٔ جنگ روسیه (`RussiaVehicleRS24`، ۳۵۰۰) عوض نشده است.
