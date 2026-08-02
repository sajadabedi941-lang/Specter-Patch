SPECTER — Advanced Air Base INFRASTRUCTURE (all factions)
=========================================================
Patch layer only. No aircraft INI changes. No B-2/B-52/AWACS.

What this provides
------------------
- Separate *_AdvancedAirBase object per faction (30)
- Faction art/models when available (USA ABAirF2 Revolution,
  Russia RUS_Airfield, China/NK Chi_Airfield, Iran iran_airfield,
  Israel Isr_Airfield, GLA Arb_Airfield, ME/Asia Irq_Airfield,
  NATO/Europe US_AirField)
- Large runway support (HasRunways=Yes + full runway bone set)
- Repair/refuel (HealAmountPerSecond)
- Increased aircraft capacity (16 pads / USA Revolution 6 pads)
- Heavy-aircraft-ready geometry and parking layout
- Production CommandSets are Rally+Sell stubs (infra only)
  OR existing stock airfield CommandSets (no new heavies)

Build wiring
------------
- Unique *_PatchAAB dozer/worker CommandSets (does not edit CommandSet.ini)
- USA: stock SC construct buttons retargeted to America_AdvancedAirBase
  inside packed CommandButton.ini (surgical Object= patch)

Install
-------
Replace game _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big with release copies.
