# Crash vs mobility

#787 crashed at America match start: `W3DTruckDraw`+`TrackMarks` on `US_MIM104F_L` (no tire bones) and `FS_BASE_DEFENSE` on a CC vehicle.

#788 avoided that by switching to `W3DModelDraw` on the static launcher. That removed the crash fields but also removed the truck chassis.

This pack keeps the crash fix **and** restores a wheeled vehicle:

- Draw = live `UsaPac3Car` `W3DTruckDraw` with the same `TIRE01`–`TIRE08` map as working `USAPAC3`
- TrackMarks/Dust only because those bones exist
- No CabBone/TrailerBone (V25 names; this model does not declare them)
- No `FS_BASE_DEFENSE`
- `AIUpdateInterface` only — no `DeployStyleAIUpdate`

In-game play was not run here.
