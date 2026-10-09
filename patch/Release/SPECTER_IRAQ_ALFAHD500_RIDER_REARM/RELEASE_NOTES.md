# Iraq_AlFahd500 unique Alabaas rider rearm

From PR #599. Missile A only. Incorporates the leftover unique CommandSet
(`Iraq_AlFahd500CommandSet`) because the rearm button must live on this TEL
without editing `Scud_B_CommandSet`.

## Rider chain

1. Spawn: `Conditions=None` + `Weapon_Iraq_AlFahd500`. No `InitialPayload`.
2. Fire: `FireOCL = OCL_Disarm_Iraq_AlFahd500` contains `Iraq_AlFahd500_RiderUnarmed`
   -> `WEAPON_RIDER1` (no PRIMARY) + `Iraq_AlFahd500_UnarmedRearmSet`.
3. Pay: `Command_Rearm_Iraq_AlFahd500` OBJECT_UPGRADE `Upgrade_Rearm_Iraq_AlFahd500` $1100.
4. Restore: `ObjectCreationUpgrade` -> `OCL_Rearm_Iraq_AlFahd500` contains
   `RearmStrip_Iraq_AlFahd500` + `Iraq_AlFahd500_RiderArmed` -> `WEAPON_RIDER2`.
5. Stripper `UpgradeDie` clears the object upgrade so the next cycle can pay again.

## Spawn-crash fix vs #594/#595

- #594/#595 used `InitialPayload GenericFakeRider2` (height 1e7) and
  `Weapon = PRIMARY NONE`. Alabaas unarmed sets have **no PRIMARY**.
- This build omits `InitialPayload`, keeps `Conditions=None` for the first shot,
  uses unique small-geometry riders, and unique OCLs.
- Leftover `#597` `OCL_Rearm_Iraq_AlFahd500` only spawned a non-contained stripper;
  it is replaced so $1100 actually restores the armed rider.

Static checks are not runtime safety. Game session was not completed in this environment.
Do not proceed to missile B.
