SPECTER Unified Install
=======================

This pack is the current compatible DATA/INI/overlay set. It is NOT a stack of
old _SPEC_DATA_ONE.big files. It does not replace _SPEC_ART_ONE.big or
_SPEC_ART_TWO.big.

Zero Hour was not run in the build environment. Static checks are not in-game proof.

What is included
----------------
_SPEC_DATA_ONE.big
  Final DATA (from missile-jlmn-buttons / PR #722). Carries:
  - War Factory strip of RS-24 / DF-41 / Khorramshahr on live RU/CN/IR factories (#718)
  - Spy Satellite removed from live country radar CommandSets (#719)
  - JP/VN/SK Command Center = VT72B only; NK = VT72B + Hwasong15BB (#720)
  - Air Defence MaxSimultaneousOfType=3
  - Shahed-136 radar-launcher range 3000
  - Missile factory K/L/M/N objects and Iran Fire CommandSets
  - J/L/M/N ButtonImage mapping (Neon / Futuristic / Nuclear / pla_df41)

CommandSet.ini
  Same bytes as inside DATA. Must be loose at Data\INI\CommandSet.ini
  (ControlBar first-wins this path over archives).

CommandButton.ini
  Same bytes as inside DATA. Must be loose at Data\INI\CommandButton.ini.

0_SPECTER_GlobalStoreCameos.big
  PR #721 original Global Store / MIC shop TGA. Keep the 0_ prefix.

0_SPECTER_MissileJLMNCameos.big
  PR #722 specter_missile_j/l/m TGA. Keep the 0_ prefix.

Install (one shot)
------------------
1. Close Zero Hour.
2. Unzip SPECTER_UNIFIED_INSTALL.zip.
3. Copy the unzipped folder into the game directory (next to generals.exe)
   or into a folder beside it.
4. Run Install_SpecterUnified.bat.
5. Confirm it found generals.exe and copied five files.
6. Keep your existing _SPEC_ART_ONE.big and _SPEC_ART_TWO.big.

Manual install
--------------
Place next to generals.exe:
  _SPEC_DATA_ONE.big
  0_SPECTER_GlobalStoreCameos.big
  0_SPECTER_MissileJLMNCameos.big

Place in Data\INI\:
  CommandSet.ini
  CommandButton.ini

Do not rename the 0_ overlays. Do not install older CommandSet.ini or
CommandButton.ini from #710-#721 after this pack.

Backup / restore
----------------
The installer copies any replaced files into
  Backup_SPECTER_UNIFIED_<date>_<time>\
inside the game folder. Run Restore_SpecterUnifiedBackup.bat from that
backup folder to put those files back. ART ONE/TWO are never copied.

Do not install
--------------
- Older _SPEC_DATA_ONE.big from #718-#721
- Full-release ART substitutes
- Loose PNG/DDS
- Extra CommandSet_*.ini or 0_ overlays other than the two named above

SHA-256
-------
See SHA256SUMS.txt next to these files.
