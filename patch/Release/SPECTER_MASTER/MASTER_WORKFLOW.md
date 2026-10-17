# Specter Master BIG Workflow

## Permanent master base

Canonical complete archives live at:

- `patch/Release/SPECTER_MASTER/_SPEC_DATA_ONE.big`
- `patch/Release/SPECTER_MASTER/_SPEC_ART_ONE.big`

Current published package:

- `SPECTER_MASTER_PATCH_EGYPT.zip` (ZIP root = the two BIG files only)

Contained factions (cumulative): Iran, Israel, Iraq, Russia, China, USA, North Korea, Egypt.

## Mandatory workflow for EVERY future change

When adding a country, unit, aircraft, vehicle, building, weapon, texture, model, INI, UI, string, or any other modification:

1. **Start from** the current latest files in `patch/Release/SPECTER_MASTER/`:
   - `_SPEC_DATA_ONE.big`
   - `_SPEC_ART_ONE.big`
2. Apply/merge changes **directly into** those BIG archives (use `patch/tools/big/merge_patch_into_spec_big.py` or equivalent).
3. **Preserve ALL** previous content and previous modifications.
4. **Never** rebuild from scratch.
5. **Never** ship only changed files.
6. **Never** ship final `Data/` / `Art/` folders.
7. **Never** ship a delta/overlay patch unless the user explicitly asks.
8. Rebuild complete `_SPEC_ART_ONE.big` + `_SPEC_DATA_ONE.big`.
9. Replace the master copies under `patch/Release/SPECTER_MASTER/`.
10. Package **both** BIGs into **one ZIP** with root exactly:
    - `_SPEC_ART_ONE.big`
    - `_SPEC_DATA_ONE.big`
11. Publish the ZIP as a downloadable link (Cursor artifact store cannot hold ~800 MiB; use gofile/HTTPS).

## Install method (always)

1. Download one ZIP  
2. Extract  
3. Copy both BIG files into Generals Zero Hour / Specter game directory  
4. Replace previous `_SPEC_ART_ONE.big` and `_SPEC_DATA_ONE.big`  
5. Launch  

## Pre-package verification checklist

- Both archives open as valid `BIGF`
- Previous factions still present
- New changes present inside the BIGs
- No duplicate/broken internal paths
- Archives readable end-to-end

## Tools

- Merge patch tree into SPEC BIGs: `patch/tools/big/merge_patch_into_spec_big.py`
- Extract BIG → loose (debug only): `patch/tools/big/extract_spec_big_to_loose.py`
