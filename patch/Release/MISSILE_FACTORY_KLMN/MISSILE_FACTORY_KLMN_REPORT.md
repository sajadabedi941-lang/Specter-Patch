# Missile factory slots K / L / M / N

**Zero Hour اجرا نشد.** تست ایستا ≠ تست داخل بازی. تا شلیک واقعی در ZH، تولید و یک‌بارمصرف بودن رفع‌شده اعلام نمی‌شود.

منبع DATA: `_SPEC_DATA_ONE.big` از PR #711 / `iran-shahed-khormshar-fire` (SHA `1cf73a20…`). `CommandSet.ini` این BIG با PR #710 بایت‌به‌بایت یکسان بود؛ نسخهٔ جدید همان فایل است به‌اضافهٔ اسلات‌های کارخانه (چهار CommandSet آتش ایران حفظ شد).

## علت / نگاشت زنده

ControlBar فقط `Data\INI\CommandSet.ini` و `CommandButton.ini` را می‌خواند. فایل‌های extra مثل `CommandSet_RussiaMissiles.ini` جدول نوار فرمان نیستند.

حرف اسلات = شمارهٔ ControlBar: A=1 … J=10، **K=11، L=12، M=13، N=14**.

| اسلات | خواسته | Object زنده | قیمت | وضعیت |
| --- | --- | --- | ---: | --- |
| K | موشک K عراق | `Iraq_Alhussaien` (دکمهٔ زنده `CB_MISSILE_K`) | **20000** (`BuildCost` همان Object) | وصل شد |
| L | خرمشهر ایران | کپی یکتا `Factory_KhormsharOnce` از `IranVehicleKhormshar` (#711) | **20000** | وصل شد؛ یک‌کلیپ |
| M | 13 Varuaktori روسیه | **پیدا نشد** | 27000 | **پر نشد — حدس زده نشد** |
| N | DF-41 چین | کپی یکتا `Factory_DF41Once` از `ChinaVehicleDF41` | **30000** | وصل شد؛ یک‌کلیپ |

### ۱۳ Varuaktori — پیدا نشد

جستجو در BIG زنده (#711)، CSF (`generals.csf`)، تمام Object/DisplayName/CommandButton، و درخت ریپو:

- هیچ رشتهٔ `Varuaktori` / `Varuaktor` / `13 Varu` نیست.
- کارخانهٔ روسیه A–J زنده: Kalibr, Iskander, Oniks, Tochka, Zircon, Kinzhal, Yars (`Russia_Yars`), Bulava, Topol, Voevoda.
- RS-24 (`RussiaVehicleRS24`) و RS-28 سیلو جدا هستند؛ نام‌شان Varuaktori نیست.

طبق دستور، Object حدس زده نشد. اسلات ۱۳ همان Rally (کشورها) / `CB_MISSILE_M` = `Iraq_BM-21` (عراق) ماند.

کشور بدون کارخانهٔ موشکی در DATA: مصر و Arabic Alliance فقط War Factory دارند.

## یک‌بارمصرف بودن (ایستا)

L و N سلاح یکتای `Weapon_Factory_*Once` دارند: `ClipSize = 1` و **`AutoReloadsClip = No`**. پس از یک شلیک موفق کلیپ خالی می‌ماند و موتور دوباره پر نمی‌کند. `FireOCL = OCL_HussienMissileDisarm` (RIDER1 بدون سلاح) همان سازوکار خرمشهر زنده است. `DelayBetweenShots` به‌عنوان راه‌حل زیاد نشد. سلاح‌های اصلی `Khormshar1_ICBM` / `ICBM_DF41_1x_300kt_Warhead` دست‌نخورده ماندند تا واحدهای موجود ایران/چین عوض نشوند.

خرید دوباره = ساخت Object جدید با همان قیمت ۲۰۰۰۰ / ۳۰۰۰۰.

K = `Iraq_Alhussaien` دست‌نخورده (قیمت عراق، `AutoReloadsClip Yes`، ClipReload ۳۰۰ث). کاربر یک‌بارمصرف بودن را فقط برای L/M/N خواست.

## عراق

A–J عراق همان `CB_MISSILE_A`…`J` ماند. فهرست A–M و CommandSet کارخانهٔ عراق به کشور دیگر کپی نشد. کشورهای دیگر فقط `CB_FACTORY_SLOT_K/L/N` گرفتند (K همان Object عراق است، نه دکمه‌های A–J عراق).

اسلات ۱۴ عراق قبلاً `Command_Sell` بود و طبق نگاشت N با DF-41 جایگزین شد. اسلات ۱۳ کشورهای دیگر Rally ماند (چون M پیدا نشد).

## گزارش کشور به کشور (ایستا)

هر ۲۵ CommandSet کارخانهٔ تولید در `CommandSet.ini`؛ هر دکمه در `CommandButton.ini` است.

| کشور | کارخانه | K (۱۱) | L (۱۲) | M (۱۳) | N (۱۴) |
| --- | --- | --- | --- | --- | --- |
| America | `America_MissileFactory` | Iraq_Alhussaien 20000 | Factory_KhormsharOnce 20000 | Rally (Varuaktori نیست) | Factory_DF41Once 30000 |
| Britain | `Britain_MissileFactory` | همان | همان | Rally | همان |
| China | `China_MissileFactory` | همان | همان | Rally | همان |
| France | `France_MissileFactory` | همان | همان | Rally | همان |
| Germany | `Germany_MissileFactory` | همان | همان | Rally | همان |
| India | `India_MissileFactory` | همان | همان | Rally | همان |
| Iran | `Iran_MissileFactory` | همان | همان | Rally | همان |
| Iraq | `Iraq_AlFahdMissileFactory` | `CB_MISSILE_K` → Iraq_Alhussaien 20000 | Factory_KhormsharOnce 20000 | `CB_MISSILE_M` Iraq_BM-21 (بدون حدس) | Factory_DF41Once 30000 |
| Israel | `Israel_MissileFactory` | همان | همان | Rally | همان |
| Italy | `Italy_MissileFactory` | همان | همان | Rally | همان |
| Japan | `Japan_MissileFactory` | همان | همان | Rally | همان |
| Libya | `Libya_MissileFactory` | همان | همان | Rally | همان |
| North Korea | `NorthKorea_MissileFactory` | همان | همان | Rally | همان |
| Pakistan | `Pakistan_MissileFactory` | همان | همان | Rally | همان |
| Russia | `Russia_MissileFactory` | همان | همان | Rally | همان |
| Saudi Arabia | `SaudiArabia_MissileFactory` | همان | همان | Rally | همان |
| South Africa | `SouthAfrica_MissileFactory` | همان | همان | Rally | همان |
| South Korea | `SouthKorea_MissileFactory` | همان | همان | Rally | همان |
| Spain | `Spain_MissileFactory` | همان | همان | Rally | همان |
| Sweden | `Sweden_MissileFactory` | همان | همان | Rally | همان |
| Syria | `Syria_MissileFactory` | همان | همان | Rally | همان |
| Turkey | `Turkey_MissileFactory` | همان | همان | Rally | همان |
| UAE | `UAE_MissileFactory` | همان | همان | Rally | همان |
| Ukraine | `Ukraine_MissileFactory` | همان | همان | Rally | همان |
| Vietnam | `Vietnam_MissileFactory` | همان | همان | Rally | همان |

A–J هر کشور با نسخهٔ #711 یکسان است. `Iraq_AlFahdMissileFactoryBuilding` فقط Sell است (نوار تولید نیست).

زنجیرهٔ ایستا L: `CB_FACTORY_SLOT_L` → `Factory_KhormsharOnce` → `IranKhorramshahrFireCommandSet` / `Command_FireMainWeapon` → `Weapon_Factory_KhormsharOnce` → `Khormshar1_Object`.

زنجیرهٔ ایستا N: `CB_FACTORY_SLOT_N` → `Factory_DF41Once` → `FactoryOnceFireCommandSet` / `Command_FireMainWeapon` → `Weapon_Factory_DF41Once` → `DF41_ICBM_Sgl_Object`. Prerequisite `ChinaWarFactory` روی کپی برداشته شد. `MISSILE01` روی کپی Show است (W3D `CHI_DF41` در ART ONE این استخوان را دارد). ART عوض نشد.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374058417 | `ad4ded5faf0a83a4886f4cc55f42b63a7b53bdd26cf2bea31e005fdbba852e16` |
| `CommandSet.ini` | 454291 | `56bd87eb6f10e5a4e2142cb020789e8302679c387993d65b13c5313d7139ea74` |

ورودی BIG: ۳۵۷۸ (دو Object یکتا اضافه شد). ART دست‌نخورده.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` جایگزین کنید.
2. `CommandSet.ini` همین Release را در `Data\INI\CommandSet.ini` بگذارید (جایگزین #710). چهار Fire ایران داخل همین فایل است؛ نسخهٔ قدیمی‌تر #710 اسلات‌های کارخانه را ندارد.
3. ART را عوض نکنید.
