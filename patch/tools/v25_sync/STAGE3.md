# راهنمای مرحلهٔ ۳ — بازیابی ART تو‌در‌تو و رفتارهای CWC

مرحلهٔ ۳ هنوز هیچ تجهیزی وارد SPECTER نمی‌کند. `apply` غیرفعال است. هیچ BIG اصلی بازی تغییر نمی‌کند.

## چه چیزی واقعاً پیاده شد

- ایندکس ART برای فایل‌های داخل zip **و** BIGهای تو‌در‌تو مثل `WYS/Textures.big` و `WYS/W3D.big`.
- پیمایش بازگشتی W3D → DDS/TGA. مسیر، نام فایل، BIG منبع و inner path ثبت می‌شود.
- هیچ فایل مشابهی جایگزین stem گمشده نمی‌شود.
- کاتالوگ CWC: `RiderChangeContain`, `OCLSpecialPower`, `DeployStyleAIUpdate`, Pack/Unpack از طریق RIDER1/RIDER2.
- وضعیت جداگانهٔ DATA و ART: `READY_FOR_TRANSFER_PLAN` / `AUTO_RECOVERABLE` / `MANUAL_REBUILD` / `BLOCKED`.
- نمونهٔ `ChinaCSSA1` و `ChinaHQ11` فقط به‌صورت plan.

## اجرا

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py art-cwc --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaCSSA1 --json
python3 patch/tools/v25_sync/v25_sync.py apply   # باید خطا بدهد
```

## خروجی

| فایل | معنا |
|---|---|
| `reports/TRANSFER_PLAN_ChinaCSSA1.md` | زنجیرهٔ DATA+ART نمونهٔ اول |
| `reports/TRANSFER_PLAN_ChinaHQ11.md` | زنجیرهٔ DATA+ART + CWC نمونهٔ دوم |
| `reports/ART_CHAIN_*.json` | محل دقیق هر فایل ART |
| `reports/CWC_BEHAVIORS.md` | بازسازی مستقل برای SPECTER |
| `reports/STAGE3_SUMMARY.md` | وضعیت DATA/ART و تست‌شده در برابر تحلیل |

`resolve` هنوز plan همهٔ Objectها را بدون پیمایش W3D تو‌در‌تو می‌نویسد (مرحلهٔ ۲). `art-cwc` فقط دو نمونه را با ArtIndex کامل بازتولید می‌کند.
