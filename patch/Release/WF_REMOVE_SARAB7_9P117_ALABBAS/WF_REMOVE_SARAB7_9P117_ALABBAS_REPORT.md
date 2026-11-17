# War Factory: remove Sarab7 / 9P117 / AlAbbas buy options (7 countries)

منبع DATA: Release `ht233-92n6e-tpy2-cue` (`242a7c81…`). فقط `_SPEC_DATA_ONE.big` بازسازی شد.

**تست داخل بازی اجرا نشده است.**

## علت

`CommandSet.ini` داخل BIG فعال (نه فایل‌های loose کشور) آخرین تعریف مشترک این نام‌ها را دارد. پنج کشور هنوز roster عراقی War Factory را last-win می‌کنند:

| اسلات | دکمه | واحد |
| --- | --- | --- |
| 9 | `Command_ConstructIraq_Sarab7` | `Iraq_Sarab7` |
| 13 | `Command_ConstructIraq_R11ScudB` | `Iraq_R11ScudB` (ButtonImage `irq_9p117`) |

`AlAbbas` به‌صورت `CB_MISSILE_D` → `Iraq_AlAbbas` روی `Iraq_AlFahdMissileFactoryCommandSet` است، نه روی War Factory این هفت کشور.

هند last-win roster آمریکایی است؛ پاکستان last-win roster روسی (`CommandSet_Pakistan.ini`). هیچ‌کدام از سه واحد را روی WF نداشتند؛ همان اسلات‌ها قفل شد تا merge نتواند دکمه‌ها را برگرداند.

`CommandSet.ini` مشترک ویرایش نشد. Parse مربوط به CommandSet اسلات‌ها را merge می‌کند؛ حذف اسلات کافی نیست و باید بازنویسی شود.

## اصلاح

فایل دیرتر (Last-Win):

`Data\INI\CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini`

فقط ۲۸ نام War Factory همین هفت کشور (base + 1/2/3). برای پنج کشور عراقی:

- اسلات ۹ از Sarab7 به `Command_ConstructIraq_Alhussaien` (از قبل روی اسلات ۱۰)
- اسلات ۱۳ از R11ScudB/9P117 به `Command_Sell` (از قبل روی اسلات ۱۴)
- اسلات‌های ۱–۸، ۱۰–۱۲، ۱۴ دست‌نخورده

هند و پاکستان همان roster فعلی را دوباره last-win کردند.

Object / Weapon / CommandButton / مدل / تصویر / آمار این سه واحد تغییر نکرد. MissileFactory و Abbas هر کشور دست‌نخورده ماند.

## نتیجه هر کشور

| کشور | CommandSetهای اصلاح‌شده | Sarab7 روی WF | 9P117 روی WF | AlAbbas روی WF | سایر گزینه‌های تولیدی |
| --- | --- | --- | --- | --- | --- |
| عربستان سعودی | `SaudiArabia_WarFactoryCommandSet` + 1/2/3 | حذف (اسلات ۹ بازنویسی) | حذف (اسلات ۱۳ بازنویسی) | از قبل نبود | T-72, BMP-1/2, BTR-90, 2S1, Sam8, AssadBabel-2, SA-6, Alhussaien, Roland3K, BM-21, Sell |
| امارات | `UAE_WarFactoryCommandSet` + 1/2/3 | حذف | حذف | از قبل نبود | همان roster باقی‌مانده |
| سوریه | `Syria_WarFactoryCommandSet` + 1/2/3 | حذف | حذف | از قبل نبود | همان roster باقی‌مانده |
| هند | `India_WarFactoryCommandSet` + 1/2/3 | از قبل نبود؛ قفل شد | از قبل نبود؛ قفل شد | از قبل نبود | Crusader, M1128, M1296, Sentry, Tomahawk, M109A7, Avenger, Microwave, TPY-2, THAAD, M142, M1075I/T, Sell |
| پاکستان | `Pakistan_WarFactoryCommandSet` + 1/2/3 | از قبل نبود؛ قفل شد | از قبل نبود؛ قفل شد | از قبل نبود | T-90A, T-72B3M, Bm30, Krasukha4, 2S19M2, BMP-3, Tor-M2M, Pantsir, 92N6R, S-400, TOS-1A, 9K720, RS-24, Sell |
| آفریقای جنوبی | `SouthAfrica_WarFactoryCommandSet` + 1/2/3 | حذف | حذف | از قبل نبود | همان roster باقی‌مانده عراق |
| لیبی | `Libya_WarFactoryCommandSet` + 1/2/3 | حذف | حذف | از قبل نبود | همان roster باقی‌مانده عراق |

سامانه‌های موشکی اختصاصی (`*_MissileFactoryCommandSet` و `Iraq_AlFahdMissileFactoryCommandSet`) last-win جدا دارند و در این فایل بازتعریف نشدند. `CB_MISSILE_D/E/G` روی کارخانه موشکی عراق باقی است.

## اعتبارسنجی استاتیک

Packer و یک اسکن مستقل merge روی ۲۸ CommandSet:

- هیچ اسلات mergeشده‌ای `Sarab7` / `R11ScudB` / `AlAbbas` / `9P117` / `CB_MISSILE_D|E|G` ندارد.
- Last-win هر ۲۸ نام همین فایل دیرتر است (`CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini`).
- گزینه‌های تولیدی باقی‌مانده برای هر کشور با جدول بالا یکی است.
- `Iraq_WarFactoryCommandSet_T3` همچنان `CommandSet_ZZZZ_IraqMicToWf.ini` است.
- Objectهای `Iraq_Sarab7` / `Iraq_R11ScudB` / `Iraq_AlAbbas` و دکمه‌های UNIT_BUILD آن‌ها عوض نشد.
- Supply Centre (`zzzzz_SpecterSupplyCentreBuy` + `CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini`) حفظ شد.
- DataLink رادار HT-233 / 92N6E (`zzzzz_SpecterRadarTpy2Cue` + `Weapon_ZZZZ_ZZZZTpy2RadarCue.ini`) حفظ شد.
- رادار عراق بدون Spy Sat و با `RadarUpgrade TriggeredBy` حفظ شد.

آنچه استاتیک ثابت می‌کند: دکمه‌های ساخت این سه واحد از CommandSetهای War Factory هفت کشور در آخرین DATA فعال پاک شده‌اند و بقیه گزینه‌ها و last-winهای قبلی مانده‌اند. آنچه ثابت نمی‌کند: ظاهر نوار ساخت داخل بازی.

## BIG

| فایل | حجم | SHA-256 |
| --- | --- | --- |
| `_SPEC_DATA_ONE.big` | 374 026 928 | `1b38d5c439106a83f5e54d0ba214035a14331361d63faaacaf3c7303239bd991` |

ورودی‌ها: 3572 → 3573. ART تغییر نکرد.

## نصب

1. `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big` و overlayهای `0_SPECTER_*` را نگه دارید.
2. فقط `_SPEC_DATA_ONE.big` این Release را جایگزین کنید.
3. پچ با یک فایل DATA و ترتیب بارگذاری فعلی SPECTER کامل است.

`0_SPECTER_CountrySupplyIncome.big` → `0_SPECTER_NatoSpainDisplay.big` → `INIZH.big` → `_SPEC_ART_ONE.big` → `_SPEC_ART_TWO.big` → `_SPEC_DATA_ONE.big`
