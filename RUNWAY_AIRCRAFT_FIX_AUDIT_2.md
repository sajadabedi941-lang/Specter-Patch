# Runway Aircraft Fix Audit 2

Cursor cannot run Zero Hour. STATIC checks only. USER RUNTIME TEST REQUIRED for takeoff/landing/return.

## SouthAfricaJetIL76
- AIUpdate: JetAIUpdate
- Locomotor: D30-F6_JetLocomotor + BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- NeedsRunway: Yes
- airbase compatibility: SouthAfrica_HeavyAirBaseCommandSet slot 4
- landing behavior: ReturnToBaseIdleTime present=True
- return behavior: ReturnToBaseIdleTime
- parking: KeepsParkingSpaceWhenAirborne
- W3D: Iraq_IL-76
- Animation refs: none (0-anim W3D)
- TransportContain: 32 slots
- Science object SouthAfrica_IL-76 left intact with DeliverPayloadAIUpdate

## LibyaJetIL76
- AIUpdate: JetAIUpdate
- Locomotor: D30-F6_JetLocomotor + BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- NeedsRunway: Yes
- airbase compatibility: Libya_HeavyAirBaseCommandSet slot 3
- landing behavior: ReturnToBaseIdleTime present=True
- return behavior: ReturnToBaseIdleTime
- parking: KeepsParkingSpaceWhenAirborne
- W3D: Iraq_IL-76
- Animation refs: none (0-anim W3D)
- TransportContain: 32 slots
- Science object Libya_IL-76 left intact with DeliverPayloadAIUpdate

## ItalyDroneMQ9
- AIUpdate: JetAIUpdate
- Locomotor: Snecma_M88_4E + BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- NeedsRunway: Yes (was No)
- airbase compatibility: Italy_HeavyAirBaseCommandSet slot 4
- landing behavior: ReturnToBaseIdleTime present=True
- return behavior: ReturnToBaseIdleTime
- parking: KeepsParkingSpaceWhenAirborne=Yes
- W3D: AVReaper
- Animation refs: none
- Identity: MQ-9 UAV, not converted to helicopter

## FranceUCAVNeuron
- AIUpdate: JetAIUpdate
- Locomotor: Snecma_M88_4E + BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- NeedsRunway: Yes (was No)
- airbase compatibility: France_HeavyAirBaseCommandSet slot 3
- landing behavior: ReturnToBaseIdleTime present=True
- return behavior: ReturnToBaseIdleTime
- parking: KeepsParkingSpaceWhenAirborne=Yes
- W3D: AV_RQ180 (was CHI_GJ11L)
- Animation refs: none (0-anim W3D)
- Loadout unchanged: France_Weapon_Neuron_AASM ClipSize 2 (GBU24_GuidedBombObject)
