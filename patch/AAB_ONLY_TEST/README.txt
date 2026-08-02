AAB-ONLY — USA AdvancedAirBase uses Revolution Project USA Airfield visuals
==========================================================================

Visual source (imported from Revolution 3.0 installer art BIGs):
  Draw / Geometry / Models / Textures / Runway = Alliance AmericaAirfield (ABAirF2)
  Models: Art/W3D/ABAirF2*.W3D + ABAirF_T2.W3D + door/FX W3Ds
  Textures: Art/Textures/ABAirF*.dds (+ supporting Revolution textures)
  Geometry: 156 x 83 x 100
  ParkingPlace: NumRows=3 NumCols=2 HasRunways=Yes
  UI portraits: SANAirF / SANAirF_L (atlas under Data/English/Art/Textures)

Unchanged:
  CommandSet.ini (not present in this overlay; stock untouched)
  Build CommandButton Object = America_AdvancedAirBase
  Prerequisites / BuildCost / BuildTime / AmericaAirfieldCommandSet
  Non-USA faction AAB objects (not retargeted for this USA-only test)

Install:
  Merge Data/ into _SPEC_DATA_ONE.big and place Art/ as loose files (or merge into ART BIG)
  so the game loads ABAirF2 meshes + textures when America_AdvancedAirBase is built.
