# Stage 5 — experimental DATA+ART BIG pack (ChinaCSSA1, ChinaHQ11)

Builds an **independent experimental copy** of SPECTER FINAL `_SPEC_DATA_ONE.big` and `_SPEC_ART_TWO.big` with unique-path Silent Death V25 defs for `ChinaCSSA1` and `ChinaHQ11`.

Original SPECTER FINAL is never opened for write. No loose INI is emitted. `apply` is refused.

## What is added (experimental copy only)

- Unique Objects `SD25_ChinaCSSA1` and `SD25_ChinaHQ11` plus DATA deps (weapons, armor, locomotor, DamageFX, CrateData, OCL, AudioEvent, projectiles).
- Unique ART members under `Art\W3D\` and `Art\Textures\` when the stem is not already in SPECTER ART TWO.
- Unique wavs under `Data\Audio\Sounds\` inside the DATA BIG.
- Factory overlay via last-win unique path `Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini` (does **not** edit `CommandSet.ini`).
- Construct buttons `SD25_Command_ConstructChinaCSSA1` / `SD25_Command_ConstructChinaHQ11` and HQ11 `Command = DEPLOY`.

## China build location (extracted, not guessed)

SPECTER Object `ChinaWarFactory` (`Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini`) uses **`PLAWarFactoryCommandSet`**, not `ChinaWarFactoryCommandSet`.

Empty slots in SPECTER FINAL: **4, 7, 15, 18**.

| Unit | Command | Slot | Building |
|---|---|---|---|
| SD25_ChinaCSSA1 | UNIT_BUILD | 4 | ChinaWarFactory |
| SD25_ChinaHQ11 | UNIT_BUILD | 7 | ChinaWarFactory |

China Supply Center only builds the supply truck. The dozer CommandSet places buildings (e.g. HQ-9 site), not this mobile TEL.

## HQ11 deploy mapping

CWC `RiderChangeContain` + rider-only `OCLSpecialPower` is rebuilt as stock `DeployStyleAIUpdate` + `WeaponSet Conditions = DEPLOYED`. Fire only when deployed. PackTime/UnpackTime = 2000 (V25 SDSR5).

Not kept: runtime CommandSet swap, SET_SLUGGISH crawl-while-deployed.

## Run

```bash
python3 patch/tools/v25_sync/v25_sync.py selftest
python3 patch/tools/v25_sync/v25_sync.py pack-sample --out /tmp/v25_stage5_pack --json
python3 patch/tools/v25_sync/v25_sync.py apply   # must error
```

Writes experimental BIGs only under `--out` (default `/tmp/v25_stage5_pack`). Original `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/` hashes must stay `7f8c7f63…` / `81d9a4aa…`.

## Generals.exe

This stage does **not** launch Generals.exe. Do not treat the pack as in-game tested.

## INI parse fix (experimental DATA only)

Three diagnosed load errors were repaired **inside** the experimental `_SPEC_DATA_ONE.big` (not as loose INI). ART TWO is unchanged. See `STAGE5_FIX.md`.

Fixed DATA SHA256 `c9d1b6ac805d9d9edd18d643f945bf740b822d88bf07d6e280129aa204f2880c`. ZIP `SPECTER_V25_STAGE5_INI_FIX.zip` `641618e790d9e2b4ed1a566d19b8006e184e3e1d4cba3c4b7ce756627efaf773`.
