# SPECTER SS1 compatibility engine

SS1 (`SPECTER FINAL`) is the immutable reference. Silent Death V25 must adapt to
SS1 load rules. This engine analyzes and plans; it does not import equipment,
does not rewrite public SPECTER INI, and does not run `Generals.exe`.

## What stages 1–5 actually built

| Stage | PR | What it did | Gap |
|---|---|---|---|
| 1 | #770 | Archive health, inventories, dry-run mapping | Assumed V25 folder layout was loadable on SS1 |
| 2 | #771 / resolve | Unique-path planner, collisions, CWC flags | Dest paths were V25-shaped |
| 3 | #773 | Nested ART + CWC behavior inventory | No SS1 VFS topology check |
| 4 | #774 | Independent DATA rebuild recipes (HQ11 deploy) | Recipes did not preflight parse-fatal refs |
| 5 pack | #775 | Experimental DATA+ART copy for CSSA1 + HQ11 | Emitted `Weapon\SilentDeath\` and `MappedImages\SilentDeath\` |
| 5 INI fix | #776 | FXList End, HQ11 DEPLOYED draw, duplicate Armor | User proved DATA still Serious-Error after those three |

Stage 5 is a **sample crash class**, not the project scope. CSSA1/HQ11 must not
be the only objects the engine understands.

## Architectural defects found (before this infra)

1. **Weapon directory is not recursive on SS1.** Live `_SPEC_DATA_ONE.big` has
   only flat `Data\INI\Weapon\Weapon_*.ini` plus extra root `Weapon_*.ini`.
   Zero `Weapon\<subdir>\` members. Stage 5 put weapons under
   `Weapon\SilentDeath\` — if GameEngine `loadDirectory(Weapon, subdirs=false)`
   matches Object's opposite (`Object` is recursive), those weapons never
   register, then parse-fatal `Weapon =` refs crash.

2. **MappedImages only loads `HandCreated` and `TextureSize_512`.** A new
   `MappedImages\SilentDeath\` folder has no SS1 precedent.

3. **Parse-fatal refs were incomplete.** `DeathWeapon` and `IgnitionFX` were
   not in `NAMED_KEYS`, so `CWCgenTreeFlameWeapon` and
   `FX_CWCruS300MissileIgnition` were invisible to validation.

4. **Readiness meant "Object INI exists".** A unit with a copied Object file
   was treated as transferable while its projectile / DeathWeapon / dest path
   were unloadable.

5. **Locomotor comment syntax.** SS1 uses
   `GroupMovementPriority = MOVES_BACK;` — V25 tails without `;` are extra
   tokens.

6. **FXList / Object End.** Column-0 `End` and tokens after Object `End` are
   parse-fatal. Stage 5 fix covered three files; the engine must reject the
   class, not those files only.

7. **`copy_big_with_adds` cannot replace members.** Experimental iteration
   needed `rewrite_big_members`. Original SPECTER BIGs stay read-only.

## SS1 rules the engine now discovers from the live DATA BIG

- `Data\INI` root: `loadDirectory(..., subdirs=False)` — every root `*.ini`
  is parsed by first-token block type.
- Proven extra prefixes already in SS1: `CommandButton_`, `CommandSet_`,
  `Weapon_`, `Object_`, `ObjectCreationList_`, `Science_`, `SpecialPower_`,
  `Upgrade_` (plus PlayerTemplate_/ControlBarScheme_ when present).
- `Object\` is recursive (`Object\Specter\<faction>\...`).
- `Weapon\` is flat. Emit extras at **root** `Weapon_SilentDeath.ini`.
- MappedImages: only `HandCreated` and `TextureSize_512`.
- Public INI basenames (`Weapon.ini`, `Armor.ini`, `CommandSet.ini`, …) are
  protected: loaded, never overwritten.

Proven extra kinds at Data\INI root (same `loadDirectory(..., subdirs=False)`
as the live `Weapon_*.ini` extras, with the stock table present):
`Armor_`, `Locomotor_`, `FXList_`, `DamageFX_`, `Crate_`, `ParticleSystem_`,
`SoundEffects_`. Unique `Armor_SilentDeath.ini` is the analogue of
`Weapon_SilentDeath.ini`. Unknown prefixes stay unloadable.

## What the engine does now

- `ss1-layout` — read-only scan of SS1 DATA member names; emit-path table.
- `catalog` — every V25 Object, full Weapon/Projectile/OCL/FXList chain,
  dest loadability, CWC rebuild, collision with SS1. Ready ≠ file exists.
- **Ready Gate** — READY only after actual payload bytes, parse-fatal deps,
  proven dest path, rewritten names, and no duplicate/broken refs. Output-only
  normalize closes FXList Ends and Locomotor `;` comments. Object missing End
  is detected, never auto-fixed. CWC RiderChangeContain / OCLSpecialPower stay
  `MANUAL_REBUILD` with required capabilities documented.
- `preflight` — Stage 5 crash classes + missing parse-fatal refs + protected
  paths. Wired into `validate_added_defs` so pack-sample cannot ship them.
- `ready-pack` — small READY group into an independent DATA copy (dry-run).
- `selftest` — discovers all `tests/test_*.py`, including Stage 5 regressions.
- `apply` — refused. No SPECTER BIG write. No loose INI. No bulk transfer.

## Commands

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py ss1-layout --json
python3 patch/tools/v25_sync/v25_sync.py catalog --json
python3 patch/tools/v25_sync/v25_sync.py e2e --json
python3 patch/tools/v25_sync/v25_sync.py ready-pack --out /tmp/v25_ready_pack --json
python3 patch/tools/v25_sync/v25_sync.py apply   # must error
```

Reports: `reports/SS1_LAYOUT.md`, `V25_CATALOG.md`, `ENGINE_AUDIT.md`.
Full per-object JSON: `reports/V25_CATALOG.json.gz`.

## Live catalog (this run)

Against SPECTER FINAL DATA `7f8c7f63…81343` and the full V25 extract. Generated 2026-11-11 17:10 Asia/Tehran. Generals.exe was not run.

| Class | Objects |
|---|---|
| Total V25 Objects | 6207 |
| Ready for safe transfer (byte gate) | 3908 |
| unique_import_ready | 3304 |
| Name in SS1 (rewrite plan required) | 604 |
| MANUAL_REBUILD (CWC kept) | 689 |
| Needs fix (parse-fatal / missing End / dest) | 1392 |
| Blocked sides | 218 |

SS1 DATA: 3587 members, 192 Data\\INI root files, Weapon\\ nested subdir files = **0**, MappedImages only HandCreated (35) + TextureSize_512 (4).

All prior unit tests plus Ready Gate / proven-path / experimental pack tests.
Generals.exe was not run.

## Success criterion

No object with a parse-fatal defect or missing parse-fatal dependency is
READY. Grouped transfer into original SPECTER FINAL stays blocked. The
experimental DATA pack is an independent copy of a small READY group only.
