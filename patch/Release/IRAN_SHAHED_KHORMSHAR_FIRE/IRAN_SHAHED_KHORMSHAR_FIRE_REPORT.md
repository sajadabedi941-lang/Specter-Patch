# Shahed-136 Fire + Khormshar launcher / impact FX

**Zero Hour اجرا نشد.** `generals.exe` و `INIZH.big` در این محیط نیستند. تست داخل بازی انجام نشده است. تا پیش از تست واقعی، هیچ‌کدام رفع‌شده اعلام نمی‌شود.

`CommandSet.ini` نسخهٔ PR #710 / Release `iran-commandset-live-path` حفظ شده است. این انتشار آن فایل را حذف یا با نسخهٔ قدیمی جایگزین نمی‌کند.

## علت‌ها (قبل از هر اصلاح)

منبع DATA زنده: `_SPEC_DATA_ONE.big` از Release `iran-commandset-ini-fire` / PR #709، SHA-256 `46aab7d5c9433471a545935e2f922949d85130de287e44da3d13772a18c604cc`، ۳۵۷۶ ورودی.

### ۱. Shahed-136 — دکمهٔ Fire دیده می‌شود ولی فعال نیست

زنجیرهٔ زنده:

| حلقه | مسیر مؤثر | نتیجه |
| --- | --- | --- |
| Object `IranVehicleShahedLauncher` | `Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini` (first-win یکتا) | `CommandSet = IranShahed136FireCommandSet`، `PRIMARY = Weapon_Iran_Shahed136Launcher`، `VisionRange = 3000` |
| CommandSet / دکمه | PR #710 `Data\INI\CommandSet.ini` (loose، LocalFileSystem قبل از هر BIG) + `Command_FireMainWeapon` | پنل باز است (تأیید کاربر) |
| Weapon `Weapon_Iran_Shahed136Launcher` | **فقط** `Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini` | WeaponStore این مسیر را نمی‌خواند |
| WeaponStore | `GameEngine` → `initSubsystem(TheWeaponStore, …, "Data\\INI\\Weapon.ini")` | `2x_SRBM_Fateh313_HE` و `Khormshar1_ICBM` داخل `Weapon.ini` هستند؛ نام Shahed نیست |
| Projectile `Iran_Shahed136_FireProjectile` | مسیر Object یکتا | `DumbProjectileBehavior`؛ `ParticleSysBone = ENGINE01` در حالی که W3D `Irn_Shahed136` استخوان `ENGINE` دارد |

`5x_Shahed136DroneSwarm` داخل `Weapon.ini` است ولی PRIMARY پرتابگر موبایل به آن اشاره نمی‌کند (و برد آن ۱۵۰۰ است، `AntiGround` ندارد).

نتیجه: ControlBar دکمه را از CommandSet می‌سازد، ولی PRIMARY به قالبی اشاره می‌کند که WeaponStore هرگز ثبت نکرده است. دکمه غیرفعال می‌ماند / شلیک رخ نمی‌دهد. اصلاح CommandSet یا دکمه این حلقه را درست نمی‌کند.

محدودیت‌های سلاح پس از ثبت در `Weapon.ini`: `AttackRange 3000`، `MinimumAttackRange 200`، `AntiGround Yes`، `ClipSize 5`. همان DeployStyle Fateh (`TurretsFunctionOnlyWhenDeployed`، Unpack ۴۹۵۰ms). برد ۳۰۰۰ حفظ شد.

### ۲. خرمشهر — موشک روی پرتابگر نیست؛ انفجار/تخریب ناقص است

Object زنده `IranVehicleKhormshar`: first-win `…\Wheeled\Khormshar.ini` و همان Hide در overlay `Object_ZZZZ_ZzGlobalStoreFivePrereq.ini`.

W3D زنده (ART ONE که `Launch_Specter.bat` کپی می‌کند، و ART TWO با SHA یکسان):

| مدل | MISSILE01 | نکته |
| --- | --- | --- |
| `Art\W3D\Irn_Khormsh.W3D` | mesh + bone + HLOD | حامل packed |
| `Art\W3D\Irn_Khormsh_A.W3D` | mesh + bone + HLOD | حامل deployed |
| `Art\W3D\Irn_Khormsh_M.W3D` | missile-only؛ استخوان `ENGINE01` | پرتابه |
| `Art\W3D\Khormshar_Bones.W3D` | ندارد؛ فقط `WEAPONFX` / `WEAPONA01` | helper |

مدل پرتابگر **موشک قابل‌نمایش دارد.** INI روی Default / MOVING / UNPACKING / PACKING / DEPLOYED مقدار `HideSubObject = MISSILE01` می‌گذارد. فقط RIDER2 نمایش می‌دهد. `FireOCL = OCL_HussienMissileDisarm` بعد از شلیک RIDER1 تزریق می‌کند (لولهٔ خالی). واحد از ابتدا RIDER2 نیست؛ بنابراین موشک روی حامل دیده نمی‌شود و هنگام شلیک پرتابه ناگهان ظاهر می‌شود.

`Command_FireMainWeapon` اسلات PRIMARY را شلیک می‌کند. `WeaponLaunchBone` فقط روی SECONDARY و فقط در RIDER1/RIDER2 DEPLOYED بود. الگوی Fateh: `WeaponLaunchBone = PRIMARY MISSILE` + `ProjectileBoneFeedbackEnabledSlots` بدون Hide.

