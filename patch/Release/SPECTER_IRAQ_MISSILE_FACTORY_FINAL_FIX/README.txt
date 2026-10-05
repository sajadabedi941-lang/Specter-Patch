SPECTER — Iraq Missile Factory Final Visibility Fix
Packed from live s + source commit c816e455 (packer output path this revision).

Replace in the SPECTER game folder (next to generals.exe):
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This ZIP contains exactly those two complete replacement BIGs.
Do NOT overwrite with earlier s-iraq-missile-factory or s-iraq-missile-factory-fix packs.

Visibility fix (same path as Heavy Air Base):
  Command_ConstructIraq_MissileFactory is defined once in core CommandButton.ini.
  Iraq_VT72BCommandSet slot 14 in core CommandSet.ini is Missile Factory.
  Extra CommandSet file holds only Iraq_MissileFactoryCommandSet (production).
  Iraq Worker Clear Mines is unchanged.

Static/pack/re-extract validation PASS. Not in-game runtime tested.
