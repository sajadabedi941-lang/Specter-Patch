SPECTER America VL MICA -- Command Center button KindOf fix
==========================================================

Fixes the missing America Command Center VL MICA button.

Cause: Object America_VL_MICA KindOf included FS_BASE_DEFENSE and POWERED.
Those flags are not on the working USAPAC3 UNIT_BUILD in the same CommandSet.
They are now removed. All other KindOf flags and the New Donor structure
(Draw, Geometry, riders, pack/unpack, locos) are unchanged. THAAD fire
and CommandSet/CommandButton slots are unchanged.

Install
-------
Extract into SPECTER FINAL (the folder that contains generals.exe). Replace:
  _SPEC_DATA_ONE.big
  _SPEC_ART_TWO.big

Do not drop a loose CommandSet.ini or CommandButton.ini over these BIGs.

America Command Center:
  slot 2 = Command_ConstructAmerica_VL_MICA
  slot 6 = Command_ConstructUSAPAC3  (unchanged)

Generals.exe was not run on the pack machine.
