# Stage 4 — independent DATA rebuild for ChinaCSSA1 and ChinaHQ11

- Generated: 2026-11-11 14:31 Asia/Tehran
- Game writes: **False**
- Generals.exe run: **False**

## Sample equipment

| Object | DATA | ART | Resolver readiness | DeployStyle used |
|---|---|---|---|---|
| `ChinaCSSA1` | `READY_FOR_TRANSFER_PLAN` | `AUTO_RECOVERABLE` | `auto_fixable` | `False` |
| `ChinaHQ11` | `READY_FOR_TRANSFER_PLAN` | `AUTO_RECOVERABLE` | `auto_fixable` | `True` |

## What was actually tested vs analysis-only

- **Tested:** unit tests in `tests/test_data_rebuild.py`, `tests/test_art_cwc.py`, `tests/test_resolver.py`.
- **Tested against live V25 volumes (if present):** ChinaCSSA1 + ChinaHQ11 Transfer Plan regeneration.
- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.

- Unit tests: `{'selftest': 'python3 patch/tools/v25_sync/v25_sync.py selftest', 'generals_exe_run': False}`

SPECTER public DamageFX.ini, Crate.ini, FXList.ini, and SpecialPower.ini are not in the unique-path list.

