# Fire برای Shahed_136 Mobile Launcher رادار کشورهای دیگر

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## مرجع ایران (کار می‌کند)

`IranVehicleShahedLauncher` در `Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini`

| فیلد | مقدار زنده |
| --- | --- |
| خرید | `IranWarfactoryCommandSet` اسلات ۱۱ — **نه** رادار ایران |
| `CommandSet` | `IranShahed136FireCommandSet` → `1 = Command_FireMainWeapon` |
| `Command_FireMainWeapon` | `FIRE_WEAPON` / `WeaponSlot = PRIMARY` / `NEED_TARGET_POS` |
| PRIMARY | `Weapon_Iran_Shahed136Launcher` داخل `Data\INI\Weapon.ini` |
| پرتابه | `Iran_Shahed136_FireProjectile` (`PROJECTILE BALLISTIC_MISSILE` + `DumbProjectileBehavior`) |
| `AutoAcquireEnemiesWhenIdle` | `No` (بدون دکمهٔ Fire شلیک نمی‌کند) |
| قیمت | **۱۵۰۰ — تغییر نکرد** |

رادار ایران (`IranRadarStationCommandSet`) پهپاد `IranDroneShahed136` دارد، نه این لانچر. نام نمایشی لانچر `OBJECT:ShahedLauncher` است.

## نسخه‌های رادار کشورهای دیگر

یک Object مشترک: `SpecterRadar_ShahedLauncher` در `Data\INI\Object\Specter\SpecterRadarUavs.ini`. تعریف تکراری در DATA نیست.

قبل از اصلاح با ایران یکی بود جز:

| فیلد | ایران | کپی رادار (قبل) |
| --- | --- | --- |
| PRIMARY | `Weapon_Iran_Shahed136Launcher` | `5x_Shahed136DroneSwarm` → پرتابه `Shahed136_AI_Object` (پهپاد قابل‌انتخاب، شلیک سلاح نیست) |
| CommandSet | `IranShahed136FireCommandSet` | `AmericaTankCrusaderCommandSet` (فقط AttackMove/Guard/Stop؛ **بدون Fire**) |
| قیمت | 1500 | 8000 |

تنها مصرف‌کنندهٔ زندهٔ `5x_Shahed136DroneSwarm` همین Object رادار بود.

## اصلاح (فقط همین)

روی `SpecterRadar_ShahedLauncher`:

- `CommandSet` → `IranShahed136FireCommandSet` (همان مجموعهٔ موجود؛ CommandSet جدید ساخته نشد)
- PRIMARY → `Weapon_Iran_Shahed136Launcher` (همان سلاح و پرتابهٔ ایران در `Weapon.ini`)
- `BuildCost = 8000` باقی ماند

دست‌نخورده: Object ایران، قیمت ایران، `Weapon.ini`، منوی رادار/اسلات ۱۲، `CommandButton` ساخت، Heron/MQ-4/Orlan-10، کارخانه، پدافند.

## مسیر Fire (ایستا)

ساخت → `Command_ConstructSpecterRadarShahedLauncher` → Object `SpecterRadar_ShahedLauncher` → `IranShahed136FireCommandSet` → `Command_FireMainWeapon` (`FIRE_WEAPON` PRIMARY) → `Weapon_Iran_Shahed136Launcher` (`AntiGround=Yes`) → `Iran_Shahed136_FireProjectile`.

`AmericaTankCrusaderCommandSet` برای تانک‌ها عوض نشد.

## کشورها و قیمت

همه از همان Object مشترک می‌خرند؛ قیمت هر نسخهٔ غیر ایران **۸۰۰۰** است.

| کشور | CommandSet رادار | اسلات | Object | قیمت |
| --- | --- | ---: | --- | ---: |
| Sweden | `SwedenGM406CommandSet` | 12 | `SpecterRadar_ShahedLauncher` | 8000 |
| Ukraine | `UkraineGM406CommandSet` | 12 | همان | 8000 |
| Turkey | `TurkeyGM406CommandSet` | 12 | همان | 8000 |
| Italy | `ItalyGM406CommandSet` | 12 | همان | 8000 |
| Britain | `BritainGM406CommandSet` | 12 | همان | 8000 |
| Germany | `GermanyGM406CommandSet` | 12 | همان | 8000 |
| France | `FranceGM406CommandSet` | 12 | همان | 8000 |
| Iraq | `Iraq_RadarStationCommandSet` | 12 | همان | 8000 |
| India | `India_RadarCommandSet` | 12 | همان | 8000 |
| Pakistan | `Pakistan_RadarCommandSet` | 12 | همان | 8000 |
| Syria | `Syria_RadarCommandSet` | 12 | همان | 8000 |
| Saudi Arabia | `SaudiArabia_RadarCommandSet` | 12 | همان | 8000 |
| UAE | `UAE_RadarCommandSet` | 12 | همان | 8000 |
| Libya | `Libya_RadarCommandSet` | 12 | همان | 8000 |
| South Africa | `SouthAfrica_RadarCommandSet` | 12 | همان | 8000 |
| South Korea | `SouthKorea_RadarStationCommandSet` | 12 | همان | 8000 |
| Japan | `Japan_RadarStationCommandSet` | 12 | همان | 8000 |
| Vietnam | `Vietnam_RadarStationCommandSet` | 12 | همان | 8000 |
| Iran (مرجع، کارخانه) | `IranWarfactoryCommandSet` اسلات ۱۱ | — | `IranVehicleShahedLauncher` | **1500** |

## فایل‌های اصلاح‌شده داخل DATA

| مسیر داخل BIG | تغییر |
| --- | --- |
| `Data\INI\Object\Specter\SpecterRadarUavs.ini` | فقط Object `SpecterRadar_ShahedLauncher` (سلاح + CommandSet) |

`CommandSet.ini` / `CommandButton.ini` بایت‌به‌بایت همان #722 هستند (برای ControlBar شل نصب می‌شوند).

## SHA-256

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075487 | `71559b012715a8336cb8b79cefef29cf4e00465825969b500184d95401cc7346` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |

این DATA جایگزین `_SPEC_DATA_ONE.big` بستهٔ `specter-unified` / #722 است و تغییرات DATA آن‌ها را دارد. Overlayهای `0_` و ART اصلی را نگه دارید. دارایی‌های ریلیزهای قبلی حذف نشدند.
