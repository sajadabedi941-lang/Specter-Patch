# Supply Centre in-building buy buttons (America / China / Russia / France)

مرجع سالم: `AirF_AmericaSupplyCenter` (اسرائیل).  
منبع DATA: Release `iraq-spy-supply-centre` (`45250b1a…`, 373 991 918 بایت).  
فقط `_SPEC_DATA_ONE.big` بازسازی شد. ART و overlay دست نخورده‌اند.

**تست داخل بازی اجرا نشده است.** این گزارش فقط اعتبارسنجی استاتیک Last-Win است.

## مرجع اسرائیل (دست‌نخورده)

| مورد | مقدار |
| --- | --- |
| ساختمان قابل بازی | `AirF_AmericaSupplyCenter` (`Data\INI\Object\Specter\Israel Defense Forces\Buildings\Supply.ini`) |
| CommandSet | `AirF_AmericaSupplyCenterCommandSet` **داخل `CommandSet.ini`** |
| اسلات | `1 = AirF_Command_ConstructAFGChinook`، `13 = Rally`، `14 = Sell` |
| دکمه | `AirF_Command_ConstructAFGChinook` = `UNIT_BUILD` در `CommandButton.ini` |
| واحد | `AFG_AmericaVehicleChinook` (Side=Israel، HARVESTER، ChinookAIUpdate) |
| Prerequisites | `;Object = AmericaSupplyCenter` (غیرفعال) |

`Israel_SupplyCenter` مرجع سالم نیست: CommandSet آن در `CommandSet_Israel_Integrity.ini` خالی است. بولدوزر اسرائیل اسلات ۵ = `AirF_Command_ConstructAmericaSupplyCenter`.

## علت مشترک چهار کشور

Last-Win قبلی ساختمان‌های آمریکا / چین / روسیه را به نام‌های `*_CountryIncome` بست. این نام‌ها **در `CommandSet.ini` وجود ندارند** و فقط در فایل overlay / ZZZZ تعریف می‌شوند. اگر آن CommandSet به نوار فرمان وصل نشود، داخل ساختمان دکمه خرید دیده نمی‌شود.

فرانسه نام هسته‌ای درست داشت، ولی تعریف `CommandSet.ini` فقط `14 = Command_Sell` است؛ دکمه خرید فقط از ادغام فایل بعدی می‌آمد.

اسرائیل از نام CommandSet هسته‌ای + دکمه `UNIT_BUILD` در `CommandButton.ini` + Prerequisites غیرفعال استفاده می‌کند. الگوی اصلاح همان ساختار است، نه کپی واحدهای اسرائیل.

`SpawnBehavior` اسرائیل هم دارد. این پچ spawn را برنداشت، ولی آن را راه‌حل خرید داخل ساختمان حساب نمی‌کند.

---

## America

**علت اصلی:** ساختمان Last-Win به `AmericaSupplyCenterCommandSet_CountryIncome` اشاره می‌کرد (نام غیر هسته‌ای). دکمه اختصاصی `Command_ConstructAmericaSupplyChinook_USA` فقط در فایل اضافه بود. `AmericaSupplyChinook_USA` شرط فعال `Prerequisites { Object = AmericaSupplyCenter }` داشت؛ Chinook سالم اسرائیل همان شرط را کامنت کرده. این شرط می‌تواند دکمه `UNIT_BUILD` را روی اولین/تنها Supply Centre مخفی یا غیرفعال کند.

**فایل‌ها / بخش‌ها:**
- `patch/Data/INI/Object/zzzzz_SpecterSupplyCentreBuy/AmericaSupplyCenter.ini` — `CommandSet = AmericaSupplyCenterCommandSet`
- `.../AmericaSupplyChinook_USA.ini` — Prerequisites کامنت شد (`؛Object = AmericaSupplyCenter`)
- `CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini` و `CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini` — اسلات ۱/۱۳/۱۴/۱۶
- `CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini` — `UNIT_BUILD` → `AmericaSupplyChinook_USA`

**دکمه‌ها و تولید:** اسلات ۱ = Chinook اختصاصی آمریکا (Side=America، HARVESTER، ChinookAIUpdate، قیمت ۱۲۰۰ / ۱۰ ثانیه بدون تغییر). اسلات ۱۶ = M-ATV_AI موجود در `CommandSet.ini` حفظ شد. خرید واقعی از `UNIT_BUILD` است، نه spawn.

**تست استاتیک:** CommandSet هسته‌ای فعال؛ دکمه → Object معتبر؛ Prerequisites فعال نیست؛ overlay+DATA همان Last-Win را می‌دهد.

**تست داخل بازی:** اجرا نشده.

---

## China

**علت اصلی:** ساختمان به `ChinaSupplyCenterCommandSet_CountryIncome` اشاره می‌کرد. خود دکمه کامیون در `CommandSet.ini` / `CommandButton.ini` درست بود، ولی وابستگی به نام غیر هسته‌ای همان الگوی شکننده آمریکا/روسیه را داشت.

