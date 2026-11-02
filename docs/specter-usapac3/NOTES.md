# USAPAC3 — ART ONE vs ART TWO packing

Zero Hour was not run.

## Live ART layout

| Archive | Bytes | Files | Role |
|---|---:|---:|---|
| `_SPEC_ART_ONE.big` | 2,145,283,309 | 3025 | `Art\Textures\`, `Art\Terrain\` |
| `_SPEC_ART_TWO.big` | 307,254,782 | 2684 | `Art\W3D\` only |

None of the 16 USAPAC3 files were in either archive before this pack.
The previous merge put them in a **truncated** 524 MB ART ONE from
`art_data.part*.rar`. That is not the live Full Release ART ONE.

## Capacity

2 GiB = 2,147,483,648. ART ONE remaining = 2,200,339 bytes.
USAPAC3 art total = 5,723,261 bytes. Does not fit in ART ONE.

All 16 files go in ART TWO. ART ONE is unchanged (same SHA-256 as
Full Release / specter-unified). ART TWO originals: 2684 kept, 16 added,
0 removed.

## Launcher

`Launch_Specter.bat` previously copied only ART ONE. It now copies
`_SPEC_ART_TWO.big` as well.

## DATA

USAPAC3 objects/weapons/CommandSet/CSF were merged into the live unified
`_SPEC_DATA_ONE.big` (374,075,482 → 374,096,090). America HQ slot 6 =
USAPAC3, slot 12 = NASAMS. THAAD/Patriot objects were not edited.
