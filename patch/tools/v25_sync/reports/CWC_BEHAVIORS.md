# CWC behaviors discovered in V25 (SPECTER-safe rebuild)

- Generated: 2026-11-11 13:30 Asia/Tehran

SPECTER runs stock Generals.exe. CWC.exe-only modules are never copied as-is.
Capabilities are kept via independent unique-path INI, not by rewriting SPECTER core.

## `RiderChangeContain`

- Origin: CWC.exe (not stock ZH)
- SPECTER exe: unsafe_on_stock_zh
- Hides rider objects inside a vehicle and swaps ModelCondition, WeaponSet, ObjectStatus, CommandSet, and Locomotor per RiderN slot. Used as deploy (stand vs prone) for TELs/AD.
- Rebuild: **MANUAL_REBUILD** — keep `deployed vs undeployed weapon set, command set, and locomotor`

- Unique Object keeps two WeaponSet blocks with conditions UNPACKING/DEPLOYED if the art supports those ModelConditions.
- Use stock DeployStyleAIUpdate (ZH module) with PackTime/UnpackTime for turret lock while packing.
- Do not spawn CWC fake-rider infantry. Encode the visual in ConditionState PACKING/DEPLOYED on the vehicle Draw.
- Map RIDER1 (packed / cannot fire) to the default ConditionState and RIDER2 (prone / missiles live) to DEPLOYED.
- CommandSet override becomes a unique last-win CommandSet_ZZZZ file swapped via Upgrade or a second CommandSet on the deployed WeaponSet if the engine allows; otherwise one CommandSet that already contains both fire and undeploy.
- Payload rider templates stay as unique hidden Objects only if still referenced; otherwise they are not imported.

## `OCLSpecialPower`

- Origin: Stock ZH module; CWC templates/OCLs are custom
- SPECTER exe: module_ok_templates_must_be_unique
- Fires a SpecialPower that creates objects via OCL. CWC uses it to apply fake-rider deploy/undeploy and also for smoke grenades.
- Rebuild: **MANUAL_REBUILD** — keep `button that switches deployed state and/or spawns support objects`

- Keep OCLSpecialPower on the unique Object only with a unique SpecialPower template (not SPECIAL_CIA_INTELLIGENCE hijack) and a unique OCL path.
- If the OCL only exists to swap CWC riders, replace the button with DeployStyleAIUpdate pack/unpack instead of importing the fake-rider OCL.
- Smoke-grenade OCLSpecialPower copies are INDEPENDENT_ADD on the unique Object with unique OCL/SpecialPower names.
- Do not rewrite SPECTER SpecialPower.ini; add Data\INI\SpecialPower_SilentDeath.ini unique-path later.

## `DeployStyleAIUpdate`

- Origin: Stock ZH
- SPECTER exe: keep_on_unique_object
- PackTime/UnpackTime, turret only when deployed, recenter before packing.
- Rebuild: **INDEPENDENT_ADD** — keep `pack/unpack deploy`

- Copy the module onto the unique Object INI. Do not patch SPECTER AIUpdate tables.
- Requires Draw ConditionState for PACKING/UNPACKING/DEPLOYED if those anims exist on the W3D.
- This is the SPECTER-safe replacement for RiderChangeContain stand/prone.

## `EnemyNearUpdate`

- Origin: CWC house-color helper (not required on stock ZH)
- SPECTER exe: optional
- Empty module in V25 (house color / nearby-enemy hook). No gameplay keys.
- Rebuild: **INDEPENDENT_ADD** — keep `house-color / nearby-enemy hook if the exe honors it`

- Keep on the unique Object. If stock Generals.exe ignores it, drop only the module class, never the rest of the unit.

## `FireWeaponUpdate`

- Origin: Stock ZH module used by CWC as a radar/search weapon ticker
- SPECTER exe: keep_on_unique_object
- Periodically fires a Weapon (ChinaHQ11 uses CWCruSA10RadarWeapon).
- Rebuild: **INDEPENDENT_ADD** — keep `passive radar / search weapon`

- Keep on the unique Object with a unique Weapon path. Do not retarget SPECTER radar tables.

## Pack / Unpack (not always DeployStyleAIUpdate)

V25 pack/unpack is not always DeployStyleAIUpdate. ChinaHQ11 encodes packed vs deployed as RIDER1 vs RIDER2 ModelConditions, WeaponSet WEAPON_RIDER1/2, CommandSet override, and SET_NORMAL vs SET_SLUGGISH locomotor.

- ConditionState default = packed (no primary missile).
- ConditionState DEPLOYED = HQ11.HQ11 once-forward with WeaponLaunchBone PRIMARY MISSILE_C.
- WeaponSet None vs HQ11MissileWeapon.
- Locomotor SET_NORMAL vs a slower deployed locomotor copied as a unique Locomotor def.
- CommandSet one unique file that contains both fire and undeploy, or two unique CommandSets swapped only if a stock Upgrade/WeaponSet path can do it without CWC.exe.

