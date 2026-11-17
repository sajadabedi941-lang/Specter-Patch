# راهنمای اجرا — مرحلهٔ ۴

مرحلهٔ ۴ DATA دو نمونه را مستقل بازسازی می‌کند. هیچ BIG بازی نوشته نمی‌شود.

## پیش‌نیاز

همان مرحلهٔ ۱: `python3`، `7z`، آرشیو ۱۵۸ جلدی V25 (با `z62`)، SPECTER FINAL در `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/`.

## دستورها

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py data-rebuild --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaHQ11 --json
python3 patch/tools/v25_sync/v25_sync.py apply   # باید خطا بدهد
```

## وضعیت کامل بودن (جدا برای DATA و ART)

| وضعیت | معنی |
|---|---|
| READY_FOR_TRANSFER_PLAN | زنجیره بدون شکاف سخت؛ هنوز وارد بازی نشده |
| AUTO_RECOVERABLE | فایل در zip یا BIG تو‌در‌تو با stem دقیق پیدا شد |
| MANUAL_REBUILD | stem گمشده، یا CWC که الگوی استقرارش اثبات نشده |
| BLOCKED | جدول عمومی / ژنرال ZH |

`DeployStyleAIUpdate` فقط پس از اثبات سازگاری packed/deployed استفاده می‌شود. محدودیت‌ها در Transfer Plan نوشته می‌شوند.
