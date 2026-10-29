# HT-233 / 92N6E DataLink aligned to working AN/TPY-2

مرجع سالم: `US_AN_TPY2_CombatMode` (`DisplayName = OBJECT:ANTPY2N`).  
واحدهای مؤثر چین/روسیه پس از Deploy: `ChinaVehicleHT233_CombatMode` و `Russia_92N6R_CombatMode`.  
منبع DATA: Release `supply-centre-buy-buttons` (`1e71fef6…`). فقط `_SPEC_DATA_ONE.big` بازسازی شد.

**تست داخل بازی اجرا نشده است.**

## علت دقیق

سامانهٔ رهگیری این رادارها از FCS باتری + `AirdefenseLinkRestarter` می‌آید. Restarter با `MainWeaponSwitchOffWeapon` وضعیت `NO_ATTACK` را روی FCS می‌زند. کشتن Restarter با `SURRENDER` / `DeathType = EXTRA_6` آن قفل را برمی‌دارد، ولی `CreateObjectDie` با همان EXTRA_6 بلافاصله Restarter را از `OCL_SAMBLABLA` دوباره می‌سازد.

`AN/TPY-2` از `FireControlRadarDataLink` استفاده می‌کند:

| فیلد | AN/TPY-2 (سالم) | HT-233 / 92N6E قبل از این پچ |
| --- | --- | --- |
| سلاح FCRL | `FireControlRadarDataLink` | `HT233_FireControlDataLink` / `92N6R_FireControlDataLink` |
| ExclusiveWeaponDelay | 1000 | حذف شده بود |
| PrimaryDamageRadius | 250 | 1600 / 1800 |
| DamageDealtAtSelfPosition | خیر | Yes |
| AntiBallisticMissile / AntiAirborneVehicle | خیر | Yes |
| DamageType / DeathType | SURRENDER / EXTRA_6 | همان |

تفاوت مؤثر همان Last-Win قبلی `Weapon_ZZZZ_ZZZ92N6Ht233.ini` است: پالس EXTRA_6 با شعاع ۱٫۶–۱٫۸ کیلومتر روی ALLIES از موقعیت خود رادار. این پالس Restarter همهٔ باتری‌های نزدیک را در حلقهٔ مرگ/بازساخت می‌اندازد و FCS با `NO_ATTACK` قفل می‌ماند. TPY-2 هرگز این پالس را نمی‌زند.

رهگیرها (`40N6Missile_ABM_Object` و مشابه) `SURRENDER = 0%` دارند؛ آمار خسارت/زرهٔ آن‌ها عوض نشد. مشکل از Weapon/Projectile رهگیر نبود.

## اصلاح

CombatMode چین و روسیه به همان بلوک FCRL سالم TPY-2 برگشت:

```
FireWeaponUpdate ModuleTag_FCRL
  Weapon = FireControlRadarDataLink
  ExclusiveWeaponDelay = 1000
```

نام‌های اختصاصی DataLink هم Last-Win شدند تا اگر ارجاعی باقی بماند همان آمار TPY-2 را داشته باشند (شعاع ۲۵۰، بدون self-position، بدون AntiBM).

`US_AN_TPY2`، `IsraelTPY2CombatMode`، رادار عراق، Supply Centre، و سلاح‌های رهگیر دست نخورده‌اند.

## فایل‌های تغییرکرده

| مسیر داخل BIG | نقش |
| --- | --- |
| `Data\INI\Object\zzzzz_SpecterRadarTpy2Cue\ChinaVehicleHT233_CombatMode.ini` | FCRL = TPY-2 |
| `Data\INI\Object\zzzzz_SpecterRadarTpy2Cue\Russia_92N6R_CombatMode.ini` | FCRL = TPY-2 |
| `Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini` | خنثی‌سازی DataLinkهای اختصاصی |

## تست استاتیک (۲۴/۲۴)

| سناریو | شناسایی (ماژول) | انتخاب هدف (FCS/Beam) | شلیک رهگیر | آسیب واقعی |
| --- | --- | --- | --- | --- |
| AN/TPY-2 فعال | `RadarTrackingBeam` + StealthDetect + Vision 900 باقی است | FCRL = `FireControlRadarDataLink` + delay 1000 | سلاح‌های Patriot/THAAD همچنان CRUSH | داخل بازی اجرا نشد |
| HT-233 فعال | Beam + StealthDetect حفظ شد | FCRL اکنون همان TPY-2 است | HQ-9 ABM همچنان CRUSH | داخل بازی اجرا نشد |
| 92N6E فعال | Beam + StealthDetect حفظ شد | FCRL اکنون همان TPY-2 است | S-400 ABM همچنان CRUSH | داخل بازی اجرا نشد |

تست ترکیبی چند پدافند / چند موشک ورودی هم اجرا نشد.

آنچه استاتیک ثابت می‌کند: زنجیرهٔ cue با TPY-2 یکی شد و آمار رهگیر عوض نشد. آنچه ثابت نمی‌کند: تشخیص، قفل، شلیک و انهدام داخل بازی.

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 008 909 | `242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d` |

ورودی‌ها: 3569 → 3572. ART تغییر نکرد.

## نصب

1. `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` و overlayهای `0_SPECTER_*` را نگه دارید.
2. فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید.
3. پچ با یک فایل DATA و ترتیب بارگذاری فعلی SPECTER کامل است.
