# Specter Patch FINAL CLEAN

## BIG scan results (before fix)

| Source | Egypt_CommandCenter | Status |
|--------|---------------------|--------|
| `_SPEC_DATA_ONE.big` same path | 7531 bytes, `irq_comndcntr`, `Iraq_Adnan1`, HP 2000 | **BROKEN** |
| Overlay `patch/Data/.../Egypt_CommandCenter.ini` | 8898 bytes, `us_commandcenter`, `US_E3G_AWACS`, HP 5000 | **REPAIRED** |
| Release old trees (6 copies) | same broken sha `1b559b9e0d4e` | **REMOVED → stubs** |

Load order (case-insensitive): `_SPEC_ART_ONE` → `_SPEC_DATA_ONE` → `_SPECTER_PATCH_FINAL_CLEAN`  
Same path override → **only repaired Egypt loads**.

## Duplicate Objects

- Overlay alone: **0** Object-name duplicates
- Final SPEC+CLEAN under `Data\INI`: **0** cross-path Object duplicates
- SPEC-internal bare `North Korea\` paths (outside `Data\INI`) are not in the runtime INI scan set

## Obsolete files removed

- 6 broken Release `Egypt_CommandCenter.ini` copies → OBSOLETE stubs
- `Industry Planet.ini` (misplaced `AirF_AmericaStrategyCenter` in Israel folder) removed from overlay pack/source
- ULTIMATE_LOOSE Egypt synced to canonical repaired bytes

## Startup validation

Simulated Zero Hour BIG load using exact GameRoot candidate bytes + `_SPEC_DATA_ONE.big`.

**STARTUP_VALIDATION=PASS** (twice: staged + GameRoot revalidate)

Live `generals.exe` not present in this environment (Wine installed, no game binary). Validation is BIG-load / Object / CommandSet / PlayerTemplate chain.

## Artifact

- `patch/Release/SPECTER_PATCH_FINAL_CLEAN/_SPECTER_PATCH_FINAL_CLEAN.big`
- SHA256: `049d23db54d2ec76d2a3f3e1ebe3382a1be03c008b26306aed36e59662e8e10e`
- Entries: 1483

Install: copy beside `_SPEC_*` / `EnglishZH.big` / `AudioZH.big`. Do not replace originals. Do not copy old Release Egypt trees.