**فایل‌ها / بخش‌ها:**
- `.../ChinaSupplyCenter.ini` — `CommandSet = ChinaSupplyCenterCommandSet`
- Last-Win هر دو نام CommandSet چین به `1 = Command_ConstructChinaVehicleSupplyTruck`، ۱۳ Rally، ۱۴ Sell
- Object کامیون (`ChinaVehicleSupplyTruck`، Side=China) بدون تغییر قیمت/مدل/زمان

**دکمه‌ها و تولید:** اسلات ۱ = کامیون اختصاصی چین. `UNIT_BUILD` واقعی.

**تست استاتیک:** زنجیره دکمه→Object و Side=China تأیید شد.

**تست داخل بازی:** اجرا نشده.

---

## Russia

**علت اصلی:** ساختمان به `RussiaSupplyCenterCommandSet_CountryIncome` اشاره می‌کرد. تعریف هسته‌ای `CommandSet.ini` اسلات ۱ = کامیون چین (Side=China؛ اگر فیلتر Side باشد برای بازیکن روسیه دیده نمی‌شود) و اسلات ۲ = Mi-8 (HARVESTER نیست). ادغام CommandSet اسلات حذف‌شده را نگه می‌دارد؛ اسلات ۲ باید بازنویسی شود.

**فایل‌ها / بخش‌ها:**
- `.../RussiaSupplyCenter.ini` — `CommandSet = RussiaSupplyCenterCommandSet`
- `.../RussiaSupplyTruck_CountryIncome.ini` — واحد اختصاصی روسیه بدون تغییر آمار
- Last-Win هر دو نام روسیه: اسلات ۱ = `Command_ConstructRussiaSupplyTruck_CountryIncome`، اسلات ۲ = Rally (خنثی‌سازی Mi-8)، ۱۳ Rally، ۱۴ Sell

**دکمه‌ها و تولید:** اسلات ۱ = کامیون اختصاصی روسیه (Side=Russia، HARVESTER، SupplyTruckAIUpdate، قیمت ۶۰۰ / ۱۰ ثانیه). Mi-8 در لیست خرید نیست.

**تست استاتیک:** اسلات ۲ دیگر Mi-8 نیست؛ دکمه → Object معتبر.

**تست داخل بازی:** اجرا نشده.

---

## France

**علت اصلی:** `FranceSupplyCenterCommandSet` در `CommandSet.ini` فقط Sell است. دکمه و Object (`Command_ConstructFranceHelicopterCH47F` → `FranceHelicopterCH47F`) از قبل وجود داشتند. بدون Last-Win کامل اسلات ۱ (و Rally مثل اسرائیل) نوار خرید خالی می‌ماند.

**فایل‌ها / بخش‌ها:**
- `.../FranceSupplyCenter.ini` — همان `FranceSupplyCenterCommandSet` (نام هسته‌ای)
- Last-Win: `1 = Command_ConstructFranceHelicopterCH47F`، `13 = Rally`، `14 = Sell`
- Object `FranceHelicopterCH47F` دست‌نخورده (Side=France، HARVESTER، ChinookAIUpdate)

**دکمه‌ها و تولید:** اسلات ۱ = CH47F اختصاصی فرانسه. هلیکوپترهای رزمی (Tiger / NH90 / Caracal) همچنان در Helicopter Base هستند.

**تست استاتیک:** اسلات ۱/۱۳/۱۴ و زنجیره دکمه→Object تأیید شد.

**تست داخل بازی:** اجرا نشده.

---

## لایه Last-Win و نصب

| مسیر داخل BIG | نقش |
| --- | --- |
| `Data\INI\CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini` | Last-Win CommandSet چهار کشور |
| `Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini` | لایهٔ بعدی (پس از ZZZZ) با همان محتوا |
| `Data\INI\CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini` | دکمه‌های USA Chinook و کامیون روسیه |
| `Data\INI\Object\zzzzz_SpecterSupplyCentreBuy\*.ini` | چهار ساختمان + واحدهای اختصاصی |

اسرائیل، رادار عراق (`TriggeredBy = Upgrade_AmericaRadar`، اسلات ۱/۲ Camo/MTS)، 92N6E و S-400 ABM حفظ شدند.

بارگذاری فعال SPECTER (overwrite=FALSE، اولین مسیر فایل برنده است؛ نام Object/CommandSet با ترتیب پارس Last-Win می‌شود):

`0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`

مسیرهای یکتای `zzzzz_*` / `CommandSet_ZZZZ_ZZZZZ*` داخل DATA آخرین پارس هستند.

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 373 994 395 | `1e71fef6c289089bc46836520f59faf246049db3b9512ad1529a2cda467207e7` |

ورودی‌ها: 3568 → 3569. ART تغییر نکرد.

## نصب

1. نسخهٔ فعلی SPECTER را با `_SPEC_DATA_ONE.big` + دو ART نگه دارید.
2. فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید.
3. overlayهای `0_SPECTER_*.big` را حذف نکنید.
4. `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` را عوض نکنید.

این پچ به‌تنهایی و با جایگزینی همان یک فایل DATA با روش نصب فعلی سازگار است.
