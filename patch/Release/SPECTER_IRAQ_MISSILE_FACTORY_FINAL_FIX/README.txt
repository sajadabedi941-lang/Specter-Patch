SPECTER — Iraq Missile Factory Final Visibility Fix
Packed from live s + visibility source c816e455 (packer FINAL_FIX path).

Replace in the SPECTER game folder (next to generals.exe):
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This ZIP contains exactly those two complete replacement BIGs.
Do NOT use s-iraq-missile-factory (crash) or s-iraq-missile-factory-fix (invisible button).

Visibility fix (same path as Heavy Air Base):
  Command_ConstructIraq_MissileFactory is defined once in core CommandButton.ini.
  Iraq_VT72BCommandSet slots:
    13 = Command_ConstructIraq_HeavyAirBase
    14 = Command_ConstructIraq_MissileFactory
    15 = Command_ConstructIraq_Abbas_AI
  Extra CommandSet file holds only Iraq_MissileFactoryCommandSet (production).
  No unique-path CommandButton file. No VT72B CommandSet override.
  Iraq Worker Clear Mines is unchanged.

Hashes:
  _SPEC_DATA_ONE.big  366358083  SHA256=0a80c803f76b3260ec045824358dcb9b8446f61d2996ff0f143a7ecdff65843b
  _SPEC_ART_ONE.big  1258740451  SHA256=67c0c15524a3d6b6dbd36664b64df88ada6bc007aa19759709c87c7069e20a9d
  SPECTER_IRAQ_MISSILE_FACTORY_FINAL_FIX.zip  1625098778  SHA256=d3db434574c0b289c07c619c5d6074a68c1e53fda5b6349151b690f331d18565

Re-extract: DATA 2911 files, ART 4597 files.
ART SHA matches the previous crash-fix ART pack (same 17 donor assets; Irq_WarFactory unchanged).
Static/pack/re-extract validation PASS. Not in-game runtime tested.
