# راهنمای مرحلهٔ ۲ — Resolver و Transfer Plan

مرحلهٔ ۲ هنوز هیچ تجهیزی وارد SPECTER نمی‌کند. `apply` غیرفعال است.

## چه چیزی در مرحلهٔ ۱ واقعاً پیاده بود

پیاده‌سازی‌شده: سلامت آرشیو ۱۵۸ جلدی، پارسر INI تودرتو، پیمایش وابستگی، تشخیص تداخل با هش بدنه، پیشوند برنامه‌ای `SD25_` بدون بازنویسی واقعی، dry-run، فهرست دسته بدون ترتیب انتقال.

فقط در README/گزارش توصیف شده بود (و در مرحلهٔ ۲ پیاده شد): بازنویسی ارجاعات، وضعیت‌های REUSE/IMPORT/RENAME/RECOVER/INDEPENDENT/MANUAL/BLOCKED، تفاوت «نیست در extract» با «نیست در zip»، سازگاری DamageType/AntiAir از روی INI، Transfer Plan، Batch با deps مشترک، تست خودکار.

## اجرا

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py resolve --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaCSSA1 --json
python3 patch/tools/v25_sync/dep_checker.py ChinaCSSA1
```

`dry-run` همان طبقه‌بندی مرحلهٔ ۱ را نگه می‌دارد تا آمار قابل مقایسه باشد.

## خروجی

| فایل | معنا |
|---|---|
| `reports/RESOLVER_SUMMARY.md` | آماده / قابل اصلاح خودکار / دستی / مسدود |
| `reports/TRANSFER_PLAN_ChinaCSSA1.md` | زنجیرهٔ کامل نمونهٔ اصلی |
| `reports/TRANSFER_PLAN_ChinaHQ11.md` | پدافند هوایی (نمونهٔ دوم) |
| `reports/BATCH_TRANSFER_PLAN.json` | deps مشترک، ART/DATA، ترتیب، برگشت |
| `reports/DRY_RUN_DELTA.md` | اختلاف آمار مرحلهٔ ۱ و ۲ |
| `tests/test_resolver.py` | تست‌های Resolver/Rewrite |

## قوانین سازگاری

تعریف‌ها در `data/compatibility_rules.json`. سلاح جدید اگر `AntiAirborneVehicle=Yes` و DamageType روی Armor اسپکتر باشد، هواگرد/موشک SPECTER را بدون بازنویسی Armor عمومی هدف می‌گیرد. قابلیت CWC حذف نمی‌شود؛ `MANUAL_REBUILD` یا `INDEPENDENT_ADD` می‌گیرد.
