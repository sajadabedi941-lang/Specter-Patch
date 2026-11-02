USAPAC3 is now inside the main SPECTER BIGs.
Do NOT install _SPECTER_USAPAC3.big.

INSTALL
-------
1. Close Generals / Specter.
2. Back up your current files (same folder as generals.exe):
     _SPEC_DATA_ONE.big
     _SPEC_ART_ONE.big
3. Replace them with the merged files from this release:
     _SPEC_DATA_ONE.big
     _SPEC_ART_ONE.big
4. Delete _SPECTER_USAPAC3.big if it is still in the game folder.
5. If _SPECTER_PATCH_FINAL.big is also in that folder, it last-wins
   Data\INI\CommandSet_FactionExpansion_Armies.ini and can hide slot 6.
   Remove that overlay BIG or replace it with one rebuilt from this PR.
6. Run Launch_Specter.bat (it copies _SPEC_DATA_ONE.big and
   _SPEC_ART_ONE.big next to generals.exe).

ROLLBACK
--------
Restore the backed-up _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big.
Original stock hashes (before this merge):

  DATA  c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05
  ART   bb5d15325e227bad247450dc379bbf85b8bbd620beacc9b2f8db89976b1989d7
