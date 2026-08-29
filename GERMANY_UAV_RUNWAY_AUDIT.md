# GERMANY UAV RUNWAY AUDIT

Template: ItalyDroneMQ9 runway UAV (NeedsRunway=Yes, KeepsParkingSpaceWhenAirborne=Yes).
Not converted to helicopters.

## GermanyUAVEuroMALE

- takeoff architecture: JetAIUpdate NeedsRunway=Yes TakeoffPause present
- landing architecture: NeedsRunway=Yes + ReturnToBaseIdleTime + taxi locomotor
- NeedsRunway: Yes
- KeepsParkingSpaceWhenAirborne: Yes
- AIUpdate: JetAIUpdate
- Locomotor: SET_NORMAL
- Physics: Mass=90.0
- airbase compatibility: Germany Heavy Airbase slots unchanged
- return-to-base: ReturnToBaseIdleTime=10000
- parking: KeepsParkingSpaceWhenAirborne=Yes
- W3D: Nat_Heron

## GermanyDroneHeronTP

- takeoff architecture: JetAIUpdate NeedsRunway=Yes TakeoffPause present
- landing architecture: NeedsRunway=Yes + ReturnToBaseIdleTime + taxi locomotor
- NeedsRunway: Yes
- KeepsParkingSpaceWhenAirborne: Yes
- AIUpdate: JetAIUpdate
- Locomotor: SET_NORMAL
- Physics: Mass=80.0
- airbase compatibility: Germany Heavy Airbase slots unchanged
- return-to-base: ReturnToBaseIdleTime=10000
- parking: KeepsParkingSpaceWhenAirborne=Yes
- W3D: AVReaper

EURODRONE_TAKEOFF_STATIC = PASS
EURODRONE_LANDING_STATIC = PASS
HERON_TP_TAKEOFF_STATIC = PASS
HERON_TP_LANDING_STATIC = PASS

STATIC PASS. USER RUNTIME TEST REQUIRED.
