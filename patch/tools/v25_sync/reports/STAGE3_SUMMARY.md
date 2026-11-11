# Stage 3 — nested ART recovery and CWC rebuild plans

- Generated: 2026-11-11 14:31 Asia/Tehran
- Game writes: **False**
- Generals.exe run: **False**

## Sample equipment

| Object | DATA | ART | Resolver readiness |
|---|---|---|---|
| `ChinaCSSA1` | `READY_FOR_TRANSFER_PLAN` | `AUTO_RECOVERABLE` | `auto_fixable` |
| `ChinaHQ11` | `READY_FOR_TRANSFER_PLAN` | `AUTO_RECOVERABLE` | `auto_fixable` |

## What was actually tested vs analysis-only

- **Tested:** unit tests in `tests/test_art_cwc.py` and `tests/test_resolver.py` (nested BIG writer/index, exact-stem lookup, multi-texture W3D, missing ART, CWC inspect, shared ART, apply refused).
- **Tested against live V25 volumes (if present):** ArtIndex of nested `WYS/Textures.big` / `WYS/W3D.big`, ChinaCSSA1 + ChinaHQ11 plan regeneration.
- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.

- Unit tests: `{'note': 'regenerated during stage 4'}`

