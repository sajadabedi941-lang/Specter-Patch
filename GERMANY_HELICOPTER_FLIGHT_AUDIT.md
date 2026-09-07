# GERMANY HELICOPTER FLIGHT AUDIT

Template: ItalyHelicopterNH90 (pass 2) JetAIUpdate NeedsRunway=No + ChinookLocomotor + PhysicsBehavior.
Do not use fixed-wing runway AI.

## GermanyHelicopterNH90

- Object: `GermanyHelicopterNH90`
- AIUpdate: JetAIUpdate (converted from ChinookAIUpdate)
- Locomotor: SET_NORMAL
- Physics: PhysicsBehavior Mass=50.0
- KindOf: `PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT HARVESTER SCORE PRODUCED_AT_HELIPAD`
- NeedsRunway: No
- Parking: KeepsParkingSpaceWhenAirborne=No PRODUCED_AT_HELIPAD present
- W3D: LSFGENH90
- Animation reference count: 2
- TransportContain: YES

## GermanyHelicopterCH53

- Object: `GermanyHelicopterCH53`
- AIUpdate: JetAIUpdate (converted from ChinookAIUpdate)
- Locomotor: SET_NORMAL
- Physics: PhysicsBehavior Mass=80.0
- KindOf: `PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD`
- NeedsRunway: No
- Parking: KeepsParkingSpaceWhenAirborne=No PRODUCED_AT_HELIPAD present
- W3D: LSFRUMi171
- Animation reference count: 2
- TransportContain: YES

NH90_STATIC_FLIGHT = PASS
CH53_STATIC_FLIGHT = PASS

STATIC PASS. USER RUNTIME TEST REQUIRED. Cursor cannot launch Zero Hour.
