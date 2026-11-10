# نقشهٔ رادار ویتنام باز نمی‌شد

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## علت

`Vietnam_RadarStation` ارتقای `Upgrade_AmericaRadar` را با `GrantUpgradeCreate` می‌دهد، اما روی `RadarUpgrade` خط `TriggeredBy` نبود. بدون آن، ماژول رادار/مینی‌مپ فعال نمی‌شود.

الگوی تأییدشده در همین DATA (ژاپن، ایران، overlay عراق `zzzzz_SpecterIraqRadar`، `AmericaRadarStation`):

```
  Behavior = GrantUpgradeCreate ModuleTag_0xd99
    UpgradeToGrant    = Upgrade_AmericaRadar
    ExemptStatus      = UNDER_CONSTRUCTION
  End
  Behavior        = RadarUpgrade ModuleTag_0d995
    TriggeredBy   = Upgrade_AmericaRadar
    DisableProof  = No
  End
```

`Upgrade.ini`: `Upgrade Upgrade_AmericaRadar` با `Type = OBJECT` از قبل وجود دارد. نام جدیدی حدس زده نشد (`Upgrade_VietnamRadar` ساخته نشد).

## تعریف‌های تکراری

دو فایل Object با نام `Vietnam_RadarStation` (هر دو بدون TriggeredBy):

1. `Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_RadarStation.ini` (کپی donor عراق)
2. `Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini`

هر دو اصلاح شدند تا first-win یا last-win هر کدام باشد نقشه کار کند. Object سوم ساخته نشد.

کشور سالم برای مقایسه: `Japan_RadarStation` در `Japan_RadarStation.ini` — همان `TriggeredBy   = Upgrade_AmericaRadar`.

## خط‌های اضافه‌شده (هر دو فایل، CRLF)

قبل:

```
  Behavior        = RadarUpgrade ModuleTag_0d995
    DisableProof  = No
  End
```

بعد (همان بایت ژاپن):

```
  Behavior        = RadarUpgrade ModuleTag_0d995
    TriggeredBy   = Upgrade_AmericaRadar
    DisableProof  = No
  End
```

فقط همین یک خط در هر فایل. `GrantUpgradeCreate`، `KindOf`، `CommandSet`، منو، پهپادها دست نخورده‌اند.

## آنچه تغییر نکرد

- `Vietnam_RadarStationCommandSet` (اسلات ۱ RadarSearch، ۲–۴ پهپاد، ۹–۱۲ Heron/MQ-4/Orlan/Shahed، ۱۴ Sell)
- `SpecterRadar_ShahedLauncher`: Fire ایران، قیمت ۸۰۰۰
- `CommandSet.ini` / `CommandButton.ini` بایت‌به‌بایت همان `radar-shahed-fire-8000`
- رادار کشورهای دیگر
- ART و overlayهای `0_`

## SHA-256

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075571 | `a71c3f902af8c08d18d1db9bbbcc2d231fafd77d2dde3f2bf7c6e8268f132c82` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |

منبع DATA: ریلیز `radar-shahed-fire-8000` (SHA `71559b01…`). Overlayهای `0_` و ART اصلی را نگه دارید.
