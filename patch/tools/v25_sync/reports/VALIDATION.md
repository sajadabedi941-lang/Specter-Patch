# Engine validation (stage 1)

Generated: 2026-11-11 04:59 Asia/Tehran

## Archive

- Volumes on disk: 159 (`V25.zip` + `z01`–`z157` + extra `z158`)
- Required 158-volume zip: **complete**
- `V25.z62`: **present**
- `7z t`: **Everything is Ok** — 12361 files, 237 folders, uncompressed 7633881130
- Extra `V25.z158` is unused by the 158-volume set

## SPECTER FINAL (read-only)

- `_SPEC_DATA_ONE.big` sha256 `7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`
- `_SPEC_ART_TWO.big` sha256 `81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf`
- Hashes unchanged after dry-run
- `apply` refused
- Generals.exe was **not** run

## Dry-run of all V25 Objects

| Metric | Count |
|---|---:|
| Objects scanned | 6207 |
| Unique V25 names | 5374 |
| Shared identical (reuse SPECTER) | 205 |
| Name collision → planned `SD25_*` | 628 |
| Hard incomplete dep trees | 1501 |
| Independent-add (CWC/deploy/special) | 936 |
| Unique protected-kind collisions | 810 |

Unique protected collisions by kind: CommandButton 342, CommandSet 148, Weapon 80, Locomotor 69, Armor 50, OCL 44, Science 33, SpecialPower 25, Upgrade 10, FXList 9.

Those names must not overwrite packed SPECTER files. Future apply uses unique-path INI plus `SD25_` rename with full ref rewrite.

## Incomplete trees

Remaining hard gaps are mostly CWC-only Object/OCL/FX names (`AircraftBomSubduer`, death riders, `OCL_TankDeathTrails`, `FX_CWCgenInfDeath`). The engine **does not drop** those capabilities; they are flagged for independent add. MappedImage/AudioEvent misses are portraits/voices often implicit from TGA/wav, not missing weapons.

## Checks performed

1. Missing refs — yes
2. Name collisions — yes
3. Incomplete deps — yes
4. Object / Weapon / OCL / FX refs — yes
5. Output BIG structure — not written (empty diff)
6. Before/after — SPECTER BIGs identical
7. SPECTER behavior impact — none in stage 1; later apply is rename/unique-path only

## Self-check commands

```bash
python3 patch/tools/v25_sync/v25_sync.py health --json
python3 patch/tools/v25_sync/v25_sync.py dry-run --json
python3 patch/tools/v25_sync/v25_sync.py apply   # must fail
python3 patch/tools/v25_sync/dep_checker.py ChinaCSSA1
```
