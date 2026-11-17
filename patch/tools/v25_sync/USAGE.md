# راهنمای اجرا — مرحلهٔ ۲

مرحلهٔ ۲ Transfer Plan می‌سازد. هیچ BIG بازی نوشته نمی‌شود.

## پیش‌نیاز

همان مرحلهٔ ۱: `python3`، `7z`، آرشیو ۱۵۸ جلدی V25 (با `z62`)، SPECTER FINAL در `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/`.

## دستورها

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py resolve --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaCSSA1 --json
python3 patch/tools/v25_sync/dep_checker.py ChinaCSSA1
python3 patch/tools/v25_sync/v25_sync.py apply   # باید خطا بدهد
```

`dry-run` همان اسکن مرحلهٔ ۱ است (هش بدنه). `resolve` طبقه‌بندی مؤثر + بازیابی از zip را اضافه می‌کند.

## وضعیت Resolver

| وضعیت | معنی |
|---|---|
| REUSE_NATIVE | تعریف SPECTER سازگار است |
| IMPORT_UNIQUE | نام آزاد است؛ مسیر یکتا |
| RENAME_AND_REWRITE | تداخل؛ `SD25_` و اصلاح ارجاع |
| RECOVER_FROM_V25 | در extract/VFS نیست، در zip هست |
| INDEPENDENT_ADD | قابلیت بدون معادل؛ تعریف مستقل |
| MANUAL_REBUILD | نیاز به بازسازی دستی (مثلاً CWC) |
| BLOCKED | PlayerTemplate / ژنرال ZH |

`ready_transfer` با تعداد Object یکتا یکی گرفته نمی‌شود.
