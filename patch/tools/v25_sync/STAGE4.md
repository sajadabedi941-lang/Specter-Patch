# راهنمای مرحلهٔ ۴ — بازسازی مستقل DATA برای دو نمونه

مرحلهٔ ۴ هنوز هیچ تجهیزی وارد SPECTER نمی‌کند. `apply` غیرفعال است. هیچ BIG اصلی بازی تغییر نمی‌کند. هیچ فایل Loose عمومی اضافه نمی‌شود.

## چه چیزی واقعاً پیاده شد

- `DamageFX` و `CrateData` به‌عنوان kind مستقل parse می‌شوند (`TankDamageFX` دیگر FXList نیست).
- `TankDamageFX` / `TruckDamageFX` روی مسیر یکتا `Data\INI\DamageFX_SilentDeath.ini` به‌صورت `SD25_*` کلون می‌شوند. `DamageFX.ini` عمومی SPECTER دست نمی‌خورد.
- `SalvageCrateData` روی مسیر یکتا `Data\INI\Crate_SilentDeath.ini` کلون می‌شود. `Crate.ini` عمومی دست نمی‌خورد.
- `ChinaHQ11`: `RiderChangeContain` + `OCLSpecialPower` فقط وقتی با الگوی packed/deployed و OCL فقط-سوارکاذب اثبات شود با `DeployStyleAIUpdate` و `WeaponSet Conditions = DEPLOYED` جایگزین می‌شود.
- محدودیت‌های اثبات‌نشده صریح هستند: تعویض CommandSet در runtime، SET_SLUGGISH هنگام استقرار، دو تصویر دکمهٔ جدا، زمان دقیق pack CWC.
- CWC.exe و SpecialPower از نوع `SPECIAL_CIA_INTELLIGENCE` وارد نمی‌شوند.

## اجرا

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py data-rebuild --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaCSSA1 --json
python3 patch/tools/v25_sync/v25_sync.py apply   # باید خطا بدهد
```

## خروجی

| فایل | معنا |
|---|---|
| `reports/TRANSFER_PLAN_ChinaCSSA1.md` | DATA+ART+کلون‌های مستقل |
| `reports/TRANSFER_PLAN_ChinaHQ11.md` | DATA+ART+اثبات DeployStyle |
| `reports/DATA_REBUILD_*.json` | مسیرهای یکتا، کلون‌ها، محدودیت‌ها |
| `reports/STAGE4_SUMMARY.md` | وضعیت DATA/ART و تست‌شده در برابر تحلیل |

Generals.exe در این مرحله اجرا نشده است.
