# Factory DF-41 ballistic launch (slot N)

**Zero Hour اجرا نشد.** تست ایستا ≠ تأیید داخل بازی.

## زنجیرهٔ زنده (کارخانه)

`CB_FACTORY_SLOT_N` → `Factory_DF41Once` (قیمت ۳۰۰۰۰) → `FactoryOnceFireCommandSet` / `Command_FireMainWeapon` → `Weapon_Factory_DF41Once` (`ClipSize=1`, `AutoReloadsClip=No`) → `ProjectileObject = DF41_ICBM_Sgl_Object` → `MissileAIUpdate` + `Locomotor DF41MissileLocomotor` → مرگ با `OCL_DF41_sgl_WareheadsReentry` → `300Kt_DF41WarheadReentryProjectile`.

پرتابه و سلاح نام‌های زندهٔ چین را last-win نمی‌کنند. `Object ChinaVehicleDF41` و `ICBM_DF41_1x_300kt_Warhead` دست‌نخورده ماندند.

## علت حرکت زمینی

مقایسهٔ `Factory_DF41Once` با `ChinaVehicleDF41` (فایل `DF41.ini`):

| | TEL زنده چین | کپی کارخانه (قبل) |
| --- | --- | --- |
| استخوان شلیک PRIMARY | فقط `ModuleTag_Bones` / `WeaponA` روی مدل `DF41_Bones` | همان **به‌علاوهٔ ۱۲** `WeaponLaunchBone = PRIMARY MISSILE01` روی `W3DTruckDraw` |
| پرتابه | `DF41_ICBM_Sgl_Object` | همان |
| KindOf پرتابه | `UNATTACKABLE PROJECTILE BALLISTIC_MISSILE` | همان |
| MissileAIUpdate | `InitialVelocity=130`, `DistanceToTravelBeforeTurning=1750`, `DistanceToTargetBeforeDiving=800` | همان |
| Locomotor | `DF41MissileLocomotor` — `Surfaces=AIR`, `PreferredHeight=1600` | همان |

کمک‌کنندهٔ #712 برای نمایش `MISSILE01` (نوشته‌شده برای خرمشهر) روی DF-41 هم اعمال شد و استخوان شلیک افقی لوله را به‌جای `WeaponA` عمودی ثبت کرد. `MissileAIUpdate` اول ۱۷۵۰ واحد **در راستای استخوان شلیک** می‌رود؛ از `MISSILE01` این راستا زمین است.

`AntiGround=Yes` روی سلاح کارخانه فقط هدف‌گیری زمینی است، نه مسیر پرواز. سلاح زنده همان پرتابه را بدون آن دارد و مسیر را عوض نمی‌کند.

RS-24 کارخانه `MISSILE01` شلیک ندارد (فقط `WeaponA`). خرمشهر از روی `MISSILE01` شلیک می‌کند چون TEL زنده‌اش همان است. هیچ‌کدام در این PR عوض نشدند.

## اصلاح

از `Factory_DF41Once.ini` فقط ۱۲ خط `WeaponLaunchBone = PRIMARY MISSILE01` و ۱۲ خط همراه `WeaponFireFXBone = PRIMARY WEAPONFX` حذف شد. `ShowSubObject MISSILE01`، `ModuleTag_Bones` / `WeaponA`، قیمت ۳۰۰۰۰، سلاح یک‌کلیپ، اسلات N، و A–M ماندند.

تنها فایل تغییرکرده در BIG همان Object یکتای کارخانه است.

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374079077 | `5b7ee5c6b8a57506c9cc82083e8366bfcdb50f1c585fba2d842504bfaa2d2312` |
| `CommandSet.ini` | 454198 | `405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858` |
| `CommandButton.ini` | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

CommandSet / CommandButton با Release `iraq-factory-cs-crash` (#714) یکسان‌اند تا overlay شل از بین نرود. ART عوض نشد.

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید.
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید (لازم برای #714).
4. ART را عوض نکنید.

یا `Install_DF41FactoryBallistic.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

پس از شلیک اسلات N، پرتابه از TEL اوج بگیرد، با `PreferredHeight` مسیر هوایی برود، و در پایان به هدف برخورد کند. بدون اجرای بازی ادعای تأیید داخل بازی نمی‌شود.
