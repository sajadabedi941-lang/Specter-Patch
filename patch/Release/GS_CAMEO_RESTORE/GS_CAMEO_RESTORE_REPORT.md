# بازیابی تصاویر اصلی دکمه‌های خرید/ساخت Global Store

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی. وجود TGA در overlay اثبات نمایش داخل ZH نیست.

## علت

زنجیرهٔ زنده:

`Iraq_MICCommandSet` → `CommandButton` → `ButtonImage` → `MappedImage` → `Texture = *.tga` → `Art\Textures\*.tga` داخل اولین BIG مالک مسیر.

DATA فعلی (`cc-vt72b-nk-hwasong`) همین نام‌ها را دارد:

- ساخت ساختمان: `Button_GlobalMarket`
- خرید داخل فروشگاه: `specbtn_mic_*`
- `MappedImage` در `SpecterUavMicCameos_Images.INI` و `IraqConstructFix_Images.INI`

PR **#693** (ریلیز `construct-button-images-2c93`) این TGAها را داخل `_SPEC_ART_ONE.big` ۴۴۷ مگابایتی گذاشت (SHA `e796fadc…`). ریلیزهای بعدی فقط DATA فرستادند. ART کامل Full Release (`_SPEC_ART_ONE.big` حدود ۲٫۱ گیگ، SHA `15ffb0dc…`) همان ۱۹ فایل را ندارد. SAGE وقتی TGA نیست، cameo قدیمی `SelectPortrait` را نشان می‌دهد.

جایگزین کردن ART ۲٫۱ گیگی با ART ۴۴۷ مگابایتی #693 مدل‌ها را حذف می‌کند. مسیرهای `Art\Textures\specbtn_mic_*.tga` یکتا هستند؛ `game.dat` فهرست `*.big` را با `_stricmp` مرتب می‌کند و اولین بایگانی مالک مسیر را نگه می‌دارد. نام `0_` قبل از `_SPEC_ART_ONE.big` و `INIZH.big` می‌آید.

