# INITIALIZATION_CRASH_FINAL_REPORT.md

Static initialization repair for C&C Generals Zero Hour — Specter Expansion.

This environment cannot launch Zero Hour. Runtime confirmation is the user's test.

---

## A. LAST KNOWN RUNTIME-SAFE BUILD

#414

- PR: https://github.com/sajadabedi941-lang/Specter-Patch/pull/414
- Commit: `8002fcccd9a9989f89f628be34ca0b70558987f6`
- Title: Force unique China airbase portraits and convert J-31 to A2A

## B. CRASHING BUILD

`3ebc42a1c80afc83d8c27aa055f4eea273e40087` on `cursor/final-global-airforce-roster-e54a`

Release: `final-global-airforce-roster-v1`

DATA sha256 `9b57540f8672d0372dfcf03a8164548acad2d00404fe3a4eb9d0743b5d7c7716`

ART sha256 `2255a132b5e68bc69d941bc7d5fa1dcb617c323db47bd502bef89af96eb4289e`

Symptom: `Release Crash` / `Uncaught Exception during initialization` with no useful object/INI line in ReleaseCrashInfo.

## C. FIRST BAD PR / COMMIT

**Proven:** PR **#417** / commit `25ec5a10` — `Add Germany, Italy, and UK air forces with donor-mesh names.`

https://github.com/sajadabedi941-lang/Specter-Patch/pull/417

That commit added both crash objects. Britain E-7 (`KVE737` + `Animation = KVE737.KVE737`) was later fixed in PR #422, but Italy G550 was not. Germany H145M was never fixed.

## D. ROOT CAUSE

`KindOf` includes `PRELOAD`, so Zero Hour loads the Draw model while parsing the Object INI.

Two post-#414 objects played an animation that does not exist in the packed W3D:

1. `ItalyAircraftG550CAEW` — `Animation = KVE737.KVE737` while `KVE737.W3D` has **zero** animation chunks (same mesh as the known Britain E-7 boot crash).
2. `GermanyHelicopterH145M` — `Animation = LSFFENNECK.LSFFENNECK` while `LSFFenneck.W3D` has **zero** animation chunks.

The engine throws an uncaught exception during initialization and does not print the INI line.

Secondary crash-capable surface (not proven as the first failure, stripped anyway):

