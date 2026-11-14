# America Patriot PAC-3 — mobile V25 truck, SS2 THAAD fire

## Vehicle (not a building)

V25 `AmericaPATRIO`: `W3DTruckDraw`, 8 wheels, cab/trailer, turret, `AIUpdateInterface`, **no deploy**.
SS2 has no `USPAC3` W3D. Live `USAPAC3` proves `UsaPac3Car` has `TIRE01`–`TIRE08` and can take `TrackMarks`/`Dust`.
This unit uses that truck Draw **without** `DeployStyleAIUpdate` / PACKING / DEPLOYED. Fire while stopped via `AIUpdateInterface` (same pattern as live Avenger).
Locomotor: live `Generic8x8Locomotor` (`Appearance = FOUR_WHEELS`, `HasSuspension = Yes`) — same family as the THAAD M1120 truck.

`US_MIM104F_L` is a static launcher (no tire bones). It is not used here.

## THAAD fire (unique clones; `US_THAAD` not edited)

| Role | Live | Clone |
|---|---|---|
| AA | `8x_LRSAM_THAAD` PENALTY | `AmericaPatriotPAC3_AA` |
| ABM + cruise | THAAD ABM stats + CRUSH fuze | `AmericaPatriotPAC3_ABM` / `_Fuze` |

AirplaneArmor: PENALTY. BallisticMissileArmor / CruiseMissileArmor: CRUSH.

## Wiring

America CC slot 10. Slot 1 dozer and slot 6 `USAPAC3` kept. Turkey, GLA, Iran factory, THAAD unchanged.
