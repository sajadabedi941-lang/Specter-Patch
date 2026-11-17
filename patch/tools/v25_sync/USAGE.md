# راهنمای اجرا — مرحلهٔ ۵

بستهٔ آزمایشی مستقل برای `ChinaCSSA1` و `ChinaHQ11`. نسخهٔ اصلی SPECTER FINAL دست‌نخورده می‌ماند.

## پیش‌نیاز

`python3`، `7z`، آرشیو ۱۵۸ جلدی V25 (با `z62`)، SPECTER FINAL در `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/`.

## دستورها

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py ready-pack --out /tmp/v25_ready_pack --json
python3 patch/tools/v25_sync/v25_sync.py pack-sample --out /tmp/v25_stage5_pack --json
python3 patch/tools/v25_sync/v25_sync.py apply   # باید خطا بدهد
```

خروجی فقط زیر `--out` نوشته می‌شود. هیچ INI لوس و هیچ تغییر روی BIGهای نصب اصلی ایجاد نمی‌شود.

محل ساخت در SPECTER (استخراج‌شده، نه حدس):

- ساختمان: `ChinaWarFactory` → `PLAWarFactoryCommandSet`
- `SD25_ChinaCSSA1`: UNIT_BUILD اسلات **۴**
- `SD25_ChinaHQ11`: UNIT_BUILD اسلات **۷**
