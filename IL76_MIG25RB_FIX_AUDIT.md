# IL-76 / MiG-25RB Runway Fix Audit
Cursor cannot run Zero Hour. These are STATIC checks only.

## VietnamJetIL76
- Object: VietnamJetIL76
- Locomotor: D30-F6_JetLocomotor, BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- AIUpdate: JetAIUpdate
- NeedsRunway: Yes
- KindOf: PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
- takeoff path: JetAIUpdate NeedsRunway + taxi locomotor
- landing path: ReturnToBaseIdleTime + KeepsParkingSpaceWhenAirborne
- return behavior: ReturnToBaseIdleTime = 10000
- transport behavior: TransportContain
- weapon: none
- W3D: Iraq_IL-76
- Animation refs: none

## IraqJetIL76
- Object: IraqJetIL76
- Locomotor: D30-F6_JetLocomotor, BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- AIUpdate: JetAIUpdate
- NeedsRunway: Yes
- KindOf: PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
- takeoff path: JetAIUpdate NeedsRunway + taxi locomotor
- landing path: ReturnToBaseIdleTime + KeepsParkingSpaceWhenAirborne
- return behavior: ReturnToBaseIdleTime = 10000
- transport behavior: TransportContain
- weapon: none
- W3D: Iraq_IL-76
- Animation refs: none

## IraqJetMig25RB
- Object: IraqJetMig25RB
- Locomotor: R15BF2-300JetLocomotor, BasicJetTaxiLocomotor
- Physics: PhysicsBehavior
- AIUpdate: JetAIUpdate
- NeedsRunway: Yes
- KindOf: PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
- takeoff path: JetAIUpdate NeedsRunway + taxi locomotor
- landing path: ReturnToBaseIdleTime + KeepsParkingSpaceWhenAirborne
- return behavior: ReturnToBaseIdleTime = 10000
- transport behavior: n/a
- weapon: IraqJetMig25RB_WpnLT3, IraqJetMig25RB_WpnGun, IraqJetMig25RB_WpnGun
- W3D: Iraq_Mig-25bm
- Animation refs: none

IL76_STATIC_RUNWAY_CHECK = PASS
MIG25RB_STATIC_RUNWAY_CHECK = PASS
