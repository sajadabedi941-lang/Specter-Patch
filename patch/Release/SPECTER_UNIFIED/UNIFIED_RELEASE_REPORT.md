# SPECTER Unified Install

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

`main` گیت‌هاب هنوز PRهای #718–#722 را ادغام نکرده (همه OPEN). این بسته از زنجیرهٔ سازگار ریلیزها ساخته شد، نه از روی‌هم‌گذاری BIGهای قدیمی:

`wf-remove-rs24-df41-khormshar` (#718) → `radar-no-spy-sat` (#719) → `cc-vt72b-nk-hwasong` (#720) → overlay `gs-cameo-restore` (#721) → DATA+overlay `missile-jlmn-buttons` (#722).

DATA نهایی همان `_SPEC_DATA_ONE.big` شمارهٔ #722 است (بازسازی #720 + تصاویر J/L/M/N). ART ONE/TWO داخل بسته نیست.

## محتوای بسته

| فایل | مقصد نصب | نقش |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | کنار `generals.exe` | DATA نهایی |
| `CommandSet.ini` | `Data\INI\CommandSet.ini` | منوی زنده ControlBar |
| `CommandButton.ini` | `Data\INI\CommandButton.ini` | دکمه‌های زنده ControlBar |
| `0_SPECTER_GlobalStoreCameos.big` | کنار exe، پیشوند `0_` | TGA فروشگاه جهانی #721 |
| `0_SPECTER_MissileJLMNCameos.big` | کنار exe، پیشوند `0_` | TGA موشک J/L/M #722 |

`CommandSet.ini` و `CommandButton.ini` بایت‌به‌بایت با همین فایل‌ها داخل DATA یکی هستند.

## Overlay و ترتیب بارگذاری

`game.dat` فهرست `*.big` را با `_stricmp` مرتب می‌کند؛ اولین بایگانی مالک مسیر می‌ماند.

- `0_SPECTER_GlobalStoreCameos.big` قبل از `_SPEC_ART_ONE.big`
- `0_SPECTER_MissileJLMNCameos.big` قبل از `_SPEC_ART_ONE.big`
- بین دو overlay: GlobalStore قبل از MissileJLMN (`G` < `M`)
- مسیرها یکتا هستند (۱۵× `specbtn_*` / `Button_GlobalMarket` در برابر ۳× `specter_missile_j/l/m`)؛ تداخل نیست.

ART اصلی جایگزین نمی‌شود.

## حفظ اصلاحات

| مورد | وضعیت در این DATA/INI |
| --- | --- |
| #718 WF RU/CN/IR | Object زنده: `RussiaWarFactoryCommandSet` / `PLAWarFactoryCommandSet` / `IranWarfactoryCommandSet` بدون RS-24 / DF-41 / Khorramshahr |
| #719 Spy Sat | هیچ `CommandSet` در `CommandSet.ini` حاوی `SpySatellite` نیست |
| #720 CC | JP/VN/SK فقط VT72B؛ NK = VT72B + Hwasong15BB |
| #721 Global Store | `Button_GlobalMarket` + `specbtn_mic_*` در CommandButton؛ TGA در overlay GS |
| #722 J/L/M/N | ۲۵× `Neon`، `Futuristic`، `Nuclear`، `pla_df41`؛ TGA در overlay JLMN |
| AD cap | `MaxSimultaneousOfType = 3` در فایل‌های پدافند |
| Shahed range 3000 | روی کپی‌های رادار/لانچر |
| کارخانه K/L/M/N | اسلات‌ها در CommandSet؛ Objectها `Factory_KhormsharOnce` / `Factory_RS24YarsOnce` / `Factory_DF41Once` |
| Fire ایران | `IranKhorramshahrFireCommandSet` و سه مجموعهٔ دیگر |

فهرست A–I کشورها و A–K عراق در کارخانهٔ موشکی جابه‌جا نشد.

## آنچه نصب نمی‌شود

- `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big`
- DATA ریلیزهای #718–#721
- PNG شل
- `CommandSet_*.ini` اضافه

## SHA-256 (منبع تأییدشده)

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075482 | `c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `0_SPECTER_GlobalStoreCameos.big` | 984367 | `1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc` |
| `0_SPECTER_MissileJLMNCameos.big` | 147733 | `618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae` |

هش ZIP در `SPECTER_UNIFIED_INSTALL.zip.sha256` کنار فایل ZIP نوشته می‌شود (بعد از بسته‌بندی).
