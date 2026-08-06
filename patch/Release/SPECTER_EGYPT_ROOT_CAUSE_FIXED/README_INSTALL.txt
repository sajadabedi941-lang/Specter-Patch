SPECTER EGYPT ROOT CAUSE FIXED
==============================

File: _SPEC_DATA_ONE.big
SHA256: 6152f44c6ed0358e8a3a9eb8c377529300363ccacbaf1f3e8912078190fd3289
Egypt_CommandCenter SHA256: 81dd3fcd672bf68d3d7a965e1d8b30195301b7ac198582fc8d28bbc5d963e00c
Validation: PASS

ROOT CAUSE
----------
Vendor _SPEC_DATA_ONE.big contains broken Egypt_CommandCenter.ini
(sha 1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61):
  L25-26 SelectPortrait/ButtonImage = irq_comndcntr
  L35    Model = Irq_Command
  L146   GunshipTemplateName = Iraq_Adnan1
  L128/153/159-161/172 SUPERWEAPON_Iraqi* / SUPERWEAPON_IraqReconnaissance

Overlays do not help if the broken SPEC Data BIG is what you still run.
You must REPLACE _SPEC_DATA_ONE.big.

INSTALL
-------
1. Backup Data\_SPEC_DATA_ONE.big
2. Copy this package's _SPEC_DATA_ONE.big over Data\_SPEC_DATA_ONE.big
3. Keep Data\_SPEC_ART_ONE.big
4. Delete ALL other Specter Data BIGs (_SPECTER_*.big, old FIXED/CLEAN overlays)

Egypt faction is kept. Object name remains Egypt_CommandCenter.
