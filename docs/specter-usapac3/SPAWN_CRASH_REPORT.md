# USAPAC3 spawn crash — cause and fix

Zero Hour was not run in this environment. In-game crash after this fix is not verified here.

## In-game report (user)

USAPAC3 appears on America’s Command Center, has no prerequisite, and the build timer completes. The game crashes at the moment construction finishes (object create / spawn).

## Live Object winner

Only one `Object USAPAC3` exists. Packed path that actually loads:

`Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini`

inside `_SPEC_DATA_ONE.big`. Overlay matches packed bytes after this fix.

## Model: complete vehicle, not a Patriot display piece

| File | Role | Hierarchy | Meshes | Animation |
|---|---|---|---:|---|
| `UsaPac3Car.W3D` | travel / packed TEL | `USAPAC3CAR`, 53 bones including `CORE`, `TIRE01–08`, `TURRET01`, `TURRETEL01`, `FIREPOINT01–04` | full chassis + launcher | `USAPAC3CAR`, 101 frames |
| `UsaPac3F.W3D` | deployed / firing pose of the same TEL | same skeleton | full | `USAPAC3F`, 101 frames |
| `UsaPac3Car_d.W3D` / `UsaPac3F_d.W3D` | damaged | same | full | matching names |
| `UsaPac3Car_w.W3D` | **extra axle only** | `USAPAC3CAR_W`, bones `TIRE09`, `TIRE10` | 2 wheel meshes | header only, 0 channels |
| `pac3mis_m.W3D` | missile | `PAC3MIS_M` (`PL11BODY`, `FL001`) | 3 | `PAC3MIS_M` |

`UsaPac3Car` / `UsaPac3F` are a complete spawnable truck. `UsaPac3Car_w` is not.

## Cause

The second Draw module was:

```
Draw = W3DTruckDraw ModuleTag_TracksDraw
  ParticlesAttachedToAnimatedBones = Yes
  AttachToBoneInAnotherModule = CORE
  DefaultConditionState
    Model = UsaPac3Car_w
  End
```

That pairing does not exist on any other SPECTER object. Healthy American extra-axle modules (`America_ARRWTEL` `ModuleTag_Tires`, AbbasLauncher) are `W3DTruckDraw` with `ConditionState = NONE` and **no** `AttachToBoneInAnotherModule`.

`W3DTruckDraw` is the primary vehicle drawable. Parenting it to `CORE` of another module runs at object create — the same moment the construction timer ends.

## What was not the cause

- Cost 3876 / time 18.6 / slot 6 / CommandSet / CommandButton
- Missing W3D names (files are in `_SPEC_ART_TWO.big`)
- Missing `Generic8x8Locomotor` / `AIM-120CLocomotor` / `USAPAC3_Weapon` / `USAPAC3_Projectile`
- CreateObject / projectile (projectile is not spawned at vehicle create)
- THAAD / Patriot / NASAMS (not edited)
- Duplicate `Object USAPAC3` (only one definition)

## Fix (this object only)

Second Draw now matches `America_ARRWTEL` extra tires: `ConditionState = NONE`, model `UsaPac3Car_w`, tire bones `TIRE09` / `TIRE10`. Removed `AttachToBoneInAnotherModule` and `ParticlesAttachedToAnimatedBones`.

First Draw, Geometry, Physics, Body, Behavior, Locomotor, WeaponSet, CommandSet, cost, and time are unchanged.
