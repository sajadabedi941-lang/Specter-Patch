# Patriot PAC-3 Stage 1 isolation — crash NOT claimed fixed

Game play through America countdown was not completed. Do not treat this as a crash fix.

## Original SS2

`/tmp/ss2/SPECTER FINAL (GeneralsMode.com)` was not modified.

- Live America CC has no Patriot slot 10
- Live `AmericaVehiclePatriotPAC3.ini` is absent
- Live hashes: CommandSet.ini `593f541674b5917715a189c2aedf462c079233bbd4e21a11f24299b85ab32240`, CommandButton.ini `16ac5b9a306f9ec58cbee944b1b36eb577aed1f3e43bea38f14de16a440be918`

## Isolated copies (original untouched)

Hardlink clones under `/tmp/ss2-tests/`:

| Tree | Patriot object | CC slot 10 | Construct button |
|---|---|---|---|
| `clean` | no | no | no |
| `with-patriot` | PR #790 file | yes | yes |
| `stripped` | deleted | restored live CS | restored live CB |

Stripping slot 10 and the construct button from the #790 files yields **byte-identical** live CommandSet.ini and CommandButton.ini. Hidden CS/CB corruption from PRs 787–790 is ruled out.

America starting buildings are unchanged in all trees: `AmericaCommandCenter`, `AmericaVehicleDozer`, `AmericaSystemSpecialPowerShortcut`.

## In-game launch attempt

Wine 9.0 + 32-bit prefix + EA registry + `-win -noshaders -quickstart` + Options.ini.

`generals.exe` / `game.dat` load native DLLs (`binkw32`, `mss32`), hit llvmpipe D3D, then exit 0. No game window. No `except.txt`. No America faction screen and no countdown.

This environment cannot complete Stage 1/2/3 playtests. Previous SPECTER notes already state Cursor cannot launch Zero Hour.

## What that means for #790

#790 still contains `AmericaVehiclePatriotPAC3` and wires it to America CC slot 10. If that pack still crashes on a real Windows install, CommandSet/Button file bytes are not a second hidden payload: removing those two lines restores the pre-PAC-3 files exactly. Remaining payload is the Object template (PRELOAD / UNIT_BUILD).

TracksDraw was already removed in #790 and did not stop the crash. Next Object sections to change **one at a time on a real game**, not together:

1. `Locomotor` — live `USAPAC3` uses `ChinaVehicleDozerLocomotor` on `UsaPac3Car`; `Generic8x8Locomotor` is proven on `US_M1120` / `US_M1075`, not on this model
2. Draw `AnimationMode`/`Flags` — live `USAPAC3` default is `ONCE` + `MAINTAIN_FRAME_ACROSS_STATES PRISTINE_BONE_POS_IN_FINAL_FRAME`, not `MANUAL`
3. `AIUpdateInterface` turret / `AllowsPitch` — live `USAPAC3` starts with turret disabled via `DeployStyleAIUpdate`
4. Weapon / projectile / fuze clones

## Stage 1 restore ZIP (for a real Windows install)

Unzip into SPECTER FINAL, then **delete** `Data/INI/Object/Specter/United States Of America/AirDefense/AmericaVehiclePatriotPAC3.ini`. Then start America and wait through countdown.
