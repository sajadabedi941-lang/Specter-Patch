SPECTER — Iraq Missile Factory Crash Fix
Packed from live s + source fix commit c9443497 (packer output path 435332fa).

Replace in the SPECTER game folder (next to generals.exe):
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This ZIP contains exactly those two complete replacement BIGs.
Do NOT use the earlier s-iraq-missile-factory ZIP (that pack crashed on Iraq_VT72BCommandSet).

Crash fix: CommandSet.ini is byte-identical to s. Missile Factory is last-won
onto Iraq_VT72BCommandSet slot 14 from CommandSet_Iraq_MissileFactory.ini.
Iraq Worker Clear Mines is unchanged.

Static/pack/re-extract validation PASS. Not in-game runtime tested.
