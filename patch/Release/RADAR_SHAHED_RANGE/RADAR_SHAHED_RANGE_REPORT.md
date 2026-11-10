# برد Shahed-136 قابل‌خرید از رادار: بازگردانی ۳۰۰۰

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## تاریخچه (عدد حدس زده نشد)

| منبع | آنچه ثبت شده |
| --- | --- |
| PR #666 / commit `201d0f92` | کپی مشترک `SpecterRadar_ShahedLauncher` از `IranVehicleShahedLauncher`؛ اسلات ۱۲؛ قیمت ۸۰۰۰؛ PRIMARY = `5x_Shahed136DroneSwarm` (همان سلاح منبع آن زمان) |
| PR #667 | فقط `ButtonImage = specbtn_shahedlnchr`؛ گیم‌پلی #666 بدون تغییر |
| PR #706 / #707 / #708 | سلاح یکتای ایران `Weapon_Iran_Shahed136Launcher` با **`AttackRange = 3000`**. صریحاً `5x_Shahed136DroneSwarm` last-win نشد چون همان نام را لانچر رادار دارد. گزارش: «`SpecterRadar_ShahedLauncher` همچنان ۱۵۰۰» |
| PR #711 | همان ۳۰۰۰ داخل `Weapon.ini` برای ایران؛ `VisionRange = 3000` روی `IranVehicleShahedLauncher`. برد ۳۰۰۰ حفظ شد |

عدد تأییدشدهٔ برد: **۳۰۰۰**.

## DATA زنده قبل از این PR (ریلیز `ad-max-three` / #716)

| Object | سلاح زنده | AttackRange | VisionRange | قیمت |
| --- | --- | ---: | ---: | ---: |
| `IranVehicleShahedLauncher` | `Weapon_Iran_Shahed136Launcher` در `Data\INI\Weapon.ini` | 3000 | 3000 | 1500 |
| `SpecterRadar_ShahedLauncher` | `5x_Shahed136DroneSwarm` در `Data\INI\Weapon.ini` | **1500** (قدیمی) | 600 | 8000 |

نسخهٔ قدیمی ۱۵۰۰ دوباره روی کپی راداری مانده بود؛ ادغام‌های #712–#716 آن را عوض نکردند چون #706–#711 عمداً سلاح مشترک را لمس نکردند.

تنها مصرف‌کنندهٔ زندهٔ `5x_Shahed136DroneSwarm` در این BIG همان `SpecterRadar_ShahedLauncher` است.

## اصلاح (فقط همین)

- `Data\INI\Weapon.ini` → بلوک `Weapon 5x_Shahed136DroneSwarm`: `AttackRange` از ۱۵۰۰ به **۳۰۰۰**. `MinimumAttackRange` ۱۰۰۰، پرتابه `Shahed136_AI_Object`، آسیب و کلیپ دست‌نخورده.
- `Data\INI\Object\Specter\SpecterRadarUavs.ini` → فقط `Object SpecterRadar_ShahedLauncher`: `VisionRange` از ۶۰۰ به **۳۰۰۰** تا برد ۳۰۰۰ قابل‌استفاده باشد (همان مقدار #711 روی لانچر ایران).

دست‌نخورده: `IranVehicleShahedLauncher`، `Weapon_Iran_Shahed136Launcher`، پهپادهای راداری Heron/MQ-4/Orlan-10، `CommandSet.ini` / `CommandButton.ini` (#714)، کارخانهٔ K/L/M/N (#712–#715)، سقف پدافند #716.

دکمهٔ زنده: `Command_ConstructSpecterRadarShahedLauncher` → `Object = SpecterRadar_ShahedLauncher` / `ButtonImage = specbtn_shahedlnchr` / اسلات ۱۲ / ۸۰۰۰.

## ۱۸ کشور (اسلات ۱۲)

Sweden, Ukraine, Turkey, Italy, Britain, Germany, France, Iraq, India, Pakistan, Syria, Saudi Arabia, UAE, Libya, South Africa, South Korea, Japan, Vietnam.

همه در `CommandSet.ini` زنده هنوز `12 = Command_ConstructSpecterRadarShahedLauncher` دارند.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374080210 | `e2b326824c774609f5e16d9c8a2b17f26f8f0edef5feb351a97ada5e1de4bdbf` |
| `CommandSet.ini` | 454198 | `405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

ART عوض نشد.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید.
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید.
4. ART را عوض نکنید.

یا `Install_RadarShahedRange.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

لانچر Shahed خریداری‌شده از رادار آن ۱۸ کشور تا ۳۰۰۰ شلیک کند. لانچر ایران همان ۳۰۰۰ قبلی بماند. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
