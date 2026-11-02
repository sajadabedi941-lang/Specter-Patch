USAPAC3 ART packing — ART ONE + ART TWO
=======================================

Canonical SPECTER ART is two archives, not one:

  _SPEC_ART_ONE.big   2,145,283,309 bytes   textures (Art\Textures\, Art\Terrain\)
  _SPEC_ART_TWO.big     307,254,782 bytes   W3D models (Art\W3D\)

ART ONE has only 2,200,339 bytes left before the 2 GiB GitHub/asset cap.
The 16 USAPAC3 art files are 5,723,261 bytes, so they do not fit in ART ONE.
ART ONE is left byte-identical. All 16 files were added to ART TWO
(6 W3D + 10 textures, paths Art\W3D\ and Art\Textures\). No previous
ART TWO entries were removed.

INSTALL
-------
1. Close Generals / Specter.
2. Keep your existing canonical _SPEC_ART_ONE.big next to generals.exe
   (2,145,283,309 bytes). Do not replace it with the 524 MB repo zip.
3. Replace:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
4. Delete _SPECTER_USAPAC3.big if present.
5. Run Launch_Specter.bat — it now copies DATA, ART ONE, and ART TWO
   next to generals.exe.

ART ONE download (unchanged original):
https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big

ROLLBACK
--------
Restore the three originals:

  ART ONE  15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66
  ART TWO  a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af
  DATA     c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac
