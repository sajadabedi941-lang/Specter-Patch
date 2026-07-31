AAB-ONLY TEST — USA AdvancedAirBase object (not StrategyCenter)
==============================================================

Constraints:
- CommandSet.ini NOT modified
- Factions / countries NOT modified
- Build CommandButton unchanged (still Object = America_AdvancedAirBase)
- Other faction AAB objects NOT edited

USA Object America_AdvancedAirBase:
- Draw Model = US_AirField (AdvancedAirBase mesh, all condition states)
- Scale = 1.60
- Geometry = 180 x 118 x 40 (runway footprint)
- ParkingPlaceBehavior: NumRows=2 NumCols=8 HasRunways=Yes
- Full ExtraPublicBone runway set (Runway1..8 Parking/ParkHan/Prep/Start/End + HeliPark)
- SelectPortrait/ButtonImage = us_airfield (not us_stratcenter)
- DisplayName = OBJECT:Patch_AdvancedAirBase
- KindOf = airfield factory flags (no FS_STRATEGY_CENTER)
- CommandSet = AmericaAirfieldCommandSet (stock; no new units)