`CommandSet.ini` / `CommandButton.ini` / DATA BIG تغییر نکردند (#720 دست‌نخورده). تصویر جدید ساخته نشد؛ بایت TGA از ART #693 کپی شد.

## دکمه‌ها

منبع TGA قبلی: `_SPEC_ART_ONE.big` ریلیز `construct-button-images-2c93` مسیر `Art\Textures\<name>.tga`.  
وضعیت ART نهایی بدون overlay: فایل نیست (split-zip ۴۴۵٬۹۵۳٬۸۰۹ بایت صفر `specbtn`).

### ساخت Global Store (dozer)

| دکمه | ButtonImage | فایل مورد انتظار | نسخهٔ قبلی | نسخهٔ نهایی بدون overlay |
| --- | --- | --- | --- | --- |
| `Command_ConstructIraq_MIC` | `Button_GlobalMarket` | `Button_GlobalMarket.tga` | #693 ART | نیست |
| `Command_Construct*_GlobalStore` (۲۴ کشور) | `Button_GlobalMarket` | همان | #693 ART / `CommandButton.ini` | نیست |

کشورها: America, Britain, China, France, Germany, India, Iran, Israel, Italy, Japan, Libya, Nato, NorthKorea, Pakistan, Russia, SaudiArabia, SouthAfrica, SouthKorea, Sweden, Syria, Turkey, UAE, Ukraine, Vietnam.

### خرید داخل Global Store (`Iraq_MICCommandSet` روی همهٔ `*_GlobalStore` و `Iraq_MIC`)

| دکمه | ButtonImage | فایل مورد انتظار |
| --- | --- | --- |
| `Command_ConstructIraq_MIC_Arrow` | `specbtn_mic_arrow` | `specbtn_mic_arrow.tga` |
| `Command_ConstructIraq_MIC_AN_TPY2` | `specbtn_mic_tpy2` | `specbtn_mic_tpy2.tga` |
| `Command_ConstructIraq_MIC_92N6R` | `specbtn_mic_92n6r` | `specbtn_mic_92n6r.tga` |
| `Command_ConstructIraq_MIC_S400` | `specbtn_mic_s400` | `specbtn_mic_s400.tga` |
| `Command_ConstructIraq_MIC_PantsirS1M` | `specbtn_mic_pantsir` | `specbtn_mic_pantsir.tga` |
| `Command_ConstructIraq_MIC_Krasukha4` | `specbtn_mic_krasukha` | `specbtn_mic_krasukha.tga` |
| `Command_ConstructIraq_MIC_96L6TSP` | `specbtn_mic_96l6tsp` | `specbtn_mic_96l6tsp.tga` |
| `Command_ConstructIraq_MIC_S500` | `specbtn_mic_s500` | `specbtn_mic_s500.tga` |
| `Command_ConstructIraq_MIC_HQ9` | `specbtn_mic_hq9` | `specbtn_mic_hq9.tga` |
| `Command_ConstructIraq_MIC_HT233` | `specbtn_mic_ht233` | `specbtn_mic_ht233.tga` |
| `Command_ConstructIraq_MIC_TRML4D` | `specbtn_mic_trml4d` | `specbtn_mic_trml4d.tga` |
| `Command_ConstructIraq_MIC_IRIST` | `specbtn_mic_irist` | `specbtn_mic_irist.tga` |
| `Command_ConstructIraq_MIC_US_AN_TPY2` | `specbtn_mic_ustpy2` | `specbtn_mic_ustpy2.tga` |
| `Command_ConstructIraq_MIC_THAAD` | `specbtn_mic_thaad` | `specbtn_mic_thaad.tga` |

ارجاع دکمه اشتباه نبود؛ فقط TGA در ART زنده غایب بود.

## خارج از محدوده

- Command Center ژاپن/ویتنام/کره جنوبی/شمالی (#720)
- موشک‌ها، رادار، پهپاد `specbtn_heron` / `mq4` / `orlan10` / `shahedlnchr`
- منطق خرید، قیمت، Object، `SelectPortrait`
- جایگزینی `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big`

## فایل‌ها

| فایل | حجم (بایت) | SHA-256 |
| --- | ---: | --- |
| `0_SPECTER_GlobalStoreCameos.big` | 984367 | `1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc` |
| `CommandSet.ini` (بدون تغییر #720) | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` (بدون تغییر #720) | 1337703 | `5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd` |

DATA `_SPEC_DATA_ONE.big` ریلیز `cc-vt72b-nk-hwasong` دست‌نخورده است (SHA `52baa018c53015e90bf55b1451a33d22cad9de0951b4924168287129eeb2144a`).

۱۵ TGA هر کدام ۱۲۸×۱۲۸، ۳۲ بیت، uncompressed SAGE؛ هش یکتا در `tga.sha256`.

## نصب

1. `0_SPECTER_GlobalStoreCameos.big` را **کنار** `generals.exe` بگذارید (همان پوشهٔ `_SPEC_ART_ONE.big`). نام `0_` لازم است.
2. `_SPEC_ART_ONE.big` و `_SPEC_ART_TWO.big` را عوض نکنید.
3. DATA / `Data\INI\CommandSet.ini` / `CommandButton.ini` ریلیز #720 را نگه دارید.
4. PNG داخل مخزن (`patch/Art/Textures/*.png`) نصب بازی نیست.

یا `Install_GsCameoRestore.bat` را اجرا کنید.

## آنچه ZH باید جداگانه تأیید کند

دکمهٔ ساخت Global Store تصویر اختصاصی انبار باشد نه `irq_mic`؛ ۱۴ دکمهٔ خرید داخل فروشگاه cameo `specbtn_mic_*` باشد نه atlas واحد. بدون اجرای بازی این نمایش تأیید نمی‌شود.
