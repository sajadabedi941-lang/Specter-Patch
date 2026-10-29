# حذف Arabic Alliance از فهرست کشورهای قابل‌انتخاب

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## این کشور چیست؟

در DATA زنده، «Arabic Alliance» یک PlayerTemplate جدا نیست. اسلات **`FactionGLA`** است:

- `Side = GLA` / `StartingBuilding = GLACommandCenter`
- `DisplayName = INI:FactionGLA`
- در `Data\English\generals.csf` مقدار `INI:FactionGLA` = **Arabic Alliance**

حذف فقط نام از CSF، کشور را از منو حذف نمی‌کرد؛ `PlayableSide = Yes` آن را در اسکرمیش/چندنفره نگه می‌داشت.

## اصلاح (فقط PlayerTemplate.ini)

داخل بلوک `PlayerTemplate FactionGLA`:

| خط | قبل | بعد |
| --- | --- | --- |
| `PlayableSide` | `Yes` | `No` |
| `OldFaction` | `Yes` | `No` (تا فیلتر «فکشن‌های اورجینال» هم نشانش ندهد) |

قالب `FactionGLA` حذف نشد (نقشه‌ها/اسکریپت‌هایی که این نام را دارند crash نشوند).

`PlayerTemplate.ini` شل در `Data\INI\PlayerTemplate.ini` نصب می‌شود تا LocalFileSystem به آرشیوها غلبه کند.

## آنچه باقی ماند و چرا

جست‌وجوی مجدد «Arabic Alliance» / `ArabicAlliance` پس از پچ:

| فایل | دلیل ماندن |
| --- | --- |
| پوشهٔ Object `...\Arabic Alliance\` (~۷۰ فایل) + `ArabicArmy_*` | `EgyptDozerCommandSet` هنوز War Factory / Aljarrah / 59N6E / D30 عربی می‌سازد. حذف Objectها مصر را می‌شکند. عراق/سعودی/امارات/سوریه/لیبی از این دکمه‌ها استفاده نمی‌کنند. |
| `CommandSet_ArabicAllianceUnlock.ini` | فایل اضافه؛ ControlBar فقط `Data\INI\CommandSet.ini` را می‌خواند. دست نخورده برای سازگاری. |
| `CommandButton_ArabicAllianceUnlock.ini` | همین؛ ControlBar فایل اضافه را بار نمی‌کند. |
| `Science_ArabicAllianceUnlock.ini` | جدول Science از `Science.ini` است، نه این فایل اضافه. |
| کامنت در `F16C_B60.ini` و `Jiny.ini` | فقط کامنت؛ Object مال مصر/GLA داخلی. |
| CSF `INI:FactionGLA` = Arabic Alliance | رشتهٔ نمایشی قالب غیرفعال. تغییر CSF روی ART/زبان ریسک دارد و فهرست انتخاب را عوض نمی‌کند. |
| `AIData.ini` `SkirmishBuildList GLA` | اگر نقشه‌ای AI را مجبور به GLA کند. فهرست انتخاب کشور از PlayableSide است. |

## کشورهای حفظ‌شده (PlayableSide = Yes، بایت قالب عوض نشد)

عراق، عربستان سعودی، امارات، سوریه، لیبی، آمریکا، روسیه، چین، ایران، ژاپن، ویتنام، و بقیهٔ قالب‌های قبلی به‌جز GLA.

ترتیب قالب‌ها عوض نشد.

## دست‌نخورده

- منوی رادار و Shahed_136 Mobile Launcher (Fire + قیمت ۸۰۰۰)
- رادار ویتنام `TriggeredBy`
- `CommandSet.ini` / `CommandButton.ini` (هش همان `vietnam-radar-minimap`)
- ART اصلی و overlayهای `0_`

## SHA-256

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075569 | `751550a6aee5d3bd9ad475b6625744d7b7a4a26e0a9551fd845e313c0f87b6b4` |
| `CommandSet.ini` | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |
| `PlayerTemplate.ini` | 43897 | `7245baec02a5a8c7af9792fa2c1e451282c0c1ddba87506ae5398cdfbaec9a20` |
