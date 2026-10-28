# SPECTER Unified Install

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

`main` گیت‌هاب هنوز PRهای #718–#722 را ادغام نکرده (همه OPEN). این بسته از زنجیرهٔ سازگار ریلیزها ساخته شد، نه از روی‌هم‌گذاری BIGهای قدیمی:

`wf-remove-rs24-df41-khormshar` (#718) → `radar-no-spy-sat` (#719) → `cc-vt72b-nk-hwasong` (#720) → overlay `gs-cameo-restore` (#721) → DATA+overlay `missile-jlmn-buttons` (#722).

DATA نهایی همان `_SPEC_DATA_ONE.big` شمارهٔ #722 است (بازسازی #720 + تصاویر J/L/M/N).

## ART اصلی کجاست؟

فایل‌های اصلی ART در مخزن git به‌صورت BIG کامل ۲٫۱ گیگی نیستند (فقط آرشیو ناقص/اسپلیت). نسخهٔ معتبر روی GitHub Release است:

ریلیز `WORLD_WAR_III2027-Full-Release` — دانلود و SHA-256 در همین محیط تأیید شد:

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_ART_ONE.big` | 2145283309 | `15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66` |
| `_SPEC_ART_TWO.big` | 307254782 | `a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af` |

همین بایت‌ها دوباره ساخته یا کوتاه نشدند.

## چرا یک ZIP شامل هر دو ART منتشر نمی‌شود

سقف دارایی GitHub **۲ گیگابایت** است (`2,147,483,648` بایت).

| مجموعه | بایت | نسبت به سقف |
| --- | ---: | --- |
| ART ONE به‌تنهایی | 2,145,283,309 | زیر سقف (~۲٫۱ مگابایت فاصله) |
| ART ONE + ART TWO | 2,452,538,091 | **بالای سقف** (~۲٫۲۸ GiB) |
| ART ONE + TWO + DATA | 2,826,613,573 | **بالای سقف** (~۲٫۶۳ GiB) |

بنابراین **نمی‌توان** یک ZIP واحد حاوی هر دو ART اصلی را روی GitHub گذاشت. این ZIP را «نصب کامل مستقل» معرفی نمی‌کنیم.

`_SPEC_ART_TWO.big` اصلی داخل همین ZIP است. `_SPEC_ART_ONE.big` اصلی به‌صورت دارایی جدا روی همین ریلیز `specter-unified` (و همان بایت روی Full Release) منتشر می‌شود.

## ARTهایی که نباید استفاده شوند

| منبع | بایت | SHA-256 | دلیل رد |
| --- | ---: | --- | --- |
| `construct-button-images-2c93` | 447200634 | `e796fadc…` | ART ناقص؛ مدل‌ها حذف می‌شوند |
| اسپلیت داخل مخزن `_SPEC_ART_ONE.zip` | ~445953809 | — | ART ناقص |
| `s-art-split-2gib` ART ONE | 2144061050 | `dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2` | با Full Release یکی نیست |
| `specter-spec-art-data` ART ONE | 2144972013 | `9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8` | با Full Release یکی نیست |

Installer فایل با اندازهٔ غیر از Full Release را کپی نمی‌کند. اگر ART اصلی کنار `generals.exe` باشد، حفظ می‌شود.

## محتوای ZIP

| فایل | مقصد نصب | نقش |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | کنار `generals.exe` | DATA نهایی |
| `_SPEC_ART_TWO.big` | کنار exe | ART TWO اصلی Full Release |
| `CommandSet.ini` | `Data\INI\CommandSet.ini` | منوی زنده ControlBar |
| `CommandButton.ini` | `Data\INI\CommandButton.ini` | دکمه‌های زنده ControlBar |
| `0_SPECTER_GlobalStoreCameos.big` | کنار exe، پیشوند `0_` | TGA فروشگاه جهانی #721 |
| `0_SPECTER_MissileJLMNCameos.big` | کنار exe، پیشوند `0_` | TGA موشک J/L/M #722 |
| `ART_ONE_REQUIRED.txt` | — | نشانی و هش ART ONE |

`CommandSet.ini` و `CommandButton.ini` بایت‌به‌بایت با همین فایل‌ها داخل DATA یکی هستند.

باید جداگانه تهیه شود:

`_SPEC_ART_ONE.big` — 2145283309 بایت — SHA `15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66`

https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/WORLD_WAR_III2027-Full-Release/_SPEC_ART_ONE.big

## Overlay و ترتیب بارگذاری

`game.dat` فهرست `*.big` را با `_stricmp` مرتب می‌کند؛ اولین بایگانی مالک مسیر می‌ماند (`replace=0`).

- `0_SPECTER_GlobalStoreCameos.big` قبل از `_SPEC_ART_ONE.big`
- `0_SPECTER_MissileJLMNCameos.big` قبل از `_SPEC_ART_ONE.big`
- بین دو overlay: GlobalStore قبل از MissileJLMN (`G` < `M`)
- مسیرها یکتا هستند (۱۵× `specbtn_*` / `Button_GlobalMarket` در برابر ۳× `specter_missile_j/l/m`)؛ تداخل نیست.

ART اصلی بازسازی نمی‌شود؛ overlay فقط TGA اضافه را first-win می‌کند.

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

## آنچه این ZIP نصب کامل مستقل نیست

- `_SPEC_ART_ONE.big` داخل ZIP نیست (سقف GitHub).
- DATA ریلیزهای #718–#721 جایگزین این DATA نمی‌شود.
- PNG شل و `CommandSet_*.ini` اضافه نصب نمی‌شود.

## SHA-256 (منبع تأییدشده)

جدول کامل پس از بسته‌بندی در `SHA256SUMS.txt` و `ZIP_MANIFEST.txt` نوشته می‌شود. مقادیر ثابت payload:

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075482 | `c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac` |
| `_SPEC_ART_TWO.big` | 307254782 | `a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `0_SPECTER_GlobalStoreCameos.big` | 984367 | `1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc` |
| `0_SPECTER_MissileJLMNCameos.big` | 147733 | `618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae` |
| `_SPEC_ART_ONE.big` (دارایی جدا) | 2145283309 | `15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66` |

هش ZIP در `SPECTER_UNIFIED_INSTALL.zip.sha256` کنار فایل ZIP نوشته می‌شود (بعد از بسته‌بندی).
