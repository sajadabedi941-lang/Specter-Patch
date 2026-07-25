SPECTER - Egypt MilitaryHQ INI FIX
=================================

Crash/compatibility fix for:
  Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_MilitaryHQ.ini

(User path may appear as specter\Egypt\Egypt_MilitaryHQ.ini)

WHAT CHANGED
------------
- Full USA America_MilitaryHQ donor rebuild (US_Command art)
- ASCII-only INI (removed UTF-8 junk that breaks SAGE parser)
- Removed Iraqi leftovers (irq_comndcntr command button, Adnan module tags)
- Kept Egypt identity: Side=Egypt, Egypt_MilitaryHQCommandSet, Egypt special powers
- Kept Egypt balance: BuildCost 1615 / BuildTime 3.2, health 2400, deposit 20
- Command_ConstructEgypt_MilitaryHQ ButtonImage -> us_commandcenter
- Validated W3D US_Command, MappedImage us_commandcenter, SpecialPowers, Sciences,
  CommandSet buttons, PlayerTemplate StartingBuilding

INSTALL
-------
1. Close Specter / Generals Zero Hour
2. Backup existing _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big
3. Copy BIG files from this ZIP into your game folder
4. Launch

CHECKSUMS
---------
_SPEC_DATA_ONE.big SHA256: a00152f4efed62c64db46df35d46370d8b92d85165f735d89271b7680ed51ae7
_SPEC_ART_ONE.big  SHA256: bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
