SPECTER Unified Install
=======================

This pack is the current compatible DATA/INI/overlay set plus original
Full Release _SPEC_ART_TWO.big. It is NOT a stack of old DATA BIGs.

It is NOT a standalone complete install: GitHub's 2 GiB asset limit
cannot hold original _SPEC_ART_ONE.big and _SPEC_ART_TWO.big in one ZIP.
See ART_ONE_REQUIRED.txt.

Zero Hour was not run in the build environment. Static checks are not
in-game proof.

What is in this ZIP
-------------------
_SPEC_DATA_ONE.big
  Final DATA (from missile-jlmn-buttons / PR #722). Carries:
  - War Factory strip of RS-24 / DF-41 / Khorramshahr on live RU/CN/IR factories (#718)
  - Spy Satellite removed from live country radar CommandSets (#719)
  - JP/VN/SK Command Center = VT72B only; NK = VT72B + Hwasong15BB (#720)
  - Air Defence MaxSimultaneousOfType=3
  - Shahed-136 radar-launcher range 3000
  - Missile factory K/L/M/N objects and Iran Fire CommandSets
  - J/L/M/N ButtonImage mapping (Neon / Futuristic / Nuclear / pla_df41)

_SPEC_ART_TWO.big
  Original Full Release ART TWO. Not rebuilt.

CommandSet.ini / CommandButton.ini
  Same bytes as inside DATA. Must be loose at Data\INI\
  (ControlBar first-wins these paths over archives).

0_SPECTER_GlobalStoreCameos.big
  PR #721 original Global Store / MIC shop TGA. Keep the 0_ prefix.

0_SPECTER_MissileJLMNCameos.big
  PR #722 specter_missile_j/l/m TGA. Keep the 0_ prefix.

What you must add
-----------------
_SPEC_ART_ONE.big  (original Full Release, 2145283309 bytes)
  SHA-256 15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66
  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big
  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/WORLD_WAR_III2027-Full-Release/_SPEC_ART_ONE.big

If that file is already next to generals.exe and the size matches, the
installer keeps it. Do not replace it with a 447 MB ART.

Install (one shot)
------------------
1. Close Zero Hour.
2. Unzip SPECTER_UNIFIED_INSTALL.zip.
3. Download _SPEC_ART_ONE.big from the links above into the unzipped
   folder or into the game folder (next to generals.exe), unless it is
   already there with the canonical size.
4. Copy the unzipped folder into the game directory or a folder beside it.
5. Run Install_SpecterUnified.bat.
6. Confirm it found generals.exe, copied DATA/INI/overlays, and either
   installed or preserved canonical ART ONE and ART TWO.

Load order
----------
game.dat lists *.big with case-insensitive sort; first archive that owns
a path wins. Names starting 0_ sort before _SPEC_ART_ONE.big, so the two
overlay BIGs first-win their Art\Textures TGA without replacing ART.

Manual install
--------------
Place next to generals.exe:
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big          (canonical Full Release only)
  _SPEC_ART_TWO.big          (from this ZIP)
  0_SPECTER_GlobalStoreCameos.big
  0_SPECTER_MissileJLMNCameos.big

Place in Data\INI\:
  CommandSet.ini
  CommandButton.ini

Do not rename the 0_ overlays. Do not install older CommandSet.ini or
CommandButton.ini from #710-#721 after this pack.

Backup / restore
----------------
The installer copies replaced DATA/INI/overlay files into
  Backup_SPECTER_UNIFIED_<date>_<time>\
inside the game folder. Canonical ART is preserved in place. ART is
backed up only when the installer has to replace a non-canonical file.
Run Restore_SpecterUnifiedBackup.bat from that backup folder to undo.

Do not install
--------------
- Older _SPEC_DATA_ONE.big from #718-#721
- Truncated ART (construct-button 447 MB, repo split zip, s-art-split-2gib)
- Loose PNG/DDS
- Extra CommandSet_*.ini or 0_ overlays other than the two named above

SHA-256
-------
See SHA256SUMS.txt and ZIP_MANIFEST.txt next to these files.
