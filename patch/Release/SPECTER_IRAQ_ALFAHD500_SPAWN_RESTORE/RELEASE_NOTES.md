# Restore spawn-safe Iraq_AlFahd500 (withdraw PR #603 rider as recommended)

PR #603 still CTDs in Zero Hour when factory slot A produces `Iraq_AlFahd500`.
That rider-rearm build is **not** accepted. This restore is the recommended
replacement. DATA and ART are **byte-identical to PR #599**.

Keep the crashing #603 files for comparison:

- Tag: `s-iraq-alfahd500-rider-rearm`
- DATA SHA-256 `f2406200669b6062b6b342eda6665e42f7dab4a7a22fcc05d542a670fa1c5a22`

## First failure

Produce/spawn `Iraq_AlFahd500` (test A/B). Crash happens before fire/rearm.

## Smallest correction

Remove the #603 rider stack from factory A. Restore PR #593/#599 object:

- `CommandSet = Scud_B_CommandSet`
- KindOf without `GARRISONABLE_UNTIL_DESTROYED`
- Single `WeaponSet Conditions=None` / `Weapon_Iraq_AlFahd500`
- No `RiderChangeContain`, no `ObjectCreationUpgrade`, no FireOCL
- `ClipReloadTime = 95000` free auto-reload
- Factory `CB_MISSILE_A` still `UNIT_BUILD`s `Iraq_AlFahd500`

Paid rearm is not implemented. Do not proceed to missile B.

## Runtime

User confirmed #603 spawn CTD in-game. This environment could not launch a
playable session, so A–E were not re-run here. #599 factory A was the last
accepted spawn-safe control.
