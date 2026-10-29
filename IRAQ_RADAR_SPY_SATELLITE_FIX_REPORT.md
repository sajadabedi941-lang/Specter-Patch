# Iraq radar Phase 1: Radar/Minimap grant + Spy Satellite detach

مخزن: sajadabedi941-lang/Specter-Patch  
مرجع SPE: commit `aac7ffc1`  
منبع DATA: Full Release / Supply Centre `_SPEC_DATA_ONE.big` (`be2f27b7…`, 373 955 679 بایت)  
فقط `_SPEC_DATA_ONE.big` بازسازی شد. ART ONE / ART TWO دست نخورده‌اند.

**تست داخل بازی انجام نشده است.** Generals Zero Hour در این محیط اجرا نمی‌شود. نتایج زیر فقط اعتبارسنجی ایستای BIG/INI و ترتیب Last-Win است. Release برای تست کاربر آماده است.

## چرا اصلاح قبلی (PR #692 / Release `iraq-radar-spy-map-2c93`) کافی نبود

PR #692 هنوز به `main` ادغام نشده، ولی Last-Winهای آن داخل DATA فعلی Full Release حضور دارند. آن اصلاح دو چیز را جا انداخت:

1. **Radar/Minimap:** `RadarUpgrade` فقط `DisableProof = No` داشت و `TriggeredBy = Upgrade_AmericaRadar` نداشت. موتور ZH ماژول ارتقا را بدون Trigger اجرا نمی‌کند، بنابراین `GrantUpgradeCreate Upgrade_AmericaRadar` به‌تنهایی رادار بازیکن را روشن نمی‌کند. رادارهای سالم همین BIG (مصر، هند، …) همین جفت را دارند. #692 فقط اسپان P30 و ماژول SSC را برداشت و Shroud را دست نزد — علت فعال‌نشدن رادار همان Trigger گم‌شده بود.
2. **Spy Satellite:** دکمه `Command_SpySatelliteScan` برداشته شد ولی جایش `Command_IraqiRadarSearch` نشست. آن دکمه همان Spy Satellite است (`CONTROLBAR:SpySatellite`, `SSSpySat`, `Enum = SPECIAL_SPY_SATELLITE`). روی Object هم `OCLSpecialPower SpecialPowerIraqiRadarSearch` ماند.

## ترتیب Last-Win مؤثر (قبل از این اصلاح)

`Iraq_RadarStationCommandSet` (۳ نسخه، آخر برنده):

1. `Data\INI\CommandSet.ini` — بدون Spy Sat
2. `Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini` — `Command_SpySatelliteScan` + `Command_SpecterSpySatelliteFee`
3. `Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini` — `Command_IraqiRadarSearch` (Spy Sat با نام دیگر)

`Object Iraq_RadarStation` (۲ نسخه، آخر برنده):

1. `Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_RadarStation.ini` — SSC + IraqiRadarSearch + P30 + RadarUpgrade بدون TriggeredBy
2. `Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini` — بدون SSC/P30، هنوز IraqiRadarSearch، هنوز RadarUpgrade بدون TriggeredBy

`CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini` و objectهای Supply Centre بعد از این مسیرها می‌آیند ولی `Iraq_RadarStation` را دوباره تعریف نمی‌کنند. overlayهای `0_SPECTER_CountrySupplyIncome.big` و `0_SPECTER_NatoSpainDisplay.big` هم Object/CommandSet رادار عراق را ندارند.

`Upgrade Upgrade_AmericaRadar` از `Upgrade.ini` (`Type = OBJECT`, `AcademyClassify = ACT_UPGRADE_RADAR`) است و تغییر نکرد.

## اصلاح (همان دو فایل Last-Win موجود؛ Overlay جدید ساخته نشد)

`RadarUpgrade` مؤثر حالا همان جفت موتور است:

```
Behavior = GrantUpgradeCreate ModuleTag_0xd99
  UpgradeToGrant = Upgrade_AmericaRadar
  ExemptStatus   = UNDER_CONSTRUCTION
End
Behavior = RadarUpgrade ModuleTag_0d995
  TriggeredBy    = Upgrade_AmericaRadar
  DisableProof   = No
End
```

فروش / نابودی / قطع برق: `DisableProof = No` + `KindOf POWERED` + `FireWeaponCollide RequiredStatus = SOLD` + `FireWeaponWhenDeadBehavior` حفظ شدند. `ShroudClearingRange = 280` تغییر نکرد.

Spy Satellite از رادار عراق جدا شد: CommandSet بدون `Command_SpySatelliteScan` / `Command_SpecterSpySatelliteFee` / `Command_IraqiRadarSearch`؛ Object بدون `ModuleTag_SSC` و بدون `ModuleTag_RadarSearch`. تعریف‌های جهانی `Command_SpySatelliteScan`، `SpecialPowerSpySatellite`، `SUPERWEAPON_SpySatellite` و CommandSet رادار کشورهای دیگر دست نخورده‌اند.

## BIG

| فایل | حجم | SHA-256 |
|---|---|---|
| منبع Full/Supply `_SPEC_DATA_ONE.big` | 373 955 679 | `be2f27b7c0d2ce233789909b029d24f2d14a34a6540fed4a71186c3c46095cd4` |
| این بازسازی `_SPEC_DATA_ONE.big` | 373 955 619 | `70454ee1bbe3b4a0d67855f77612e1fa3915619e619307a97849a3aa73a03533` |

ورودی‌ها: 3563 (همان تعداد). Header همچنان BIGF؛ فیلد اندازه با طول فایل یکی است. فقط دو مسیر داخلی بازنویسی شدند.

بازسازی:

```
python3 patch/tools/big/patch_spec_data_one_iraq_radar.py \
  --src-big patch/Release/WORLD_WAR_III2027_FULL/_SPEC_DATA_ONE.big \
  --out-big patch/Release/IRAQ_RADAR_SPY_SATELLITE_FIX/_SPEC_DATA_ONE.big
```
