_SPECTER_USAPAC3.big — load-path fix
====================================

Zero Hour loads every *.big that sits NEXT TO generals.exe.
It does NOT load archives from the Data\ folder.

WRONG:
  ...\Zero Hour\Data\_SPECTER_USAPAC3.big

RIGHT (same folder as these files):
  generals.exe
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  EnglishZH.big
  _SPECTER_PATCH_FINAL.big     (if you already use this overlay)
  _SPECTER_USAPAC3.big         <--- this file

Launch_Specter.bat previously copied only _SPEC_DATA_ONE.big and
_SPEC_ART_ONE.big. It now also copies every _SPECTER_*.big that sits
next to the launcher into the game folder.

Do not use:  generals.exe -mod _SPECTER_USAPAC3.big
That ZH switch loads only ONE extra archive and would drop Specter.

This overlay last-wins CommandSet_FactionExpansion_Armies.ini by the
SAME internal path used by the working SPECTER patch BIG, so America
HQ slot 6 becomes USAPAC3 and NASAMS moves to empty slot 12.