- Post-#414 packers inlined weapons/buttons/portraits into `Weapon.ini` / `CommandSet.ini` / `HandCreatedMappedImages.ini` **and** still packed overlay copies (`Weapon_FranceAirforce.ini`, `Weapon_EuropeAirforce.ini`, `Weapon_FinalGlobalAirforceRoster.ini`, matching CommandButton and `z*Portrait` files). The E-7 packer already treated duplicate overlay INIs as unsafe (`SpecialPower_BritainAirforce.ini`).
- 105 `North Korea\...` INI entries packed at BIG root (not under `Data\`) duplicated Specter North Korea objects if anything enumerated them.

## E. FIRST BAD FILE

`patch/Data/INI/Object/Specter/Italian Armed Forces/Airforce/ItalyAircraftG550CAEW.ini`

(Also crash-capable in the same commit: `patch/Data/INI/Object/Specter/German Armed Forces/Rotary/GermanyHelicopterH145M.ini`)

## F. FIRST BAD DEFINITION

`Object ItalyAircraftG550CAEW` — `DefaultConditionState` / `ConditionState` `Animation = KVE737.KVE737`

Secondary: `Object GermanyHelicopterH145M` — `Animation = LSFFENNECK.LSFFENNECK`

## G. WHY ZERO HOUR CRASHED DURING INITIALIZATION

Objects with `KindOf = PRELOAD ...` force W3DModelDraw to resolve `Model` and `Animation` at INI load, before the main menu.

`KVE737.W3D` is hierarchy + mesh only. Requesting animation `KVE737.KVE737` throws. Britain E-7 hit this first among UK objects; Italy G550 kept the broken Draw after the E-7-only repair. Germany H145M is the same pattern on a Fennek donor mesh.

ReleaseCrashInfo stays empty because the failure is inside model/animation preload, not a printable unknown INI token.

## H. EXACT FIX APPLIED

1. Removed `Animation` / `AnimationMode` from `ItalyAircraftG550CAEW` Draw states. Kept `Model = KVE737`, particles, cost, CommandSet, KindOf (no RADAR).
2. Removed `Animation` / `AnimationMode` from `GermanyHelicopterH145M` Draw states. Kept `LSFFenneck` / `LSFFenneckd` / `LSFFenneckk`, Chinook AI, CommandSet.
3. Packed from clean staging off the roster BIGs. Did not edit USA/Russia/China live files (CommandSet hashes unchanged).
4. Stripped duplicate inlined overlay INIs listed in section K.
5. Stripped 105 orphan `North Korea\...` BIG entries not under `Data\`.
6. Re-extracted both BIGs and re-validated the extracted objects.

No aircraft added. No country roster redesign. No Nuclear/Atomic, Rally, or Sell edits.

## I. POST-414 CONTENT PRESERVED

All valid expansion after #414 remains:

- France air force rebuild and helicopters
- Germany / Italy / UK air forces, airbase structure, weapon-fire wrappers
- UK diversity, F-35B donor, Tempest, E-7 (already animation-safe)
- Global donor expansion, New-folder TEOD visuals, unused-donor completion
- Final 12-fighter global roster for every playable country except locked USA/Russia/China
- Italy G550 CAEW and Germany H145M **units kept**, Draw repaired only

## J. CONTENT DISABLED/REVERTED

NONE of the aircraft roster was disabled.

Removed from the packed DATA BIG only:

- Invalid `Animation=` lines on G550 and H145M (source + packed)
- Duplicate overlay INIs already inlined into canonical files
- Orphan `North Korea\...` paths (canonical `Data\INI\Object\Specter\North Korea\...` kept)

## K. DUPLICATE DEFINITIONS FOUND

Pre-repair packed roster scan: **1419** named-global collisions (includes stock Specter overlays that #414 already booted with).

Post-#414 overlay duplicates stripped (definitions remain in the canonical INI):

| Overlay file | Type |
|---|---|
| `Weapon_FranceAirforce.ini` | Weapon x21 |
| `Weapon_EuropeAirforce.ini` | Weapon x48 |
| `Weapon_DonorUnusedAircraft.ini` | Weapon x24 |
| `Weapon_FinalGlobalAirforceRoster.ini` | Weapon x468 |
| `CommandButton_DonorUnusedAircraft.ini` | CommandButton |
| `CommandButton_FinalGlobalAirforceRoster.ini` | CommandButton x156 |
| `zFrance_AirbasePortrait_Images.INI` | MappedImage |
| `zEurope_AirbasePortrait_Images.INI` | MappedImage |
| `zGlobalDonor_AirbasePortrait_Images.INI` | MappedImage |
| `zFinalGlobalCompletion_Portrait_Images.INI` | MappedImage |
| `zNewFolderSourceFix_Portrait_Images.INI` | MappedImage |
| `zDonorUnused_AirbasePortrait_Images.INI` | MappedImage |
| `zFinalGlobal_AirbasePortrait_Images.INI` | MappedImage x156 |

`zChina_AirbasePortrait_Images.INI` kept (present in #414, runtime-safe).

Stock `Weapon_Egypt.ini` / India / Libya / Pakistan / Saudi / SouthAfrica / Syria / UAE overlays kept (no overlap with `Weapon.ini`).

`Weapon.ini` still has 9 internal duplicate names that predate this pass and match stock Specter behavior.

## L. MISSING REFERENCES FOUND

Air CommandSets: **0** missing CommandButtons (including France/Germany/Italy/Britain/Turkey/Iran/Japan/Pakistan/India/Israel/Saudi airfields).

PLAAirfield / China Large / China Heavy CommandSet hashes identical to the crashing roster (and to the unused-donor baseline).

G550 / H145M construct buttons remain declared in `CommandSet.ini` **before** the Italy/Germany airbase CommandSets that use them.

Unresolved stock-model W3Ds (EnglishZH / other ART BIGs) are not treated as SPEC-ART bugs. New roster jets were not given `Animation=` on mesh-only W3Ds.

## M. BROKEN W3D/TEXTURE REFERENCES FOUND

| Model | Packed | Animation chunks | Used with Animation= (pre-fix) |
|---|---|---|---|
| `KVE737.W3D` | yes (44628 bytes) | **0** | Italy G550 (fixed); Britain E-7 already safe |
| `LSFFenneck.W3D` | yes (70160 bytes) | **0** | Germany H145M (fixed) |
| `E3.W3D` | yes | yes (0x200) | France/Germany E3 left unchanged |

New-folder TEOD substitutes (`NVJ-20`, `AVF-35`, `PAK-FA`, …) had **no** `Animation=` on those meshes in packed DATA.

ART BIG was not modified. ART sha256 unchanged from roster v1.

## N. WEAPON/PROJECTILE ERRORS FOUND

Roster wrapper weapons remain inlined in `Weapon.ini` with packed projectiles:

`MeteorMissile_Object`, `AIM-9X_Object`, `R77_Object`, `GBU24_GuidedBombObject`, `Fab-250`, `Kh59MK2_Object`, `KH31P_MissileObject`, `Paveway_IV_Object`, `30mm_API-T_Projectile`, `GenericUnguidedRockets`.

No aircraft deleted for weapon errors. Duplicate overlay weapon files stripped (see K).

## O. COMMANDSET/BUTTON ERRORS FOUND

Airfield/Large/Heavy menus for expanded countries still resolve. Rally/Sell meta slots preserved. USA/RU/CN CommandSet hashes:

- AmericaAirfield `0954ea634aaf8a5a`
- America_Large `9045e025345dfb25`
- America_Heavy `3fcb76336e9c336c`
- RussiaAirfield `e615b640749e67b4`
- Russia_Large `20cf43d97715d4eb`
- Russia_Heavy `4d98bbc64f76cf2b`
- PLAAirfield `522862c4d7e9e556`
- China_Large `afdecf56f3b8e16f`
- China_Heavy `2fc489c13960283d`

## P. MODULETAG ERRORS FOUND

G550 and H145M ModuleTags unique after repair.

Broader ModuleTag scan of stock Specter objects reports many duplicates that exist in #414; those were not rewritten.

## Q. PARSER RESULT

**PASS** for crash-class checks on re-extracted DATA:

- G550 / H145M End-balance PASS
- No `Animation =` field remaining on KVE737 or LSFFenneck
- No `KindOf RADAR` on those objects
- No CountryBalance / BuildLimit / PricingDefault unknown schemas
- USA/RU/CN protected INI hashes PASS

Full-tree End-depth scan of stock INIs still reports noise (nested `Behavior`/`Draw` heuristics). That noise exists in the #414 tree and is not the init exception.

## R. DATA RE-EXTRACT

**PASS** — 2751 files extracted from the new `_SPEC_DATA_ONE.big` and re-validated.

## S. ART RE-EXTRACT

**PASS** — 3639 files extracted from `_SPEC_ART_ONE.big`. `KVE737` and `LSFFenneck` present.

## T. FINAL INITIALIZATION STATIC STATUS

**PASS**

STATIC INITIALIZATION VALIDATION: PASS

READY FOR USER RUNTIME TEST: YES

---

## Repair pack hashes

- DATA sha256 `898bca00c424a413be785e911ee5e8167b0928243c783ff6cc040f1ded781381`
- ART sha256 `2255a132b5e68bc69d941bc7d5fa1dcb617c323db47bd502bef89af96eb4289e`

## #414 structures still intact

- Fighter / Large / Heavy airbases remain; no third airbase added
- Rally and Sell not retargeted on protected or repaired sets
- Nuclear/Atomic buildings not edited
- No PlayerTemplate deleted
- USA / Russia / China live object INIs byte-identical to the crashing roster (which itself did not touch them vs unused-donor)
