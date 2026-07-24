SPECTER_BOOT_MENU_FIX
=====================

رفع کرش Technical Difficulties هنگام بوت Specter / Zero Hour

مشکل پچ CLEAN_PATCH با پوشه‌های:
  Data\INI\Weapon\
  Data\INI\CommandButton\
  Data\INI\CommandSet\

موتور Specter معمولاً فقط این‌ها را لود می‌کند:
  Data\INI\*.ini
  Data\INI\Object\**\*.ini

اگر Weapon داخل زیرپوشه باشد، بازی Weapon را پیدا نمی‌کند و کرش می‌کند.

این پچ همه فایل‌های Weapon_ / CommandButton_ / CommandSet_ را
در ریشه Data\INI می‌گذارد.

INSTALL
-------
1. بازی را کامل ببندید.
2. اگر CLEAN_PATCH قبلی را کپی کرده‌اید، پوشه‌های زیر را از GameRoot حذف کنید
   (اگر فقط از آن پچ آمده‌اند):
     Data\INI\Weapon
     Data\INI\CommandButton
     Data\INI\CommandSet
3. کپی/مرج کنید:
     Patch\Data  →  <GameRoot>\Data
     Patch\Art   →  <GameRoot>\Art
4. Data.zip و *.big و آرشیو Specter را عوض نکنید.
5. بازی را اجرا کنید.

NO installer. NO BAT. Stock Specter untouched.
