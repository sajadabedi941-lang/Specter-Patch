# V25 → SPECTER sync engine (stage 4 independent DATA rebuild)

Independent planner for moving **Generals Silent Death V25** equipment into **SPECTER FINAL**.

Stage 4 completes DATA rebuild plans for `ChinaCSSA1` and `ChinaHQ11` (unique-path DamageFX / CrateData, proven DeployStyleAIUpdate mapping). It still **does not import** Objects, Weapons, CommandSets, CommandButtons, or ART into the game. Original SPECTER BIGs stay untouched. `apply` is refused.

See `STAGE2.md` for what stage 1 actually implemented vs what was only described.

## What this is

A dry-run engine that:

1. Verifies the V25 split archive (`V25.zip` + `V25.z01`…`V25.z157`, including `V25.z62`). Names may have a leading space on GitHub.
2. Reads V25 DATA/ART (loose `Data/INI` last-win, then BIG alphabetical order).
3. Reads SPECTER FINAL (`_SPEC_DATA_ONE.big`, `_SPEC_ART_TWO.big`, loose `Data/INI/CommandSet.ini` + `CommandButton.ini`).
4. Walks every Object and its Weapon / Projectile / Armor / Locomotor / OCL / FX / SpecialPower / Upgrade / CommandSet chain.
5. Detects name collisions. Shared identical defs are marked reuse; differing shared names become `SD25_<name>` with a planned full-ref rewrite.
6. Never drops a V25 capability because SPECTER lacks an equivalent — those rows are `independent_add`.
7. Writes Manifest, Mapping, compatibility, and dry-run reports.

## Run

From the repo root (7z required):

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py health --json
python3 patch/tools/v25_sync/v25_sync.py dry-run --json
python3 patch/tools/v25_sync/v25_sync.py resolve --json
python3 patch/tools/v25_sync/v25_sync.py art-cwc --json
python3 patch/tools/v25_sync/v25_sync.py data-rebuild --json
python3 patch/tools/v25_sync/v25_sync.py plan-object --object ChinaCSSA1 --json
```

Commands: `health`, `extract`, `inventory`, `dry-run`, `plan`, `validate`, `resolve`, `art-cwc`, `data-rebuild`, `plan-object`.  
`apply` always exits with an error.

Cache/extract live under `/tmp/v25_src`, `/tmp/v25_extract`, `/tmp/ss1` — not inside the repo.

## Reports

Written to `patch/tools/v25_sync/reports/`:

| File | Meaning |
|---|---|
| `ARCHIVE_HEALTH.md` / `.json` | 158 volumes, 7z test, SPECTER FINAL hashes |
| `COMPATIBILITY.md` / `.json` | V25 vs SPECTER overlap by kind, side map, rules |
| `MAPPING.json.gz` / `MAPPING.md` | Per-object dest, deps, art, missing refs (`gunzip` the JSON; `dry-run` regenerates it) |
| `MANIFEST.json` | Stage-1 bundle metadata (no game files) |
| `DRY_RUN.md` / `.json` | Full scan, collisions, incomplete trees, impact notes |

## SPECTER protection

Blocked paths (never overwritten, never shipped loose as public INI):

- `Data\INI\CommandSet.ini`, `CommandButton.ini`
- `Weapon.ini`, `Armor.ini`, `Locomotor.ini`, `PlayerTemplate.ini`
- `ObjectCreationList.ini`, `FXList.ini`, `SpecialPower.ini`, `Science.ini`, `Upgrade.ini`

Future apply (not this stage) may only add **unique-path** files, for example:

- `Data\INI\Object\SilentDeath\<Side>\<Object>.ini`
- `Data\INI\CommandSet_ZZZZ_SilentDeath_<Side>.ini`
- unique Weapon/Armor files that do not replace packed names

Existing SPECTER Objects, public CommandSets, and public Weapons stay. New air defense must keep AntiAir targeting that already hits SPECTER aircraft/missiles, using new independent defs rather than rewriting core Armor/Weapon tables.

## Archive notes

Silent Death V25 on GitHub `main` uses:

- `' V25.zip'` … `' V25.z157'` (leading space)
- `V25.z62` (no leading space; required — without it W3Ds fail)
- extra `V25.z158` is unused by the 158-volume zip and is ignored

`7z t V25.zip` must report **Everything is Ok** before any later transfer.

## Stage 1 outputs in git

Only files under `patch/tools/v25_sync/`. No SPECTER BIG, no V25 zip volumes, no imported Object INI.
