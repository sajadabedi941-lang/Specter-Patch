# SPECTER — بانک کامل تجهیزات زمینی

زمان ممیزی: ۱ نوامبر ۲۰۲۶ (Asia/Tehran). **فقط خواندنی.** هیچ فایل DATA / ART / BIG / Object / CommandSet تغییر نکرد.
Zero Hour اجرا نشده و ادعای تست داخل بازی نیست.

## منبع

| فیلد | مقدار |
|---|---|
| DATA منتشرشده | `s300-radar-drones` |
| آرشیو | `_SPEC_DATA_ONE.big` |
| SHA-256 | `aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53` |
| قانون بارگذاری | Objectها last-win به ترتیب BIG؛ `CommandSet*.ini` / `CommandButton*.ini` ریشه به‌صورت الفبایی (overlayهای ZZZZ) |
| قیمت / زمان | Object `BuildCost` / `BuildTime` |
| نام نمایشی | `DisplayName` → `generals.csf` |
| خسارت / برد | Weapon `PrimaryDamage` / `AttackRange` |
| سرعت | Locomotor `Speed` |
| وجود فایل W3D روی دیسک | Unknown (پک DATA-only؛ ART BIG در این نصب نیست) |

عضویت در منوی ساخت فقط با زنجیرهٔ واقعی ثبت شد: Object last-win ← CommandButton.Object ← اسلات CommandSet ← CommandSet استفاده‌شده توسط ساختمان last-win (شامل CommandSetUpgrade). هیچ تجهیزی فقط به‌خاطر نامش فعال فرض نشد. فیلد غایب = Unknown.

## آمار کل

| شاخص | تعداد |
|---|---:|
| تجهیزات زمینی/نظامی در بانک | 1404 |
| A — در منوی ساخت زنده | 659 |
| B — تعریف معتبر ولی خارج از منوی زنده | 745 |
| C — ناقص / اتصال خراب | 1 |
| D — تکراری / کلون | 741 |
| پیوست هوایی | 1015 |
| پیوست دریایی | 6 |
| پیوست پیاده‌نظام | 353 |

## تعداد هر دسته

| Category | Count | In menu | Unused | Broken |
|---|---:|---:|---:|---:|
| Tanks | 115 | 36 | 79 | 0 |
| APC and IFV | 68 | 19 | 49 | 0 |
| Armored Vehicles | 302 | 47 | 255 | 1 |
| Air Defense | 308 | 135 | 173 | 0 |
| Artillery | 53 | 43 | 10 | 0 |
| Rocket and Missile Launchers | 396 | 302 | 94 | 0 |
| Radar and Electronic Warfare | 80 | 28 | 52 | 0 |
| Support Vehicles | 39 | 28 | 11 | 0 |
| Drones and UAV Launchers | 43 | 21 | 22 | 0 |
| Other Military | 0 | 0 | 0 | 0 |

## کشورهای مرجع

| کشور | Object منتسب | در منوی ساخت زنده |
|---|---:|---:|
| America | 81 | 50 |
| China | 69 | 58 |
| Russia | 82 | 52 |
| Iraq | 80 | 62 |
| Iran | 77 | 58 |
| Israel | 56 | 42 |
| Spain | 10 | 10 |
| Arabic Alliance | 68 | 38 |

Arabic Alliance = Side GLA / `Arb_*` / `Arab_*` / `Arabic_*`. عراق فقط `Iraq_*` است. این دو ادغام نشدند.

اسپانیا War Factory فعال ندارد. Objectهای واقعی با پیشوند `Spain_` : **10** — همگی محصول Missile Factory هستند نه WF:

- `Spain_Albatros` — Albatros — منو=Yes — Spain_MissileFactory
- `Spain_Armada` — Armada — منو=Yes — Spain_MissileFactory
- `Spain_Castilla` — Castilla — منو=Yes — Spain_MissileFactory
- `Spain_Cid` — Cid — منو=Yes — Spain_MissileFactory
- `Spain_Escorial` — Escorial — منو=Yes — Spain_MissileFactory
- `Spain_Halcon` — Halcon — منو=Yes — Spain_MissileFactory
- `Spain_Hispania` — Hispania — منو=Yes — Spain_MissileFactory
- `Spain_Iberia` — Iberia — منو=Yes — Spain_MissileFactory
- `Spain_Pelayo` — Pelayo — منو=Yes — Spain_MissileFactory
- `Spain_Tridente` — Tridente — منو=Yes — Spain_MissileFactory

