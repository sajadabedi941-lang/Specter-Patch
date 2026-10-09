# Isolated lever 1: unique CommandSet on Iraq_AlFahd500

Preserves PR #599 baseline. One packed path changed:
`Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini`
CommandSet `Scud_B_CommandSet` -> existing leftover `Iraq_AlFahd500CommandSet`.

## Packed last-wins inspected (PR #599 DATA)

- Factory `Iraq_AlFahdMissileFactoryCommandSet` slot 1 = `CB_MISSILE_A` UNIT_BUILD Object=`Iraq_AlFahd500`.
- `Iraq_AlFahd500`: KindOf vehicle (no GARRISONABLE), WeaponSet Conditions=None, Weapon=`Weapon_Iraq_AlFahd500`, empty `WeaponSetUpgrade ModuleTag_09h56u56j` (no TriggeredBy), ProductionUpdate, CommandSet was `Scud_B_CommandSet`, BuildCost=2200.
- `Weapon_Iraq_AlFahd500`: ClipSize=1, ClipReloadTime=95000, no FireOCL, AutoReloadsClip omitted (default Yes).
- `Iraq_Alhussaien`: GARRISONABLE_UNTIL_DESTROYED + RiderChangeContain + InitialPayload rider2 + ObjectCreationUpgrade TriggeredBy=`Upgrade_Rearm_Iraq_Alhussaien` + unique armed/unarmed CommandSets. That machine is not copied.
- Leftover (unreferenced by AlFahd500 body): `Iraq_AlFahd500CommandSet` (FireMainWeapon + Command_Rearm_Iraq_AlFahd500 + Scud switches), `Command_Rearm_Iraq_AlFahd500` OBJECT_UPGRADE, `Upgrade_Rearm_Iraq_AlFahd500` Type=OBJECT BuildCost=1100, `Iraq_AlFahd500_UnarmedRearmSet`, `RearmStrip_Iraq_AlFahd500`.
- `Scud_B_CommandSet` unchanged; MOTHER `Iraq_R11ScudB` still uses it.

## Spawn-CTD split (#594-#597)

- #594/#595: RiderChangeContain + InitialPayload (+ GARRISONABLE in #595) + weapon FireOCL/AutoReloadsClip=No. Unique CS was NOT required for #594 (kept Scud_B, still CTD).
- #596: startup CTD from duplicate `Iraq_AlAbbasCommandSet` (building vs TEL).
- #597: no riders; PLAYER_UPGRADE WeaponSet + unique CS + WeaponSetUpgrade TriggeredBy + FireOCL OCL_Rearm_* + AutoReloadsClip=No on A/D. Spawn still CTD.
- Shared crash ingredients: riders or TriggeredBy/PLAYER_UPGRADE plus FireOCL/AutoNo. Isolated unique CS was never tested.

## This lever

Assign the leftover unique CommandSet only. No KindOf, rider, WeaponSet, TriggeredBy, FireOCL, or weapon edits. B-J / country TELs / MOTHER / factory button unchanged.

Paid rearm is NOT complete: clip still auto-reloads in 95s. The leftover $1100 OBJECT_UPGRADE button can charge money with no clip restore because no module listens to `Upgrade_Rearm_Iraq_AlFahd500`.

Static validation is not runtime safety. A 32-bit generals.exe/game.dat exists under /tmp/zh-ab-clean, but a full factory-produce/fire/rearm skirmish was not completed in this environment.

Do not proceed to missile B. Do not add TriggeredBy/FireOCL/riders until this lever is spawn-safe in Zero Hour.
