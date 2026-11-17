# راهنمای اجرای موتور همگام‌سازی V25 → SPECTER

مرحلهٔ ۱ فقط بررسی و برنامه‌ریزی است. هیچ BIG بازی نوشته نمی‌شود.

## پیش‌نیاز

- `python3`
- `7z`
- آرشیو Silent Death V25: `V25.zip` و جلدهای `V25.z01` تا `V25.z157` (جلد `V25.z62` الزامی است). نام فایل روی GitHub ممکن است با فاصلهٔ ابتدایی باشد.
- نسخهٔ سالم SPECTER FINAL در `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/` یا مسیر معادل با `_SPEC_DATA_ONE.big` و `_SPEC_ART_TWO.big`.

## دستورها

از ریشهٔ مخزن:

```bash
python3 patch/tools/v25_sync/v25_sync.py health --json
python3 patch/tools/v25_sync/v25_sync.py extract --json
python3 patch/tools/v25_sync/v25_sync.py inventory --json
python3 patch/tools/v25_sync/v25_sync.py dry-run --json
```

`plan` و `validate` همان dry-run هستند.

بررسی یک تجهیز:

```bash
python3 patch/tools/v25_sync/dep_checker.py AmericaPatriotBattery
```

`apply` در این مرحله خطا می‌دهد و عمداً غیرفعال است.

## خروجی

گزارش‌ها در `patch/tools/v25_sync/reports/`:

- سلامت آرشیو ۱۵۸ جلدی
- سازگاری V25 و SPECTER
- Manifest و Mapping هر Object
- فهرست دسته‌ها برای انتقال گروهی بعدی (`BATCH_INDEX.json`)
- Dry Run کامل بدون تغییر BIG

## قوانین

- Object / Weapon / Armor / CommandSet عمومی SPECTER بازنویسی نمی‌شوند.
- تداخل نام → `SD25_<name>` و اصلاح تمام ارجاعات (فقط در برنامهٔ مرحلهٔ بعد).
- قابلیت بدون معادل در SPECTER حذف نمی‌شود؛ به‌صورت تعریف مستقل علامت می‌خورد.
- بستهٔ برگشت‌پذیر برای هر دسته در مرحلهٔ بعد ساخته می‌شود، نه در این مرحله.
