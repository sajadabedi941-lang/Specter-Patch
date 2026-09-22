You are continuing the Specter Zero Hour init-crash isolation.

This pair rewrote ONLY:
  Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI
by removing the stray leading apostrophe. ART is STRIP_02 bytes.

Read first:
- patch/Release/SPECTER1_FLAG_TURKEY_MI_PARSE_01/audit.txt
- patch/Release/SPECTER1_FLAG_TURKEY_MI_PARSE_01/SHA256.txt

Pair:
  DATA SHA256 0603b12e855f5f35cfff889362b0a02f2044968b7cdd1dd35c8c1285843f2652
  ART  SHA256 c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7
  ZIP  SHA256 655737b03076b43adb262cb2fdd928701d1593482743c6749b0e5c9b6fd4a8af

FIX_APPLIED = YES (Turkey_FactionImages parser fix)
INGAME_TESTED = NO

If the user reports this pair still crashes:
1. Do not restore flags, cloth, or extra Draws.
2. Isolate next: Specter_RemainingFlags.INI + Specter_CampFlags.INI + PlayerTemplate.ini.
3. Keep CommandButton and ART frozen unless a later isolation requires them.
4. One change group per pair. Do not claim in-game fixed.

If the user reports this pair launches:
Record INGAME_TESTED = YES and stop. Do not add cloth.