## پدافند قدرتمند آمریکا (جدا از SHORAD)

| Object | نام نمایشی | Side | منو | قیمت |
|---|---|---|---|---|
| `AmericaRadarAN/TPY2` | Unknown | America | No | Unknown |
| `US_AN_TPY2` | AN/TPY2
AESA
MultiTrack | America | Yes | 2600 |
| `US_AN_TPY2_CombatMode` | AN/TPY2
AESA
MultiTrack | America | No | Unknown |
| `US_M1120AI_Launcher` | THAAD | America | No | Unknown |
| `US_M1120AI_Launcher_ABM` | THAAD | America | No | Unknown |
| `US_THAAD` | M1120 Thaad
x10 AAM
x2 ABM
Multi Attack | America | Yes | 3000 |
| `US_THAAD_CombatMode` | M1120 Thaad
x10 AAM
x2 ABM
Multi Attack | America | No | Unknown |
| `US_THAAD_PackMode` | M1120 Thaad
x10 AAM
x2 ABM
Multi Attack | America | No | 3000 |
| `US_THAAD_Site_AI` | SAM Site | America | Yes | 2000 |
| `Iraq_MIC_AN_TPY2` | AN/TPY2S
Multitrack
Deployable
Jam Resist | Iraq | Yes | 6000 |
| `Iraq_MIC_THAAD` | M1120 Thaad
x10 AAM
x2 ABM
Multi Attack | Iraq | Yes | 15000 |
| `Iraq_MIC_US_AN_TPY2` | AN/TPY2
AESA
MultiTrack | Iraq | Yes | 10000 |
| `IsraelTPY2CombatMode` | Unknown | Israel | No | Unknown |
| `Israel_AN_TPY2` | AN/TPY2S
Multitrack
Deployable
Jam Resist | Israel | Yes | 2600 |

Avenger / Linebacker / Pantsir / Tor / Roland پدافند معمولی‌اند و اینجا نیستند.

## مشکلات کشف‌شده

- ناقص/خراب (گروه C): **1**
- خارج از منوی زنده (گروه B): **745**
- گروه کلون/تکراری: **135** گروه، **741** Object با پرچم D

### گروه C

| Object | مشکل |
|---|---|
| `Israel_AD_Barak8` | WeaponSet names not in Weapon.ini: Israel_Weapon_Barak8,None |

### زنجیرهٔ استفاده‌نشدهٔ روسیه `_T`

بولدوزر زنده `RussiaWarFactory` + `RussiaWarFactoryCommandSet` را می‌سازد. `RussiaWarFactoryCommandSet_T3` دکمه‌هایی به نام‌های ناموجود دارد (`RussiaTankT72B3`, `Russian_T15`, `Russia_Krasukha-4`). Objectهای واقعی: `RussiaTankT72B3M`, `RussianTankT15`, `RussiaVehicleKrasukha4`.

### Israel leftover

IDF زنده = `AirF_AmericaWarFactory`. `Israel_WarFactory` + Integrity CS روی بولدوزر زنده نیست. دکمه‌های Barak8/IronDome در CommandButton نیستند.

### Arabic Alliance در برابر عراق

Objectهای AA: 68. Objectهای عراق: 72. AA از کمبو مخفی است (`FactionGLA` PlayableSide=No) ولی تعریف‌ها مانده‌اند.

## فایل‌ها

- `SPECTER_COMPLETE_EQUIPMENT_DATABASE.csv`
- `SPECTER_COMPLETE_EQUIPMENT_DATABASE.xlsx` (شیت‌های درخواستی)
- `SPECTER_EQUIPMENT_APPENDIX_AIR_NAVAL_INFANTRY.csv`
- همین گزارش

Unknown یعنی فیلد در INI last-win نبود. هیچ عدد یا نامی حدس زده نشد.
