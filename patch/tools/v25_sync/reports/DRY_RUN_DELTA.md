# Dry-run stage 1 vs stage 2

- Generated: 2026-11-11 13:05 Asia/Tehran

Stage 2 still runs the original dry-run classifier (body-hash collisions) so the scan is comparable.
The resolver uses **effective gameplay fingerprints** and archive recovery; those counts are separate.

## Dry-run object status

- Stage 1: `{'unique_v25': 5374, 'collision_rename': 628, 'shared_identical': 205}` objects_scanned=6207
- Stage 2: `{'unique_v25': 5374, 'collision_rename': 628, 'shared_identical': 205}` objects_scanned=6207
- Stage 1 incomplete sample size / missing kinds: `{'MappedImage': 64794, 'AudioEvent': 1346, 'Object': 7593, 'ObjectCreationList': 3868, 'FXList': 1505, 'ParticleSystem': 473, 'CommandSet': 17, 'CommandButton': 11}`
- Stage 2 missing kinds: `{'FXList': 8811, 'MappedImage': 64794, 'AudioEvent': 1372, 'CrateTemplate': 1608, 'Object': 7593, 'ObjectCreationList': 3868, 'ParticleSystem': 473, 'CommandSet': 17, 'CommandButton': 11}`

## Why missing-ref counts can change

- Stage 2 INI parser also records `FireSound`, `DeathFX`/`DamageFX`, embedded `PSys:`/`FXList:`, and behavior module names.
- Dry-run still reports unresolved names as missing; the resolver then classifies them as REUSE_NATIVE, RECOVER_FROM_V25, or MANUAL_REBUILD.
- No missing name was deleted just to turn the report green.

## Resolver (not equal to unique_v25)

- ready_transfer: **624**
- auto_fixable: **1079**
- manual_rebuild: **4224**
- blocked: **218**
- reuse_only: **62**

