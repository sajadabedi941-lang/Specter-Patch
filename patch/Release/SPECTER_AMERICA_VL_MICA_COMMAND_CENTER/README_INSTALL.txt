SPECTER America VL MICA — Command Center
=======================================

Adds an independent America VL MICA (New Donor LSFziyuan launcher) to the
main America Command Center. Vietnam files are not modified.
Patriot / USAPAC3 / AirF / Laser / Superweapon Command Centers are not modified.

Live chain (packed DATA)
------------------------
PlayerTemplate FactionAmerica
  StartingBuilding = AmericaCommandCenter
Object AmericaCommandCenter
  CommandSet = AmericaCommandCenterCommandSet
Packed Data\INI\CommandSet.ini  (this is the live CC set; overlay CommandSet.ini
  does not contain USAPAC3 and is not the file the game shows)
  1  Dozer
  2  VL MICA          <-- added, previously empty
  6  USAPAC3          unchanged
 12  UH60             unchanged
 13  M2A3             unchanged
 14  Sell             unchanged
Packed Data\INI\CommandButton.ini
  Command_ConstructAmerica_VL_MICA  UNIT_BUILD  Object=America_VL_MICA
  (same file as the working Command_ConstructUSAPAC3)

Install
-------
1. Extract into SPECTER FINAL (folder with generals.exe).
2. Replace:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
   ART TWO carries LSFziyuan / VlmicaTB / CWCruS300_m from the VL MICA art pack.
3. Do not drop a loose CommandSet.ini or CommandButton.ini over these BIGs.

Use
---
America Command Center slot 2 -> VL MICA. Deploy before it fires.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
