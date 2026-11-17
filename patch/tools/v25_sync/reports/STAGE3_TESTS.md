# Stage 3 tests

- Generated: 2026-11-11 13:31 Asia/Tehran
- Command: `python3 patch/tools/v25_sync/v25_sync.py selftest`
- Result: **29 tests, OK** (0.013s)

## Coverage

| Case | Result |
|---|---|
| Nested BIG write + exact stem index | tested |
| Texture inside nested BIG (`EXTireTrack` vs `EXTnkTrack`, no prefix match) | tested |
| Nested BIG inside a zip (`WYS/Textures.big`) | tested |
| Multi-texture W3D (`CHCSSA1B/T` + `Glass1`) | tested |
| Missing ART not substituted | tested |
| Shared ART across two objects | tested |
| CWC RiderChangeContain / OCLSpecialPower / DeployStyleAIUpdate inspect | tested |
| RiderN parsed as Object refs | tested |
| DATA vs ART status split | tested |
| MappedImage name is not a missing file | tested |
| `apply` refused | tested |
| Stage 2 resolver regressions | tested |

## Live V25 (not unit tests)

- Indexed 9 nested BIGs, 22415 exact stems.
- `ChinaCSSA1` ART `AUTO_RECOVERABLE`, DATA `MANUAL_REBUILD`.
- `ChinaHQ11` ART `AUTO_RECOVERABLE`, DATA `MANUAL_REBUILD` (CWC riders).

## Not tested

- Generals.exe
- Import into SPECTER BIGs
- In-game pack/unpack of HQ11
