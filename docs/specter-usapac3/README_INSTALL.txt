USAPAC3 — spawn crash fix (America Command Center slot 6)
=========================================================

ساخت USAPAC3 بدون پیش‌نیاز است و دکمه در اسلات ۶ Command Center آمریکا
باقی می‌ماند. این بسته فقط crash هنگام ایجاد Object را اصلاح می‌کند.

علت: Draw دوم مدل UsaPac3Car_w (فقط دو چرخ) با
AttachToBoneInAnotherModule=CORE به W3DTruckDraw وصل شده بود. این ترکیب
در SPECTER روی هیچ خودروی سالمی نیست و در لحظهٔ Spawn کرش می‌کند.

INSTALL
-------
1. Close Generals / Specter.
2. Extract the ZIP. Keep every file next to Launch_Specter.bat.
3. Do not replace canonical _SPEC_ART_ONE.big (2,145,283,309 bytes).
4. Run Launch_Specter.bat.

ART ONE: https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

Zero Hour was not run here; the spawn crash is not verified in-game in this environment.