زنجیرهٔ برخورد:

- `Khormshar1_ICBM` در `Weapon.ini`: `PrimaryDamage = 1`، شعاع ۰، **بدون** `ProjectileDetonationFX`
- پرتابه `Khormshar1_Object`: `InstantDeath DeathTypes = ALL` بدون FX
- `CreateObjectDie OCL_Khormshar1WareheadsReentry` → `Khormshar1WarheadReentryObject` با تأخیر ۶۵۰۰ms و `Attack` اسلات SECONDARY، ۲۰ شلیک، در حالی که `Khormshar1WarheadReentryWeapon` مقدار `ClipSize = 1` دارد
- `Khormshar1HighExplosiveExplosion` فقط `FireFX` + `OCL_PoisonFieldLarge` است؛ **PrimaryDamage ندارد**

آمار ICBM عوض نشد. افکت برخورد از `FX_HeavyWarheadCruiseMissileExplosion` و تخریب از سلاح موجود خانواده (`Khormshar1WarheadReentryGlideVehicleDamage`) به مرگ پرتابه وصل شد.

ART بسته‌بندی نشد: W3D خرمشهر در ART ONE با ART TWO بایت‌به‌بایت یکسان است و `MISSILE01` دارد.

## اصلاح (فقط DATA زنده)

شش مسیر داخل همان BIG؛ `CommandSet.ini` بایت‌به‌بایت بدون تغییر.

1. `Data\INI\Weapon.ini` — تعریف `Weapon_Iran_Shahed136Launcher` (برد ۳۰۰۰، `AntiGround Yes`) اضافه شد. روی `Khormshar1_ICBM` فقط `ProjectileDetonationFX` و `AntiGround Yes` اضافه شد؛ Damage همچنان ۱.
2. `Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini` — همان تعریف همگام شد (اگر exe پچ‌شده extra را بخواند last-win متفاوت نشود).
3. `Iran_Shahed136_FireProjectile.ini` — `ParticleSysBone` از `ENGINE01` به استخوان واقعی `ENGINE`.
4. `Khormshar.ini` و overlay همان Object — `ShowSubObject = MISSILE01` روی حالت‌های مسلح؛ RIDER1 همچنان Hide؛ `WeaponLaunchBone PRIMARY MISSILE01`؛ `ProjectileBoneFeedbackEnabledSlots`.
5. `Iran_WeaponObjects.ini` / `Khormshar1_Object` — InstantDeath به سبک Fateh + `FireWeaponWhenDead` با `Khormshar1WarheadReentryGlideVehicleDamage`. زنجیرهٔ MIRV `CreateObjectDie` باقی است. Object هوش مصنوعی دست نخورده.

حفظ‌شده: BuildTime خرمشهر ۱۰ث، Prerequisites خالی، قیمت ۲۵۰۰، CommandSetها، برد Shahed ۳۰۰۰، هزینه ۱۵۰۰، `Command_FireMainWeapon`.

سلاح‌های سایر کشورها در `Weapon.ini` تغییر نکردند. تنها نام افزوده‌شده: `Weapon_Iran_Shahed136Launcher`.

## اعتبارسنجی ایستا

- ۳۵۷۶ ورودی؛ فقط ۶ مسیر تغییر کرد
- `CommandSet.ini` و Object پرتابگر Shahed با #709 یکسان‌اند
- Shahed weapon در `Weapon.ini`: AttackRange ۳۰۰۰، Min ۲۰۰، AntiGround Yes، ClipSize ۵
- خرمشهر Default: Show MISSILE01 + PRIMARY MISSILE01؛ RIDER1 همچنان Hide؛ BuildTime ۱۰.۰؛ BuildCost ۲۵۰۰
- ICBM PrimaryDamage همچنان ۱
- `Khormshar1_ICBM_AI`، Fateh، swarm Shahed بدون تغییر

داخل ZH: **اجرا نشد.**

## BIG

| فایل | حجم (بایت) | SHA-256 | ورودی |
| --- | ---: | --- | ---: |
| `_SPEC_DATA_ONE.big` | 374016390 | `1cf73a202d68a9008dfc6bc2925d26b31da53f622ad5881e400f5ce74c3c7937` | 3576 |

## نصب (سازگار با PR #710)

ترتیب:

1. **نگه دارید** `Data\INI\CommandSet.ini` از Release `iran-commandset-live-path` / PR #710. SHA-256 باید `5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac` باشد. این فایل را حذف نکنید و با نسخهٔ قدیمی عوض نکنید. اختیاری: `0_SPECTER_IranCommandSet.big` با SHA `274c4a52c1e79d440914f709d98639fc017b29d81f96e7e9d20a620b53466ed4`.
2. همین `_SPEC_DATA_ONE.big` را کنار `generals.exe` جایگزین کنید. SHA باید `1cf73a20…` شود.
3. ART را عوض نکنید (`_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big`).

هم‌زمان نگذارید: DATAهای `iran-commandset-ini-fire`، `iran-missile-fire-buttons`، `iran-missiles-unlock-shahed-fire`، `iran-khorramshahr-shahed136`.
