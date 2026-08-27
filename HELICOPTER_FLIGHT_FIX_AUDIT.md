# Helicopter Flight Fix Audit

Cursor cannot run Zero Hour. These are STATIC INI checks only. USER RUNTIME TEST REQUIRED for lift-off/fly/return/land.

| Object | AIUpdate | Locomotor | Physics | parking method | runway requirement | W3D | status |
|---|---|---|---|---|---|---|---|
| ItalyHelicopterNH90 | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | LSFGENH90 | PASS |
| ItalyHelicopterAW101 | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | LSFGENH90 | PASS |
| ItalyHelicopterAW139 | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | LSFRUMi171 | PASS |
| FranceHelicopterNH90 | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | LSFFRNH90 | PASS |
| SouthAfrica_Mi-8T | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | Irq_MI8T | PASS |
| Libya_Mi-8T | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | Irq_MI8T | PASS |
| SouthAfricaHelicopterRooivalk | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | LSFFRTiger | PASS |
| SouthAfricaHelicopterOryx | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | NAT_Puma | PASS |
| LibyaHelicopterMi24 | JetAIUpdate | ChinookLocomotor | PhysicsBehavior | helipad/no-runway | No | Iraq_Mi-35M3 | PASS |

HELICOPTER_FLIGHT_STATIC_CHECK = PASS

Notes:
- Template: VietnamJetMi8 / SouthKoreaJetAH64E (JetAIUpdate, NeedsRunway=No, ChinookLocomotor, PhysicsBehavior). HelicopterAIUpdate does not exist in this patch.
- NAT_Puma has 0 animation chunks; Oryx has no Animation= line.
- LSFFRTiger / Iraq_Mi-35M3 / LSFGENH90 / LSFFRNH90 have animation chunks and keep Animation=.
- Rooivalk displayed identity is Rooivalk (CSF), not Apache/Tiger.
- Oryx displayed identity is Oryx (Puma-family visual stand-in).
