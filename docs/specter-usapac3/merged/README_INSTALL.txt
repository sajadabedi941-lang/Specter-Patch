USAPAC3 — spawn crash fix (America Command Center slot 6)
=========================================================

ساخت USAPAC3 بدون پیش‌نیاز است و دکمه در اسلات ۶ Command Center آمریکا
باقی می‌ماند. این بسته فقط crash هنگام ایجاد Object را اصلاح می‌کند.

علت: Draw دوم مدل UsaPac3Car_w (فقط دو چرخ) با
AttachToBoneInAnotherModule=CORE به W3DTruckDraw وصل شده بود. این ترکیب
در SPECTER روی هیچ خودروی سالمی نیست و در لحظهٔ Spawn کرش می‌کند.

INSTALL
-------
1. بازی را ببندید.
2. ZIP را در پوشهٔ بازی (کنار generals.exe) باز کنید.
3. فایل‌ها را کنار Launch_Specter.bat نگه دارید.
4. _SPEC_ART_ONE.big اصلی را عوض نکنید (2,145,283,309 بایت).
5. Launch_Specter.bat را اجرا کنید.

ART ONE:
https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

Zero Hour در این محیط اجرا نشد؛ crash داخل بازی اینجا تأیید نشده است.
